"""
Extended Validation and Scientific Integrity Tests for AuraTour.

Covers Step 4 of Research Validation:
1. Hand-computed metric verification against exact analytical solutions
2. Score direction and normalization boundaries [0, 1]
3. Missing or malformed data robustness
4. Deterministic repeatability
5. Monotonic ranking behavior and trade-offs under sustainability weight lambda
6. Itinerary constraints and feasibility limits
7. API / Pydantic schema validation and error responses
"""

import pytest
import numpy as np
from pydantic import ValidationError

from app.sustainability.scoring import (
    haversine_distance_km,
    compute_emissions_kg,
    compute_preference_score,
    compute_popularity_score,
    compute_seasonality_score,
    compute_feasibility_score,
    compute_composite_score,
    normalise_emission_scores,
)
from app.evaluation.metrics import (
    compute_cmr_at_k,
    compute_category_diversity_at_k,
    compute_total_emissions,
    compute_gini_coefficient,
    compute_geographic_spread,
    compute_unique_districts,
    compute_jaccard_overlap,
    compute_kendall_tau,
    compute_catalog_coverage,
)
from app.recommendation.engine import RecommendationEngine
from app.itinerary.builder import ItineraryBuilder, estimate_road_distance_km
from app.data_ingestion.models import UserPreferences, TransportMode


# ─── 1. Hand-Computed Metric Verification ────────────────────────────────────

class TestHandComputedMetrics:
    """Verify metrics against exact analytical hand-computed solutions."""

    def test_cmr_at_k_exact_fraction(self):
        # 4 items, user interests = ["history", "nature"]
        # item 1: ["history"] -> match
        # item 2: ["culture"] -> no match
        # item 3: ["nature", "wildlife"] -> match
        # item 4: ["food"] -> no match
        # Exact CMR = 2 / 4 = 0.5000
        recs = [
            {"attraction": {"categories": ["history"]}},
            {"attraction": {"categories": ["culture"]}},
            {"attraction": {"categories": ["nature", "wildlife"]}},
            {"attraction": {"categories": ["food"]}},
        ]
        cmr = compute_cmr_at_k(recs, ["history", "nature"])
        assert cmr == 0.5000

    def test_category_diversity_exact_union(self):
        recs = [
            {"attraction": {"categories": ["history", "culture"]}},
            {"attraction": {"categories": ["culture", "architecture"]}},
            {"attraction": {"categories": ["nature"]}},
        ]
        # Union = {"history", "culture", "architecture", "nature"} => 4
        assert compute_category_diversity_at_k(recs) == 4

    def test_gini_coefficient_hand_computed_arithmetic_series(self):
        # Array: [1, 2, 3, 4, 5]
        # Analytical Gini:
        # n = 5, sum = 15.
        # weights = 2*i - n - 1 = [ -4, -2, 0, 2, 4 ]
        # sum(weights * y) = (-4)*1 + (-2)*2 + 0*3 + 2*4 + 4*5 = -4 - 4 + 0 + 8 + 20 = 20.
        # Gini = 20 / (5 * 15) = 20 / 75 = 0.2667
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        gini = compute_gini_coefficient(values)
        assert gini == pytest.approx(0.2667, abs=0.001)

    def test_jaccard_overlap_hand_computed(self):
        # set_a = {1, 2, 3, 4}, set_b = {3, 4, 5}
        # intersection = {3, 4} (size 2), union = {1, 2, 3, 4, 5} (size 5)
        # Jaccard = 2/5 = 0.4000
        assert compute_jaccard_overlap(["1", "2", "3", "4"], ["3", "4", "5"]) == 0.4000

    def test_kendall_tau_hand_computed_partial_inversion(self):
        # ranked_a = [A, B, C, D]
        # ranked_b = [A, C, B, D]
        # Common items: 4. Total pairs: 4*3/2 = 6.
        # Pairs: (A,B), (A,C), (A,D), (B,C), (B,D), (C,D)
        # In a: B before C. In b: C before B. (1 discordant pair: B,C)
        # Concordant = 5, Discordant = 1.
        # Tau = (5 - 1) / 6 = 4/6 = 0.6667
        a = ["A", "B", "C", "D"]
        b = ["A", "C", "B", "D"]
        assert compute_kendall_tau(a, b) == pytest.approx(0.6667, abs=0.001)

    def test_catalog_coverage_hand_computed(self):
        # 3 recommendation lists of 2 items each, drawn from a catalogue of 10 items
        # Unique recommended IDs: {1, 2, 3, 4} => 4 / 10 = 0.4000
        run1 = [{"attraction": {"id": "1"}}, {"attraction": {"id": "2"}}]
        run2 = [{"attraction": {"id": "2"}}, {"attraction": {"id": "3"}}]
        run3 = [{"attraction": {"id": "4"}}, {"attraction": {"id": "1"}}]
        cov = compute_catalog_coverage([run1, run2, run3], total_catalog_size=10)
        assert cov == 0.4000

    def test_haversine_and_road_distance_delhi_to_jaipur(self):
        # Delhi coords: 28.6139, 77.2090
        # Jaipur coords: 26.9124, 75.7873
        # Great-circle distance is known to be ~238 km
        straight = haversine_distance_km(28.6139, 77.2090, 26.9124, 75.7873)
        assert 235.0 <= straight <= 245.0
        # Estimated road distance with 1.30 detour factor: ~310 km
        road = estimate_road_distance_km(28.6139, 77.2090, 26.9124, 75.7873)
        assert road == pytest.approx(straight * 1.3, abs=0.05)


# ─── 2. Score Direction & Normalization ──────────────────────────────────────

class TestScoreDirectionAndNormalization:
    """Ensure all component scores adhere to defined directions and [0, 1] bounds."""

    def test_all_scores_strictly_in_unit_interval(self):
        # Composite score
        for p in [0.0, 0.5, 1.0]:
            for e in [0.0, 0.5, 1.0]:
                for pop in [0.0, 0.5, 1.0]:
                    for s in [0.0, 0.5, 1.0]:
                        for f in [0.0, 0.5, 1.0]:
                            comp = compute_composite_score(p, e, pop, s, f)
                            assert 0.0 <= comp <= 1.0

    def test_emission_inversion_monotonicity(self):
        # Lower emissions must yield strictly higher score
        emissions = [50.0, 100.0, 200.0]
        scores = normalise_emission_scores(emissions)
        assert scores[0] > scores[1] > scores[2]
        assert scores[0] == 1.0  # lowest emission destination
        assert scores[2] == 0.0  # highest emission destination

    def test_popularity_moderate_preference_direction(self):
        counts = [10000, 500000, 5000000]
        score_low = compute_popularity_score(10000, counts)
        score_mid = compute_popularity_score(500000, counts)
        score_high = compute_popularity_score(5000000, counts)
        assert score_mid > score_low
        assert score_mid > score_high

    def test_seasonality_direction_regional_and_microclimate(self):
        # Peak month (December = 12) vs Off-peak summer (May = 5)
        peak_score = compute_seasonality_score(12)
        offpeak_score = compute_seasonality_score(5)
        assert offpeak_score > peak_score

        # Microclimate: Mount Abu summer bonus vs Jaisalmer summer penalty in May (month 5)
        abu_att = {"city": "Mount Abu", "district": "Sirohi", "categories": ["nature"]}
        jais_att = {"city": "Jaisalmer", "district": "Jaisalmer", "categories": ["history"]}
        assert compute_seasonality_score(5, abu_att) > compute_seasonality_score(5, jais_att)


# ─── 3. Missing or Malformed Data Robustness ─────────────────────────────────

class TestMissingDataRobustness:
    """Verify system does not crash and applies defensible defaults on missing data."""

    def test_missing_visitor_count_returns_default(self):
        assert compute_popularity_score(None, [10000, 50000]) == 0.5

    def test_empty_visitor_counts_list(self):
        assert compute_popularity_score(50000, []) == 0.5

    def test_missing_travel_hours_and_cost(self):
        assert compute_feasibility_score(None, None) == 0.5

    def test_unknown_origin_raises_value_error(self):
        engine = RecommendationEngine()
        with pytest.raises(ValueError, match="Unknown origin city"):
            engine.recommend_multicriteria(
                user_interests=["history"],
                origin_city="atlantis",
                travel_month=11,
            )

    def test_empty_user_interests_returns_zero_scores(self):
        score = compute_preference_score(["history", "culture"], [])
        assert score == 0.0


# ─── 4. Deterministic Repeatability ──────────────────────────────────────────

class TestDeterminism:
    """Verify identical inputs produce identical recommendations."""

    def test_recommendation_determinism(self):
        engine = RecommendationEngine()
        res1 = engine.recommend_multicriteria(
            user_interests=["history", "architecture"],
            origin_city="delhi",
            travel_month=11,
            sustainability_priority=0.5,
            top_k=5,
        )
        res2 = engine.recommend_multicriteria(
            user_interests=["history", "architecture"],
            origin_city="delhi",
            travel_month=11,
            sustainability_priority=0.5,
            top_k=5,
        )
        ids1 = [r["attraction"]["id"] for r in res1]
        ids2 = [r["attraction"]["id"] for r in res2]
        scores1 = [r["final_score"] for r in res1]
        scores2 = [r["final_score"] for r in res2]
        assert ids1 == ids2
        assert scores1 == scores2


# ─── 5. Monotonic Trade-offs under Lambda ───────────────────────────────────

class TestSustainabilityWeightMonotonicity:
    """Verify increasing sustainability weight lambda achieves emissions reduction."""

    def test_higher_lambda_reduces_or_maintains_emissions(self):
        engine = RecommendationEngine()
        # Compare zero priority (pure preference) vs high priority (sustainability heavy)
        recs_zero = engine.recommend_multicriteria(
            user_interests=["history", "architecture", "culture"],
            origin_city="delhi",
            travel_month=11,
            sustainability_priority=0.0,
            top_k=10,
        )
        recs_high = engine.recommend_multicriteria(
            user_interests=["history", "architecture", "culture"],
            origin_city="delhi",
            travel_month=11,
            sustainability_priority=1.0,
            top_k=10,
        )
        emiss_zero = compute_total_emissions(recs_zero)
        emiss_high = compute_total_emissions(recs_high)
        # High sustainability priority must yield less emissions
        assert emiss_high < emiss_zero

        # Check ranking divergence: they must not be identical rankings
        ids_zero = [r["attraction"]["id"] for r in recs_zero]
        ids_high = [r["attraction"]["id"] for r in recs_high]
        assert ids_zero != ids_high


# ─── 6. Itinerary Constraints and Routing Feasibility ───────────────────────

class TestItineraryConstraints:
    """Verify day progression and daily time limits."""

    def test_day_progression_with_daily_limit(self):
        builder = ItineraryBuilder()
        # Choose 6 attractions across Rajasthan (e.g. Jaipur, Jodhpur, Udaipur)
        ids = ["raj_001", "raj_002", "raj_009", "raj_010", "raj_013", "raj_014"]
        itin = builder.build_itinerary(
            origin_city="delhi",
            attraction_ids=ids,
            trip_duration_days=5,
        )
        assert itin["total_days"] >= 2
        assert len(itin["stops"]) == 6
        assert itin["total_distance_km"] > 0
        assert itin["total_travel_hours"] > 0

    def test_itinerary_with_zero_valid_ids_raises_error(self):
        builder = ItineraryBuilder()
        with pytest.raises(ValueError, match="No valid attractions found"):
            builder.build_itinerary(origin_city="delhi", attraction_ids=["invalid_id_999"])


# ─── 7. API / Pydantic Schema Validation ─────────────────────────────────────

class TestApiSchemaValidation:
    """Verify input validation handles invalid parameters with informative errors."""

    def test_invalid_travel_month_rejected(self):
        with pytest.raises(ValidationError):
            UserPreferences(
                interests=["history"],
                origin_city="delhi",
                travel_month=13,  # Invalid month > 12
            )

    def test_invalid_sustainability_priority_rejected(self):
        with pytest.raises(ValidationError):
            UserPreferences(
                interests=["history"],
                origin_city="delhi",
                travel_month=5,
                sustainability_priority=1.5,  # Out of [0, 1] bounds
            )

    def test_empty_interests_rejected(self):
        with pytest.raises(ValidationError):
            UserPreferences(
                interests=[],  # Must have min_length=1
                origin_city="delhi",
                travel_month=5,
            )

    def test_invalid_origin_city_rejected(self):
        with pytest.raises(ValidationError):
            UserPreferences(
                interests=["history"],
                origin_city="tokyo",
                travel_month=5,
            )


# ─── 8. User Study API Endpoints ─────────────────────────────────────────────

class TestUserStudyEndpoints:
    """Verify privacy-preserving questionnaire and survey submission."""

    def test_questionnaire_generation_valid_persona(self):
        from fastapi.testclient import TestClient
        from app.api.main import app

        client = TestClient(app)
        res = client.get("/api/user-study/questionnaire?persona_id=P1")
        assert res.status_code == 200
        data = res.json()
        assert "questionnaire_id" in data
        assert data["scenario"]["persona_id"] == "P1"
        assert len(data["system_a_items"]) == 5
        assert len(data["system_b_items"]) == 5
        assert set(data["blinded_mapping"].keys()) == {"System A", "System B"}
        assert len(data["questions"]) == 6

    def test_questionnaire_invalid_persona(self):
        from fastapi.testclient import TestClient
        from app.api.main import app

        client = TestClient(app)
        res = client.get("/api/user-study/questionnaire?persona_id=P99")
        assert res.status_code == 404

    def test_survey_submission_and_summary(self, monkeypatch, tmp_path):
        import uuid
        from fastapi.testclient import TestClient
        import app.api.main as main_mod
        from app.api.main import app

        temp_study_file = str(tmp_path / "isolated_user_study.json")
        monkeypatch.setattr(main_mod, "USER_STUDY_FILE", temp_study_file)

        client = TestClient(app)
        unique_id = f"test_hash_{uuid.uuid4().hex[:12]}"
        payload = {
            "participant_id": unique_id,
            "persona_id": "P1",
            "blinded_a_is": "C1_baseline",
            "consent_given": True,
            "ratings_system_a": {
                "relevance": 4,
                "perceived_sustainability": 3,
                "usefulness": 4,
                "trust": 4,
                "feasibility": 3,
                "willingness_to_visit": 4,
            },
            "ratings_system_b": {
                "relevance": 5,
                "perceived_sustainability": 5,
                "usefulness": 5,
                "trust": 5,
                "feasibility": 5,
                "willingness_to_visit": 5,
            },
            "preferred_system": "System B",
            "qualitative_feedback": "System B gave a much better balanced day-to-day route.",
        }
        res_post = client.post("/api/user-study/responses", json=payload)
        assert res_post.status_code == 200
        assert res_post.json()["status"] == "success"

        res_summary = client.get("/api/user-study/responses")
        assert res_summary.status_code == 200
        data = res_summary.json()
        assert data["status"] == "active"
        assert data["total_participants"] >= 1
        assert "mean_ratings" in data

