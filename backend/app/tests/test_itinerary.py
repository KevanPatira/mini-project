"""
Tests for the Itinerary Builder module.
"""

import pytest
from app.itinerary.builder import (
    ItineraryBuilder,
    estimate_road_distance_km,
    solve_tsp_nearest_neighbor,
    refine_route_2opt,
)
from app.data_ingestion.loader import load_attractions


class TestItineraryBuilder:
    @classmethod
    def setup_class(cls):
        cls.builder = ItineraryBuilder()
        cls.df = load_attractions()

    def test_estimate_road_distance(self):
        # Straight line between Delhi and Jaipur is ~235km, road should be ~305km
        road = estimate_road_distance_km(28.6139, 77.2090, 26.9124, 75.7873)
        assert road > 235
        assert road < 350

    def test_solve_tsp_empty_or_single(self):
        assert solve_tsp_nearest_neighbor((28.0, 77.0), []) == []
        dest = [{"latitude": 26.0, "longitude": 75.0, "name": "Point A"}]
        assert solve_tsp_nearest_neighbor((28.0, 77.0), dest) == dest

    def test_build_itinerary_valid(self):
        sample_ids = ["raj_001", "raj_002", "raj_003"]
        itin = self.builder.build_itinerary(
            origin_city="delhi",
            attraction_ids=sample_ids,
            trip_duration_days=3,
            optimize_for="balanced",
        )
        assert "stops" in itin
        assert len(itin["stops"]) == 3
        assert itin["total_distance_km"] > 0
        assert itin["total_emissions_kg"] > 0
        assert itin["total_days"] >= 1
        assert "baseline_car_emissions_kg" in itin
        assert itin["co2_savings_kg"] >= 0

    def test_build_itinerary_invalid_ids(self):
        with pytest.raises(ValueError):
            self.builder.build_itinerary(
                origin_city="delhi",
                attraction_ids=["invalid_id_999"],
            )

    def test_itinerary_day_progression(self):
        # 6 attractions spread out should span across multiple days
        sample_ids = ["raj_001", "raj_002", "raj_008", "raj_010", "raj_015", "raj_020"]
        itin = self.builder.build_itinerary(
            origin_city="delhi",
            attraction_ids=sample_ids,
            trip_duration_days=5,
        )
        days = [s["day"] for s in itin["stops"]]
        assert days[0] == 1
        # Days should be monotonically non-decreasing
        assert all(days[i] <= days[i + 1] for i in range(len(days) - 1))
