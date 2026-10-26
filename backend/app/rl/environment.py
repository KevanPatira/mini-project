"""
Gym-Compatible Tourism Itinerary Simulation Environment (MDP).

Implements the sequential recommendation Markov Decision Process for
Rajasthan heritage tourism, enforcing hard temporal and financial budget
constraints through action masking.
"""

from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
import os
import csv

from app.config import ORIGIN_CITIES, AVERAGE_SPEEDS_KMH
from app.data_ingestion.loader import load_attractions
from app.sustainability.scoring import (
    haversine_distance_km,
    estimate_road_distance_km,
    compute_emissions_kg,
)
from app.rl.state import StateEncoder
from app.rl.reward import ItineraryRewardCalculator

PROCESSED_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")
)


def load_cleaned_monument_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Load authentic entry fees and visit durations from the cleaned Kaggle dataset.
    """
    cleaned_file = os.path.join(PROCESSED_DATA_DIR, "cleaned_tourist_places_rajasthan.csv")
    meta = {}
    if os.path.exists(cleaned_file):
        try:
            with open(cleaned_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    cid = r.get("canonical_attraction_id")
                    if cid and cid not in meta:
                        try:
                            fee = float(r.get("entry_fee_inr", 0) or 0)
                        except ValueError:
                            fee = 0.0
                        meta[cid] = {
                            "entry_fee_inr": fee,
                            "visit_duration": r.get("visit_duration"),
                            "crowd_level": r.get("crowd_level"),
                            "rating": float(r.get("user_rating", 4.0) or 4.0),
                        }
        except Exception:
            pass
    return meta


class TourismItineraryEnv:
    """
    Episodic Tourism Recommender MDP Environment.
    
    Action Space:
    - 0 to N-1: Visit corresponding attraction index
    - N: Explicit STOP action
    """

    def __init__(
        self,
        attractions_df=None,
        reward_calculator: Optional[ItineraryRewardCalculator] = None,
        max_stops: int = 12,
    ):
        if attractions_df is None:
            self.attractions_df = load_attractions()
        else:
            self.attractions_df = attractions_df

        records = self.attractions_df.to_dict("records")
        clean_records = []
        for r in records:
            clean_r = {}
            for k, v in r.items():
                if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                    clean_r[k] = None
                else:
                    clean_r[k] = v
            clean_records.append(clean_r)
        self.attractions = clean_records
        self.n_attractions = len(self.attractions)
        self.stop_action_idx = self.n_attractions # Action N is STOP
        self.action_space_size = self.n_attractions + 1
        self.max_stops = max_stops

        # Load authentic fees and durations
        self.monument_meta = load_cleaned_monument_metadata()

        self.state_encoder = StateEncoder(self.attractions)
        self.state_dim = self.state_encoder.state_dim
        self.reward_calc = reward_calculator or ItineraryRewardCalculator()

        # Operational Constants
        self.HOURS_PER_DAY = 9.0  # 9 AM to 6 PM daily operational sightseeing window

        # Episode State Variables
        self.current_lat = 0.0
        self.current_lon = 0.0
        self.origin_lat = 0.0
        self.origin_lon = 0.0
        self.origin_city = "delhi"
        self.travel_month = 11
        self.user_interests = ["history", "architecture"]
        self.preferred_transport = "train"

        self.total_budget = 15000.0
        self.remaining_budget = 15000.0
        self.trip_days = 5
        self.total_hours = 45.0
        self.remaining_hours = 45.0
        self.current_day = 1
        self.day_hours_spent = 0.0

        self.visited_mask = np.zeros(self.n_attractions, dtype=np.int32)
        self.itinerary_stops = []
        self.visited_categories = set()
        self.total_distance_km = 0.0
        self.total_emissions_kg = 0.0
        self.total_fare_inr = 0.0
        self.total_entry_fees_inr = 0.0
        self.done = False

    def reset(
        self,
        origin_city: str = "delhi",
        travel_month: int = 11,
        trip_days: int = 5,
        budget_inr: float = 15000.0,
        user_interests: Optional[List[str]] = None,
        preferred_transport: str = "train",
        seed: Optional[int] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset environment to the beginning of a traveler scenario."""
        if seed is not None:
            np.random.seed(seed)

        self.origin_city = origin_city.lower()
        origin_info = ORIGIN_CITIES.get(self.origin_city, ORIGIN_CITIES["delhi"])
        self.origin_lat = origin_info["lat"]
        self.origin_lon = origin_info["lon"]
        self.current_lat = self.origin_lat
        self.current_lon = self.origin_lon

        self.travel_month = travel_month
        self.trip_days = max(trip_days, 1)
        self.total_hours = self.trip_days * self.HOURS_PER_DAY
        self.remaining_hours = self.total_hours
        self.total_budget = max(budget_inr, 0.0)
        self.remaining_budget = self.total_budget

        self.user_interests = user_interests or ["history", "architecture"]
        self.preferred_transport = preferred_transport

        self.visited_mask = np.zeros(self.n_attractions, dtype=np.int32)
        self.itinerary_stops = []
        self.visited_categories = set()
        self.current_day = 1
        self.day_hours_spent = 0.0
        self.total_distance_km = 0.0
        self.total_emissions_kg = 0.0
        self.total_fare_inr = 0.0
        self.total_entry_fees_inr = 0.0
        self.done = False

        state = self._get_state()
        info = {"action_mask": self.get_action_mask()}
        return state, info

    def _get_state(self) -> np.ndarray:
        day_rem = max(0.0, self.HOURS_PER_DAY - self.day_hours_spent)
        return self.state_encoder.encode(
            current_lat=self.current_lat,
            current_lon=self.current_lon,
            visited_mask=self.visited_mask,
            remaining_hours=self.remaining_hours,
            total_hours=self.total_hours,
            remaining_budget=self.remaining_budget,
            total_budget=self.total_budget,
            current_day=self.current_day,
            max_days=self.trip_days,
            day_hours_remaining=day_rem,
            max_day_hours=self.HOURS_PER_DAY,
            user_interests=self.user_interests,
            travel_month=self.travel_month,
            stops_count=len(self.itinerary_stops),
        )

    def get_action_mask(self) -> np.ndarray:
        """
        Binary mask of valid actions [0, 1] of size action_space_size.
        1 = Valid, 0 = Infeasible / Masked.
        """
        mask = np.zeros(self.action_space_size, dtype=np.int32)

        if self.done:
            return mask

        # Stop action is always valid once at least 1 attraction is visited
        mask[self.stop_action_idx] = 1

        for idx, att in enumerate(self.attractions):
            # 1. Do not revisit already visited attractions
            if self.visited_mask[idx] == 1:
                continue

            # 2. Check maximum stops
            if len(self.itinerary_stops) >= self.max_stops:
                continue

            # Compute travel distance and duration
            lat = att["latitude"]
            lon = att["longitude"]
            straight_dist = haversine_distance_km(self.current_lat, self.current_lon, lat, lon)
            dist_km = estimate_road_distance_km(straight_dist)

            # Determine transit mode & speed
            if dist_km <= 30.0:
                mode = "car"
                speed = 30.0
                rate_per_km = 14.0 # Intra-city taxi / auto fare per km
            else:
                mode = self.preferred_transport
                speed = AVERAGE_SPEEDS_KMH.get(mode, 60.0)
                rate_per_km = 2.0 if mode == "train" else (1.5 if mode == "bus" else 12.0)

            travel_hours = dist_km / speed
            visit_hours = att.get("estimated_visit_duration_hours") or 2.0

            # 3. Check remaining total trip duration constraint
            leg_time = travel_hours + visit_hours
            if leg_time > self.remaining_hours:
                continue

            # Check trip days limit on daily rollover
            will_rollover = (self.day_hours_spent + leg_time > self.HOURS_PER_DAY) and (len(self.itinerary_stops) > 0)
            if self.current_day + (1 if will_rollover else 0) > self.trip_days:
                continue

            # Compute cost (transit fare + entry fee)
            transit_fare = dist_km * rate_per_km
            cid = att["id"]
            if cid in self.monument_meta:
                entry_fee = self.monument_meta[cid]["entry_fee_inr"]
            else:
                # Default parsed fee proxy
                entry_fee = 50.0

            total_leg_cost = transit_fare + entry_fee

            # 4. Check remaining budget constraint
            if total_leg_cost > self.remaining_budget:
                continue

            # All constraints satisfied -> action is feasible
            mask[idx] = 1

        return mask

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Execute action, update state, and return (state, reward, terminated, truncated, info)."""
        if self.done:
            return self._get_state(), 0.0, True, False, {"message": "Episode already finished"}

        mask = self.get_action_mask()

        # Handle invalid action
        if mask[action] == 0:
            # Penalize invalid action and force termination to prevent loops
            self.done = True
            return self._get_state(), -1.0, True, False, {"error": "Invalid action selected", "action": action}

        # ── Case A: STOP action ──
        if action == self.stop_action_idx:
            self.done = True
            reward_dict = self.reward_calc.compute_step_reward(
                attraction={},
                user_interests=self.user_interests,
                travel_hours=0.0,
                leg_cost_inr=0.0,
                leg_emissions_kg=0.0,
                current_visited_categories=self.visited_categories,
                is_terminal_stop_action=True,
                stops_count=len(self.itinerary_stops),
                min_stops_target=min(self.trip_days * 2, 8),
            )
            return self._get_state(), reward_dict["total"], True, False, {"action": "STOP", "stops_total": len(self.itinerary_stops)}

        # ── Case B: Visit Attraction action ──
        att = self.attractions[action]
        lat = att["latitude"]
        lon = att["longitude"]
        straight_dist = haversine_distance_km(self.current_lat, self.current_lon, lat, lon)
        dist_km = estimate_road_distance_km(straight_dist)

        if dist_km <= 30.0:
            mode = "car"
            speed = 30.0
            rate_per_km = 14.0
        else:
            mode = self.preferred_transport
            speed = AVERAGE_SPEEDS_KMH.get(mode, 60.0)
            rate_per_km = 2.0 if mode == "train" else (1.5 if mode == "bus" else 12.0)

        travel_hours = round(dist_km / speed, 2)
        visit_hours = att.get("estimated_visit_duration_hours") or 2.0
        emissions_kg = round(compute_emissions_kg(dist_km, mode), 2)

        transit_fare = round(dist_km * rate_per_km, 2)
        cid = att["id"]
        entry_fee = self.monument_meta.get(cid, {}).get("entry_fee_inr", 50.0)
        leg_cost = transit_fare + entry_fee

        # Compute Step Reward
        reward_dict = self.reward_calc.compute_step_reward(
            attraction=att,
            user_interests=self.user_interests,
            travel_hours=travel_hours,
            leg_cost_inr=leg_cost,
            leg_emissions_kg=emissions_kg,
            current_visited_categories=self.visited_categories,
            is_terminal_stop_action=False,
            stops_count=len(self.itinerary_stops),
        )

        # Update Progress
        self.visited_mask[action] = 1
        for c in att.get("categories", []):
            self.visited_categories.add(c)

        self.remaining_budget -= leg_cost
        self.total_fare_inr += transit_fare
        self.total_entry_fees_inr += entry_fee
        self.total_distance_km += dist_km
        self.total_emissions_kg += emissions_kg

        time_spent_leg = travel_hours + visit_hours
        self.remaining_hours -= time_spent_leg

        # Check day progression
        if self.day_hours_spent + time_spent_leg > self.HOURS_PER_DAY and len(self.itinerary_stops) > 0:
            self.current_day += 1
            self.day_hours_spent = time_spent_leg
        else:
            self.day_hours_spent += time_spent_leg

        self.current_lat = lat
        self.current_lon = lon

        stop_record = {
            "order": len(self.itinerary_stops) + 1,
            "day": self.current_day,
            "attraction": att,
            "transport_mode": mode,
            "travel_distance_km": dist_km,
            "travel_hours": travel_hours,
            "visit_duration_hours": visit_hours,
            "leg_emissions_kg": emissions_kg,
            "transit_fare_inr": transit_fare,
            "entry_fee_inr": entry_fee,
            "total_leg_cost_inr": leg_cost,
        }
        self.itinerary_stops.append(stop_record)

        # Check Termination
        next_mask = self.get_action_mask()
        # If no attractions are feasible or trip days exceeded, terminate
        if next_mask[:self.n_attractions].sum() == 0 or self.current_day > self.trip_days or len(self.itinerary_stops) >= self.max_stops:
            self.done = True

        info = {
            "reward_components": reward_dict["components"],
            "stop": stop_record,
            "action_mask": next_mask,
            "remaining_budget": self.remaining_budget,
            "remaining_hours": self.remaining_hours,
        }

        return self._get_state(), reward_dict["total"], self.done, False, info
