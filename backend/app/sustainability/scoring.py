"""
Sustainability scoring module.

Computes individual sustainability component scores and the composite
multi-criteria sustainability index for each destination.

Components:
1. Emissions score — based on transport CO₂e from origin to destination
2. Popularity score — based on visitor volume / search interest
3. Seasonality score — based on monthly tourism demand index
4. Feasibility score — based on travel time and estimated cost

Reference: Banerjee et al. (2025) composite sustainability index concept.
Our implementation adapts the general framework with India-specific data and
transparent handling of missing components.

All scores are normalised to [0, 1] where 1.0 = best.
Score directions are explicitly documented per component.
"""

import numpy as np
import pandas as pd
import math
import logging
from typing import Dict, List, Optional, Tuple

from app.config import (
    EMISSION_FACTORS,
    SEASONAL_DEMAND_INDEX,
    ORIGIN_CITIES,
    RAJASTHAN_HUBS,
    MISSING_SCORE_DEFAULT,
    DEFAULT_WEIGHTS,
    SCORE_DIRECTIONS,
)

logger = logging.getLogger(__name__)


# ─── Distance Calculation ────────────────────────────────────────────────────

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute great-circle distance between two points using the Haversine formula.
    
    Args:
        lat1, lon1: Coordinates of point 1 (degrees)
        lat2, lon2: Coordinates of point 2 (degrees)
    
    Returns:
        Distance in kilometres.
    """
    R = 6371.0  # Earth's radius in km
    
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def estimate_road_distance_km(straight_line_km: float) -> float:
    """
    Estimate road distance from straight-line distance.
    
    Uses a detour factor of 1.3 (common for Indian road networks).
    This is an ESTIMATE — real road distances may vary significantly.
    """
    DETOUR_FACTOR = 1.3
    return straight_line_km * DETOUR_FACTOR


# ─── Emissions Scoring ──────────────────────────────────────────────────────

def compute_emissions_kg(distance_km: float, transport_mode: str) -> float:
    """
    Compute estimated CO₂e emissions for a trip.
    
    Args:
        distance_km: Trip distance in km
        transport_mode: One of 'train', 'bus', 'car', 'flight'
    
    Returns:
        Estimated emissions in kg CO₂e (one-way).
        
    Note: Uses India-specific emission factors (national averages).
    """
    factor = EMISSION_FACTORS.get(transport_mode)
    if factor is None:
        raise ValueError(f"Unknown transport mode: {transport_mode}. Valid: {list(EMISSION_FACTORS.keys())}")
    
    # factor is in g CO₂e / passenger-km, convert to kg
    return (distance_km * factor) / 1000.0


def compute_emission_score(
    origin_lat: float, origin_lon: float,
    dest_lat: float, dest_lon: float,
    transport_mode: Optional[str] = None,
) -> Dict:
    """
    Compute emission details for travelling from origin to destination.
    
    If transport_mode is None, computes for all available modes and returns
    the lowest-emission option as the recommended mode.
    
    Returns dict with emission details per mode and recommended mode.
    """
    straight_km = haversine_distance_km(origin_lat, origin_lon, dest_lat, dest_lon)
    road_km = estimate_road_distance_km(straight_km)
    
    results = {}
    
    modes_to_check = [transport_mode] if transport_mode else list(EMISSION_FACTORS.keys())
    
    for mode in modes_to_check:
        if mode == "flight":
            # Flights use straight-line distance (great circle)
            # Only available if distance > 200 km (practical minimum for domestic flights)
            if straight_km < 200:
                continue
            dist = straight_km * 1.1  # 10% overhead for non-direct routing
        else:
            dist = road_km
        
        emissions_kg = compute_emissions_kg(dist, mode)
        
        # Estimate travel time (rough heuristics)
        if mode == "train":
            speed_kmh = 55  # Average Indian train speed including stops
        elif mode == "bus":
            speed_kmh = 45
        elif mode == "car":
            speed_kmh = 60
        elif mode == "flight":
            speed_kmh = 600  # Plus 2 hours overhead for airport
            dist_for_time = straight_km
        else:
            speed_kmh = 50
        
        if mode == "flight":
            travel_hours = (straight_km / speed_kmh) + 2.0  # Airport overhead
        else:
            travel_hours = road_km / speed_kmh
        
        # Rough cost estimates (INR) — HEURISTIC
        if mode == "train":
            cost_inr = road_km * 1.2  # ~INR 1.2/km (sleeper class)
        elif mode == "bus":
            cost_inr = road_km * 1.5
        elif mode == "car":
            cost_inr = road_km * 8.0  # Fuel + tolls for private car
        elif mode == "flight":
            cost_inr = 3000 + straight_km * 4.0  # Base fare + per-km
        else:
            cost_inr = None
        
        results[mode] = {
            "distance_km": round(dist, 1),
            "emissions_kg": round(emissions_kg, 2),
            "travel_hours": round(travel_hours, 1),
            "estimated_cost_inr": round(cost_inr, 0) if cost_inr else None,
            "data_source": "estimated",
            "distance_type": "great_circle" if mode == "flight" else "road_estimate",
        }
    
    # Find lowest emission mode
    if results:
        best_mode = min(results, key=lambda m: results[m]["emissions_kg"])
        results["recommended_mode"] = best_mode
    
    return results


def normalise_emission_scores(emissions: List[float]) -> List[float]:
    """
    Normalise emission values to [0, 1] scores.
    Lower emissions = higher score (inverted).
    
    Uses min-max normalisation within the candidate set.
    """
    if not emissions:
        return []
    
    arr = np.array(emissions, dtype=float)
    min_val, max_val = arr.min(), arr.max()
    
    if max_val == min_val:
        return [1.0] * len(emissions)  # All equal = all good
    
    # Invert: lower emissions → higher score
    normalised = 1.0 - (arr - min_val) / (max_val - min_val)
    return normalised.tolist()


# ─── Popularity Scoring ─────────────────────────────────────────────────────

def compute_popularity_score(
    annual_visitors: Optional[int],
    all_visitor_counts: List[Optional[int]],
) -> float:
    """
    Compute popularity score for a destination.
    
    Score direction: MODERATE popularity is preferred.
    - Very popular sites get lower scores (overtourism concern)
    - Very unknown sites get lower scores (may lack infrastructure)
    - Moderately popular sites get higher scores
    
    Uses a bell-curve-like transformation:
    score = 1 - |2 * normalised_rank - 1|
    
    This penalises both extremes of the popularity spectrum.
    """
    if annual_visitors is None:
        return MISSING_SCORE_DEFAULT
    
    # Filter to only destinations with visitor data
    valid_counts = [v for v in all_visitor_counts if v is not None]
    
    if not valid_counts or len(valid_counts) < 2:
        return MISSING_SCORE_DEFAULT
    
    # Normalise using log scale (visitor counts can span orders of magnitude)
    log_counts = np.log1p(valid_counts)
    log_current = np.log1p(annual_visitors)
    
    min_log, max_log = min(log_counts), max(log_counts)
    
    if max_log == min_log:
        normalised_rank = 0.5
    else:
        normalised_rank = (log_current - min_log) / (max_log - min_log)
    
    # Bell curve: moderate = best, extremes = worse
    score = 1.0 - abs(2 * normalised_rank - 1)
    
    return round(max(0.0, min(1.0, score)), 4)


def normalise_popularity_scores(
    visitor_counts: List[Optional[int]],
) -> List[float]:
    """
    Normalise popularity across all destinations.
    Returns scores where moderate popularity = highest score.
    """
    return [
        compute_popularity_score(v, visitor_counts)
        for v in visitor_counts
    ]


def compute_seasonality_score(month: int, attraction: Optional[Dict] = None) -> float:
    """
    Compute seasonality score for a given travel month and optional attraction context.
    
    Score direction: Higher score = more seasonally optimal / crowd-sustainable.
    - Low regional peak crowd pressure yields higher baseline score.
    - Destination-specific climatic factors:
      * Desert regions (Jaisalmer, Bikaner, Osian) during peak summer (May, June) receive heat penalties.
      * High altitude / hill station (Mount Abu) during summer/monsoon receives a climate refuge bonus.
      * Wildlife sanctuaries (Ranthambore, Keoladeo) receive monsoon seasonal closure/breeding penalties (July-September)
        and winter migratory advantages (Nov-Feb).
    
    Data source: HEURISTIC / Climatic Norms (Open-Meteo & IMD Rajasthan normals).
    """
    base_demand = SEASONAL_DEMAND_INDEX.get(month, 0.5)
    base_score = 1.0 - base_demand  # lower regional demand -> higher sustainability score

    if not attraction:
        return round(max(0.0, min(1.0, base_score)), 4)

    # Contextual climate and attraction-type adjustment
    adjustment = 0.0
    city = (attraction.get("city") or "").lower()
    district = (attraction.get("district") or "").lower()
    categories = [c.lower() for c in attraction.get("categories", [])]

    # 1. Hill station refuge during hot summer months
    if "mount abu" in city or "sirohi" in district:
        if month in [4, 5, 6, 7]:  # summer refuge
            adjustment += 0.25
        elif month in [11, 12, 1]:
            adjustment -= 0.05

    # 2. Extreme desert heat penalty
    if city in ["jaisalmer", "bikaner", "osian"]:
        if month in [5, 6]:  # peak summer >44C
            adjustment -= 0.35
        elif month in [4, 7]:  # hot shoulder
            adjustment -= 0.15
        elif month in [11, 12, 1, 2]:  # optimal desert season
            adjustment += 0.10

    # 3. Wildlife sanctuary seasonal dynamics
    if "wildlife" in categories or "nature" in categories:
        if month in [7, 8, 9]:  # monsoon: parks closed / difficult terrain
            adjustment -= 0.30
        elif month in [11, 12, 1, 2]:  # prime bird migration & tiger sightings
            adjustment += 0.15

    # 4. Lake city post-monsoon freshness
    if "udaipur" in city:
        if month in [9, 10, 11]:  # full lakes, pleasant weather
            adjustment += 0.10

    final_score = base_score + adjustment
    return round(max(0.05, min(1.0, final_score)), 4)



# ─── Feasibility Scoring ────────────────────────────────────────────────────

def compute_feasibility_score(
    travel_hours: Optional[float],
    cost_inr: Optional[float],
    max_travel_hours: Optional[float] = None,
    budget_level: str = "medium",
) -> float:
    """
    Compute feasibility score based on travel time and cost.
    
    Shorter travel time and lower cost = higher score.
    Hard constraint: if travel_hours > max_travel_hours, return 0.
    """
    if travel_hours is None and cost_inr is None:
        return MISSING_SCORE_DEFAULT
    
    # Hard constraint check
    if max_travel_hours and travel_hours and travel_hours > max_travel_hours:
        return 0.0
    
    time_score = 1.0
    cost_score = 1.0
    
    if travel_hours is not None:
        # Diminishing returns: up to 4h is good, beyond 12h is poor
        if travel_hours <= 4:
            time_score = 1.0
        elif travel_hours <= 8:
            time_score = 1.0 - (travel_hours - 4) * 0.1
        elif travel_hours <= 16:
            time_score = 0.6 - (travel_hours - 8) * 0.05
        else:
            time_score = max(0.1, 0.2 - (travel_hours - 16) * 0.02)
    
    if cost_inr is not None:
        # Budget thresholds
        budget_limits = {
            "low": 2000,
            "medium": 5000,
            "high": 15000,
        }
        limit = budget_limits.get(budget_level, 5000)
        
        if cost_inr <= limit:
            cost_score = 1.0
        elif cost_inr <= limit * 2:
            cost_score = 1.0 - (cost_inr - limit) / limit * 0.5
        else:
            cost_score = max(0.1, 0.5 - (cost_inr - limit * 2) / (limit * 3) * 0.4)
    
    # Combine time and cost (equal weight)
    score = 0.5 * time_score + 0.5 * cost_score
    return round(max(0.0, min(1.0, score)), 4)


# ─── Preference Scoring ─────────────────────────────────────────────────────

def compute_preference_score(
    attraction_categories: List[str],
    user_interests: List[str],
) -> float:
    """
    Compute how well an attraction matches user interests.
    
    Uses Jaccard-like overlap between attraction categories and user interests.
    """
    if not user_interests or not attraction_categories:
        return 0.0
    
    user_set = set(user_interests)
    attr_set = set(attraction_categories)
    
    overlap = user_set & attr_set
    
    if not overlap:
        return 0.0
    
    # Score is based on how many of the user's interests are matched
    # Weighted by how specific the attraction is (fewer categories = more focused)
    match_ratio = len(overlap) / len(user_set)
    
    # Bonus for highly specific matches
    specificity = len(overlap) / max(len(attr_set), 1)
    
    score = 0.7 * match_ratio + 0.3 * specificity
    return round(min(1.0, score), 4)


# ─── Composite Score ─────────────────────────────────────────────────────────

def compute_composite_score(
    preference_score: float,
    emission_score: float,
    popularity_score: float,
    seasonality_score: float,
    feasibility_score: float,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Compute the weighted composite sustainability-aware score.
    
    score = Σ (w_i × score_i) for all components
    
    All scores should be in [0, 1] where 1 = best.
    Weights should sum to 1.0.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS.copy()
    
    # Validate weights sum
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 0.01:
        logger.warning(f"Weights sum to {total_weight}, normalising to 1.0")
        weights = {k: v / total_weight for k, v in weights.items()}
    
    composite = (
        weights.get("preference", 0) * preference_score +
        weights.get("emissions", 0) * emission_score +
        weights.get("popularity", 0) * popularity_score +
        weights.get("seasonality", 0) * seasonality_score +
        weights.get("feasibility", 0) * feasibility_score
    )
    
    return round(max(0.0, min(1.0, composite)), 4)


def adjust_weights_for_priority(
    sustainability_priority: float,
    base_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Adjust scoring weights based on user's sustainability priority.
    
    sustainability_priority = 0.0: pure preference-based ranking
    sustainability_priority = 1.0: maximum sustainability weight
    
    Linear interpolation between preference-heavy and sustainability-heavy configs.
    """
    if base_weights is None:
        base_weights = DEFAULT_WEIGHTS.copy()
    
    sp = max(0.0, min(1.0, sustainability_priority))
    
    # Preference-heavy config (sp=0)
    pref_config = {
        "preference": 0.80,
        "emissions": 0.05,
        "popularity": 0.05,
        "seasonality": 0.05,
        "feasibility": 0.05,
    }
    
    # Sustainability-heavy config (sp=1)
    sust_config = {
        "preference": 0.15,
        "emissions": 0.30,
        "popularity": 0.20,
        "seasonality": 0.20,
        "feasibility": 0.15,
    }
    
    # Linear interpolation
    weights = {}
    for key in pref_config:
        weights[key] = pref_config[key] * (1 - sp) + sust_config[key] * sp
    
    return weights
