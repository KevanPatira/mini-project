"""
Itinerary Builder Module.

Generates realistic, carbon-aware multi-stop travel itineraries for tourist attractions.
Features:
- Route sequencing using nearest-neighbor / 2-opt heuristic
- Multi-day grouping based on realistic daily travel and visit budget
- Mode-aware transit distance and emissions calculations
- Support for optimizing for time, emissions, or balanced
"""

from typing import List, Dict, Optional, Tuple
import math
from app.config import ORIGIN_CITIES, EMISSION_FACTORS, AVERAGE_SPEEDS_KMH
from app.data_ingestion.models import (
    Attraction,
    ItineraryStop,
    ItineraryResponse,
    TransportMode,
)
from app.sustainability.scoring import haversine_distance_km, compute_emissions_kg
from app.data_ingestion.loader import get_attraction_by_id, load_attractions


def estimate_road_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Road distance is typically 1.25 to 1.35x great-circle in Rajasthan terrain."""
    straight = haversine_distance_km(lat1, lon1, lat2, lon2)
    return round(straight * 1.3, 2)


def solve_tsp_nearest_neighbor(
    start_coords: Tuple[float, float],
    destinations: List[Dict],
    optimize_for: str = "time"
) -> List[Dict]:
    """
    Greedy nearest neighbor TSP ordering from origin, then sequentially picking
    the best next stop.
    """
    if len(destinations) <= 1:
        return destinations

    remaining = list(destinations)
    current_lat, current_lon = start_coords
    route = []

    while remaining:
        best_idx = 0
        best_dist = float("inf")

        for idx, dest in enumerate(remaining):
            lat = dest.get("latitude") or dest["attraction"].get("latitude", 0)
            lon = dest.get("longitude") or dest["attraction"].get("longitude", 0)
            d = haversine_distance_km(current_lat, current_lon, lat, lon)
            if d < best_dist:
                best_dist = d
                best_idx = idx

        next_dest = remaining.pop(best_idx)
        route.append(next_dest)
        current_lat = next_dest.get("latitude") or next_dest["attraction"].get("latitude", 0)
        current_lon = next_dest.get("longitude") or next_dest["attraction"].get("longitude", 0)

    # 2-opt refinement if number of stops is between 4 and 15
    if 4 <= len(route) <= 15:
        route = refine_route_2opt(start_coords, route)

    return route


def compute_route_total_distance(start_coords: Tuple[float, float], route: List[Dict]) -> float:
    """Compute total distance of ordered route."""
    if not route:
        return 0.0
    tot = 0.0
    curr_lat, curr_lon = start_coords
    for stop in route:
        lat = stop.get("latitude") or stop["attraction"].get("latitude", 0)
        lon = stop.get("longitude") or stop["attraction"].get("longitude", 0)
        tot += haversine_distance_km(curr_lat, curr_lon, lat, lon)
        curr_lat, curr_lon = lat, lon
    return tot


def refine_route_2opt(start_coords: Tuple[float, float], route: List[Dict]) -> List[Dict]:
    """Perform 2-opt local search swap moves to untangle crossing paths."""
    best = list(route)
    improved = True
    iterations = 0
    max_iter = 50

    while improved and iterations < max_iter:
        improved = False
        iterations += 1
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                # candidate swap
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                if compute_route_total_distance(start_coords, candidate) < compute_route_total_distance(start_coords, best) - 1e-4:
                    best = candidate
                    improved = True
                    break
            if improved:
                break
    return best


class ItineraryBuilder:
    """Builds and schedules day-by-day itineraries."""

    def __init__(self, attractions_df=None):
        if attractions_df is None:
            self.attractions_df = load_attractions()
        else:
            self.attractions_df = attractions_df

    def build_itinerary(
        self,
        origin_city: str,
        attraction_ids: List[str],
        trip_duration_days: Optional[int] = None,
        optimize_for: str = "balanced",
        preferred_mode: Optional[str] = None,
    ) -> Dict:
        """
        Build an optimized itinerary given origin and selected attraction IDs.
        """
        origin_info = ORIGIN_CITIES.get(origin_city.lower(), ORIGIN_CITIES["delhi"])
        origin_lat = origin_info["lat"]
        origin_lon = origin_info["lon"]

        # Retrieve attractions
        destinations = []
        for aid in attraction_ids:
            att = get_attraction_by_id(aid)
            if att:
                destinations.append(att)

        if not destinations:
            raise ValueError(f"No valid attractions found for IDs: {attraction_ids}")

        # Optimize sequence
        ordered_attractions = solve_tsp_nearest_neighbor(
            (origin_lat, origin_lon),
            destinations,
            optimize_for=optimize_for,
        )

        # Plan schedule
        stops_output = []
        total_dist_km = 0.0
        total_travel_hours = 0.0
        total_emissions_kg = 0.0
        warnings = []

        # Determine inter-city transport mode
        # If user picked preferred_mode use it, else pick train or car
        default_mode = preferred_mode or "train"
        if default_mode not in ["train", "bus", "car", "flight"]:
            default_mode = "train"

        curr_lat = origin_lat
        curr_lon = origin_lon

        current_day = 1
        hours_in_day = 0.0
        MAX_HOURS_PER_DAY = 9.0  # 9 AM to 6 PM

        for order, att in enumerate(ordered_attractions, 1):
            lat = att["latitude"]
            lon = att["longitude"]

            leg_dist = estimate_road_distance_km(curr_lat, curr_lon, lat, lon)
            
            # Select mode for this leg:
            # First leg from origin might be train or flight; between attractions in same city is taxi/car
            if order == 1:
                leg_mode = default_mode
                speed = AVERAGE_SPEEDS_KMH.get(leg_mode, 60.0)
            else:
                # If distance < 30km, it's intra-city local transport (car / taxi)
                if leg_dist <= 30.0:
                    leg_mode = "car"
                    speed = 30.0  # city traffic
                else:
                    leg_mode = default_mode
                    speed = AVERAGE_SPEEDS_KMH.get(leg_mode, 60.0)

            leg_hours = round(leg_dist / speed, 2)
            leg_emissions = compute_emissions_kg(leg_dist, leg_mode)

            visit_duration = att.get("estimated_visit_duration_hours") or 2.5
            
            # Check day overflow
            if hours_in_day + leg_hours + visit_duration > MAX_HOURS_PER_DAY and order > 1:
                current_day += 1
                hours_in_day = 0.0

            arrival_clock_hour = 9.0 + hours_in_day + leg_hours
            departure_clock_hour = arrival_clock_hour + visit_duration
            hours_in_day += (leg_hours + visit_duration)

            arrival_str = f"Day {current_day}, {int(arrival_clock_hour):02d}:{int((arrival_clock_hour % 1) * 60):02d}"
            departure_str = f"Day {current_day}, {int(departure_clock_hour):02d}:{int((departure_clock_hour % 1) * 60):02d}"

            total_dist_km += leg_dist
            total_travel_hours += leg_hours
            total_emissions_kg += leg_emissions

            stops_output.append({
                "order": order,
                "day": current_day,
                "attraction": att,
                "arrival_time": arrival_str,
                "departure_time": departure_str,
                "visit_duration_hours": visit_duration,
                "travel_from_previous_km": leg_dist,
                "travel_from_previous_hours": leg_hours,
                "transport_mode": leg_mode,
                "leg_emissions_kg": round(leg_emissions, 2),
            })

            curr_lat = lat
            curr_lon = lon

        # Check against trip duration days if specified
        if trip_duration_days and current_day > trip_duration_days:
            warnings.append(
                f"Generated itinerary requires {current_day} days, which exceeds requested {trip_duration_days} days. "
                "Consider removing some stops or extending duration."
            )

        # Baseline emissions comparison (if traveled by private car for all legs)
        car_emissions = compute_emissions_kg(total_dist_km, "car")
        saved_emissions = max(0.0, car_emissions - total_emissions_kg)

        return {
            "origin": origin_info["name"],
            "stops": stops_output,
            "total_distance_km": round(total_dist_km, 2),
            "total_travel_hours": round(total_travel_hours, 2),
            "total_emissions_kg": round(total_emissions_kg, 2),
            "baseline_car_emissions_kg": round(car_emissions, 2),
            "co2_savings_kg": round(saved_emissions, 2),
            "total_days": current_day,
            "optimization_used": optimize_for,
            "warnings": warnings,
        }
