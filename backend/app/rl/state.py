"""
State Representation for the Tourism Recommendation MDP.

Encodes user context, itinerary progress, spatiotemporal constraints,
budget, and destination features into a normalized numerical state vector.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from app.config import ORIGIN_CITIES, INTEREST_CATEGORIES


class StateEncoder:
    """
    Constructs normalized state vectors for DRL itinerary planning.
    
    State Vector Composition:
    - Current Location: One-hot or coordinate embedding (lat, lon) [2 dims]
    - Visited Attractions Mask: Binary vector [N_att dims]
    - Normalized Remaining Trip Hours: [1 dim]
    - Normalized Remaining Budget (INR): [1 dim]
    - Current Itinerary Day (normalized): [1 dim]
    - Time Remaining in Current Day (normalized): [1 dim]
    - User Preference Profile: Affinity for 10 category genres [10 dims]
    - Seasonal Month Context: Sin/Cos cyclical encoding [2 dims]
    - Total Stops Visited (normalized): [1 dim]
    """

    def __init__(self, attractions: List[Dict[str, Any]]):
        self.attractions = attractions
        self.n_attractions = len(attractions)
        self.attraction_id_to_idx = {a["id"]: idx for idx, a in enumerate(attractions)}
        self.category_keys = list(INTEREST_CATEGORIES.keys())
        
        # State dimension: 2 (coords) + n_att + 1 (trip_hours) + 1 (budget) + 1 (day) + 1 (day_hours) + 10 (pref) + 2 (season) + 1 (stops)
        self.state_dim = 2 + self.n_attractions + 1 + 1 + 1 + 1 + len(self.category_keys) + 2 + 1

    def encode(
        self,
        current_lat: float,
        current_lon: float,
        visited_mask: np.ndarray,
        remaining_hours: float,
        total_hours: float,
        remaining_budget: float,
        total_budget: float,
        current_day: int,
        max_days: int,
        day_hours_remaining: float,
        max_day_hours: float,
        user_interests: List[str],
        travel_month: int,
        stops_count: int,
    ) -> np.ndarray:
        """Construct normalized 1D numpy feature vector."""
        vec = []

        # 1. Normalized Current Coordinates (Rajasthan bounding box: Lat 23-31, Lon 69-79)
        norm_lat = (current_lat - 23.0) / (31.0 - 23.0)
        norm_lon = (current_lon - 69.0) / (79.0 - 69.0)
        vec.extend([float(np.clip(norm_lat, 0.0, 1.0)), float(np.clip(norm_lon, 0.0, 1.0))])

        # 2. Visited Mask (N_att binary elements)
        vec.extend([float(x) for x in visited_mask])

        # 3. Normalized Remaining Total Trip Hours
        norm_rem_hours = remaining_hours / max(total_hours, 1.0)
        vec.append(float(np.clip(norm_rem_hours, 0.0, 1.0)))

        # 4. Normalized Remaining Budget
        norm_rem_budget = remaining_budget / max(total_budget, 1.0)
        vec.append(float(np.clip(norm_rem_budget, 0.0, 1.0)))

        # 5. Day Index & Remaining Day Hours
        norm_day = current_day / max(max_days, 1)
        norm_day_hours = day_hours_remaining / max(max_day_hours, 1.0)
        vec.extend([float(np.clip(norm_day, 0.0, 1.0)), float(np.clip(norm_day_hours, 0.0, 1.0))])

        # 6. User Interest Categories Affinity (10 dimensions)
        user_set = set(user_interests)
        cat_vec = [1.0 if cat in user_set else 0.0 for cat in self.category_keys]
        vec.extend(cat_vec)

        # 7. Seasonal Cyclical Encoding (Month 1-12 as sin/cos)
        angle = 2.0 * np.pi * (travel_month - 1) / 12.0
        vec.extend([float(np.sin(angle)), float(np.cos(angle))])

        # 8. Normalized Count of Stops Visited
        vec.append(float(np.clip(stops_count / max(self.n_attractions, 1), 0.0, 1.0)))

        return np.array(vec, dtype=np.float32)
