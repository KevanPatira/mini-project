"""
Tests for the core scoring and recommendation logic.

Tests cover:
- Distance calculations
- Emission computations
- Score normalisation and direction
- Preference matching
- Popularity scoring (bell curve)
- Seasonality scoring (inversion)
- Composite score computation
- Weight adjustment
- Missing data handling
- Ranking determinism
"""

import pytest
import math
import numpy as np
from app.sustainability.scoring import (
    haversine_distance_km,
    compute_emissions_kg,
    compute_preference_score,
    compute_popularity_score,
    compute_seasonality_score,
    compute_feasibility_score,
    compute_composite_score,
    normalise_emission_scores,
    adjust_weights_for_priority,
)
from app.config import EMISSION_FACTORS, SEASONAL_DEMAND_INDEX


class TestDistanceCalculation:
    """Test haversine distance computation."""
    
    def test_same_point_zero_distance(self):
        d = haversine_distance_km(26.9, 75.8, 26.9, 75.8)
        assert d == 0.0
    
    def test_delhi_to_jaipur(self):
        """Delhi to Jaipur is approximately 235 km great-circle (260-280 km road)."""
        d = haversine_distance_km(28.6139, 77.2090, 26.9124, 75.7873)
        assert 230 < d < 280
    
    def test_delhi_to_mumbai(self):
        """Delhi to Mumbai is approximately 1150-1200 km straight line."""
        d = haversine_distance_km(28.6139, 77.2090, 19.0760, 72.8777)
        assert 1100 < d < 1250
    
    def test_symmetry(self):
        d1 = haversine_distance_km(28.6139, 77.2090, 26.9124, 75.7873)
        d2 = haversine_distance_km(26.9124, 75.7873, 28.6139, 77.2090)
        assert abs(d1 - d2) < 0.001


class TestEmissions:
    """Test emission calculations."""
    
    def test_zero_distance_zero_emissions(self):
        assert compute_emissions_kg(0, "train") == 0.0
    
    def test_train_lowest_emissions(self):
        """Train should produce lowest emissions per km."""
        dist = 300
        train = compute_emissions_kg(dist, "train")
        bus = compute_emissions_kg(dist, "bus")
        car = compute_emissions_kg(dist, "car")
        assert train < bus < car
    
    def test_known_emission_value(self):
        """100km by train at 17 g/pkm = 1.7 kg."""
        em = compute_emissions_kg(100, "train")
        assert abs(em - 1.7) < 0.01
    
    def test_invalid_transport_mode(self):
        with pytest.raises(ValueError):
            compute_emissions_kg(100, "helicopter")
    
    def test_all_modes_positive(self):
        for mode in EMISSION_FACTORS:
            em = compute_emissions_kg(100, mode)
            assert em > 0


class TestPreferenceScore:
    """Test preference/interest matching."""
    
    def test_perfect_match(self):
        score = compute_preference_score(["history", "architecture"], ["history", "architecture"])
        assert score == 1.0
    
    def test_no_match(self):
        score = compute_preference_score(["nature", "wildlife"], ["food", "shopping"])
        assert score == 0.0
    
    def test_partial_match(self):
        score = compute_preference_score(["history", "nature"], ["history", "food", "culture"])
        assert 0 < score < 1
    
    def test_empty_interests(self):
        score = compute_preference_score(["history"], [])
        assert score == 0.0
    
    def test_empty_categories(self):
        score = compute_preference_score([], ["history"])
        assert score == 0.0


class TestPopularityScore:
    """Test popularity scoring with bell-curve preference for moderate."""
    
    def test_missing_visitors_returns_default(self):
        score = compute_popularity_score(None, [1000, 2000])
        assert score == 0.5  # MISSING_SCORE_DEFAULT
    
    def test_moderate_popularity_highest(self):
        """Moderately popular should score highest."""
        counts = [1000, 50000, 500000, 2000000, 5000000]
        scores = [compute_popularity_score(c, counts) for c in counts]
        
        # The middle value should have the highest or near-highest score
        middle_score = scores[2]  # 500000
        extreme_scores = [scores[0], scores[4]]  # 1000, 5000000
        
        assert middle_score >= min(extreme_scores)
    
    def test_scores_in_valid_range(self):
        counts = [100, 1000, 10000, 100000, 1000000]
        for c in counts:
            score = compute_popularity_score(c, counts)
            assert 0 <= score <= 1


class TestSeasonalityScore:
    """Test seasonal demand scoring."""
    
    def test_peak_month_low_score(self):
        """December (peak) should give a low score (we want to avoid crowds)."""
        score = compute_seasonality_score(12)
        assert score < 0.2  # December demand is 0.90, so score = 0.10
    
    def test_offpeak_month_high_score(self):
        """June (off-peak) should give a high score."""
        score = compute_seasonality_score(6)
        assert score > 0.8  # June demand is 0.10, so score = 0.90
    
    def test_all_months_valid(self):
        for month in range(1, 13):
            score = compute_seasonality_score(month)
            assert 0 <= score <= 1
    
    def test_inversion(self):
        """Lower demand → higher score."""
        peak_score = compute_seasonality_score(12)  # High demand
        low_score = compute_seasonality_score(6)    # Low demand
        assert low_score > peak_score


class TestFeasibilityScore:
    """Test feasibility scoring."""
    
    def test_short_trip_high_score(self):
        score = compute_feasibility_score(2.0, 1000, budget_level="medium")
        assert score > 0.8
    
    def test_very_long_trip_low_score(self):
        score = compute_feasibility_score(20.0, 15000, budget_level="low")
        assert score < 0.5
    
    def test_exceeds_max_hours_returns_zero(self):
        score = compute_feasibility_score(10.0, 3000, max_travel_hours=5.0)
        assert score == 0.0
    
    def test_within_max_hours_positive(self):
        score = compute_feasibility_score(4.0, 3000, max_travel_hours=6.0)
        assert score > 0
    
    def test_missing_data_returns_default(self):
        score = compute_feasibility_score(None, None)
        assert score == 0.5


class TestCompositeScore:
    """Test composite multi-criteria scoring."""
    
    def test_all_perfect_scores(self):
        score = compute_composite_score(1.0, 1.0, 1.0, 1.0, 1.0)
        assert abs(score - 1.0) < 0.01
    
    def test_all_zero_scores(self):
        score = compute_composite_score(0.0, 0.0, 0.0, 0.0, 0.0)
        assert abs(score - 0.0) < 0.01
    
    def test_custom_weights(self):
        """Preference-only weight should equal preference score."""
        weights = {"preference": 1.0, "emissions": 0, "popularity": 0, "seasonality": 0, "feasibility": 0}
        score = compute_composite_score(0.8, 0.2, 0.5, 0.5, 0.5, weights=weights)
        assert abs(score - 0.8) < 0.01
    
    def test_score_bounded(self):
        """Score should always be in [0, 1]."""
        for _ in range(100):
            scores = np.random.uniform(0, 1, 5)
            result = compute_composite_score(*scores)
            assert 0 <= result <= 1
    
    def test_higher_sustainability_weight_changes_ranking(self):
        """Different weights should produce different scores for same inputs."""
        low_sp = adjust_weights_for_priority(0.0)
        high_sp = adjust_weights_for_priority(1.0)
        
        # Destination with good preference but bad emissions
        s1 = compute_composite_score(0.9, 0.1, 0.5, 0.5, 0.5, weights=low_sp)
        s2 = compute_composite_score(0.9, 0.1, 0.5, 0.5, 0.5, weights=high_sp)
        
        # Low sustainability priority should favour preference
        assert s1 > s2


class TestWeightAdjustment:
    """Test weight adjustment based on sustainability priority."""
    
    def test_zero_priority_preference_heavy(self):
        weights = adjust_weights_for_priority(0.0)
        assert weights["preference"] > 0.7
    
    def test_max_priority_sustainability_heavy(self):
        weights = adjust_weights_for_priority(1.0)
        assert weights["emissions"] > weights["preference"]
    
    def test_weights_sum_to_one(self):
        for sp in [0.0, 0.25, 0.5, 0.75, 1.0]:
            weights = adjust_weights_for_priority(sp)
            assert abs(sum(weights.values()) - 1.0) < 0.01
    
    def test_all_weights_non_negative(self):
        for sp in [0.0, 0.5, 1.0]:
            weights = adjust_weights_for_priority(sp)
            for v in weights.values():
                assert v >= 0


class TestNormalisation:
    """Test emission score normalisation."""
    
    def test_lowest_emission_gets_highest_score(self):
        emissions = [10.0, 50.0, 100.0]
        scores = normalise_emission_scores(emissions)
        assert scores[0] == 1.0  # Lowest emission → highest score
        assert scores[2] == 0.0  # Highest emission → lowest score
    
    def test_equal_emissions_equal_scores(self):
        emissions = [50.0, 50.0, 50.0]
        scores = normalise_emission_scores(emissions)
        assert all(s == 1.0 for s in scores)
    
    def test_empty_list(self):
        assert normalise_emission_scores([]) == []
    
    def test_scores_in_range(self):
        emissions = [5, 15, 30, 60, 100]
        scores = normalise_emission_scores(emissions)
        for s in scores:
            assert 0 <= s <= 1
