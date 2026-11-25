"""
Tests for empirical transport routes and fares ingestion and modeling.
"""

import pytest
from app.data_ingestion.loader import (
    load_transport_fare_matrix,
    get_transport_route_details,
    load_attractions,
)
from app.sustainability.scoring import compute_emission_score
from app.itinerary.builder import ItineraryBuilder
from app.rl.environment import TourismItineraryEnv


class TestTransportRoutes:
    def test_load_transport_fare_matrix(self):
        matrix = load_transport_fare_matrix()
        assert isinstance(matrix, dict)
        assert len(matrix) > 0
        # Verify key presence
        assert "delhi__jaipur__train" in matrix
        assert "delhi__jaipur__bus" in matrix
        assert "delhi__jaipur__flight" in matrix

    def test_empirical_train_route(self):
        details = get_transport_route_details("delhi", "jaipur", "train")
        assert details["is_empirical"] is True
        assert details["data_source"] == "empirical_indian_railways_schedule"
        assert 250 <= details["distance_km"] <= 350
        assert 3.0 <= details["duration_hours"] <= 7.0
        assert details["fare_inr"] > 200

    def test_empirical_bus_route(self):
        details = get_transport_route_details("delhi", "jaipur", "bus")
        assert details["is_empirical"] is True
        assert details["data_source"] == "empirical_rajasthan_bus_routes"
        assert 240 <= details["distance_km"] <= 300
        assert 4.0 <= details["duration_hours"] <= 8.0
        assert details["fare_inr"] > 250

    def test_empirical_flight_route(self):
        details = get_transport_route_details("delhi", "jaipur", "flight")
        assert details["is_empirical"] is True
        assert details["data_source"] == "empirical_flight_dataset"
        assert details["fare_inr"] > 3000

    def test_fallback_unobserved_route(self):
        # Route between small town or unobserved pair
        details = get_transport_route_details("unknown_village_a", "unknown_village_b", "bus", distance_km=100.0)
        assert details["is_empirical"] is False
        assert "calibrated" in details["data_source"]
        assert details["fare_inr"] == pytest.approx(145.0, abs=10.0)

    def test_intra_city_taxi_route(self):
        details = get_transport_route_details("jaipur", "jaipur", "car", distance_km=15.0)
        assert details["fare_inr"] == pytest.approx(15.0 * 14.0, abs=5.0)
        assert details["duration_hours"] == pytest.approx(15.0 / 30.0, abs=0.1)

    def test_scoring_uses_empirical_routes(self):
        # Delhi to Amber Fort (Jaipur)
        score_details = compute_emission_score(
            origin_lat=28.6139, origin_lon=77.2090,
            dest_lat=26.9855, dest_lon=75.8513,
            transport_mode="train",
            origin_city="delhi",
            dest_city="jaipur",
        )
        assert "train" in score_details
        train_info = score_details["train"]
        assert train_info["estimated_cost_inr"] > 200
        assert train_info["data_source"] == "empirical_indian_railways_schedule"

    def test_itinerary_builder_fare_accounting(self):
        builder = ItineraryBuilder()
        sample_ids = ["raj_001", "raj_002"]
        itin = builder.build_itinerary(
            origin_city="delhi",
            attraction_ids=sample_ids,
            preferred_mode="train",
        )
        assert "total_fare_inr" in itin
        assert "total_cost_inr" in itin
        assert itin["total_fare_inr"] > 0
        assert itin["total_cost_inr"] >= itin["total_fare_inr"]

        for stop in itin["stops"]:
            assert "transit_fare_inr" in stop
            assert "entry_fee_inr" in stop
            assert "total_leg_cost_inr" in stop
            assert stop["total_leg_cost_inr"] == pytest.approx(stop["transit_fare_inr"] + stop["entry_fee_inr"], abs=0.01)

    def test_rl_environment_budget_deduction(self):
        env = TourismItineraryEnv()
        state, info = env.reset(origin_city="delhi", budget_inr=15000.0, preferred_transport="train")
        initial_budget = env.remaining_budget
        assert initial_budget == 15000.0

        mask = info["action_mask"]
        valid_actions = [i for i, m in enumerate(mask) if m == 1 and i < env.n_attractions]
        assert len(valid_actions) > 0

        action = valid_actions[0]
        next_state, reward, done, truncated, step_info = env.step(action)
        assert env.remaining_budget < initial_budget
        assert env.total_fare_inr > 0
        assert env.total_cost_inr if hasattr(env, "total_cost_inr") else (env.total_fare_inr + env.total_entry_fees_inr) > 0

