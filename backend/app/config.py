"""
Central configuration for the Sustainable Tourism Recommendation System.

All scoring parameters, emission factors, data paths, and defaults are
defined here. This file is the single source of truth for configurable
values used across the application.
"""

from pathlib import Path
from typing import Dict, List
import os


# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EMISSIONS_DATA_DIR = DATA_DIR / "emissions"
WEATHER_DATA_DIR = DATA_DIR / "weather"
RESULTS_DIR = DATA_DIR / "results"

# Ensure directories exist
for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, EMISSIONS_DATA_DIR, WEATHER_DATA_DIR, RESULTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ─── Emission Factors (g CO₂e per passenger-km) ─────────────────────────────
# Source: WRI India / India GHG Program / IEA benchmarks
# These are national average estimates for India.
# Reference: India Specific Rail/Road/Air Transport Emission Factors (2023-24)

EMISSION_FACTORS: Dict[str, float] = {
    "train": 17.0,    # Indian Railways (high occupancy, partially electrified)
    "bus": 40.0,       # State transport buses (average occupancy)
    "car": 150.0,      # Private car (average 1.5 occupants, petrol/diesel mix)
    "flight": 130.0,   # Domestic aviation (per seat-km, economy class)
}

AVERAGE_SPEEDS_KMH: Dict[str, float] = {
    "train": 65.0,    # Average Indian broad gauge express speed
    "bus": 45.0,      # State highway / national highway bus
    "car": 60.0,      # Highway driving in India
    "flight": 500.0,  # Commercial jet incl. takeoff/landing overhead
}

EMISSION_FACTOR_SOURCE = "WRI India / India GHG Program (national averages, 2023-24)"
EMISSION_FACTOR_NOTE = (
    "These are estimated national averages. Actual emissions depend on "
    "vehicle occupancy, fuel type, route, and electricity grid carbon intensity."
)


# ─── Interest Categories ─────────────────────────────────────────────────────
# Mapping from user-facing interest categories to OSM tag values

INTEREST_CATEGORIES: Dict[str, List[str]] = {
    "history": ["monument", "fort", "palace", "castle", "archaeological_site", "ruins", "memorial"],
    "architecture": ["monument", "fort", "palace", "castle", "building"],
    "nature": ["nature_reserve", "national_park", "garden", "park", "viewpoint", "lake"],
    "wildlife": ["zoo", "nature_reserve", "national_park", "bird_sanctuary"],
    "culture": ["museum", "gallery", "arts_centre", "theatre", "cultural"],
    "religion": ["place_of_worship", "temple", "mosque", "church", "gurudwara"],
    "adventure": ["theme_park", "water_park", "climbing", "desert", "trekking"],
    "food": ["marketplace", "market", "bazaar", "food_court"],
    "shopping": ["marketplace", "market", "bazaar", "mall"],
    "relaxation": ["spa", "resort", "beach", "lake", "garden"],
}


# ─── Origin Cities ────────────────────────────────────────────────────────────
# Major Indian cities as possible trip origins, with coordinates

ORIGIN_CITIES: Dict[str, Dict] = {
    "delhi": {"name": "New Delhi", "lat": 28.6139, "lon": 77.2090, "has_airport": True},
    "mumbai": {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "has_airport": True},
    "bangalore": {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946, "has_airport": True},
    "kolkata": {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "has_airport": True},
    "chennai": {"name": "Chennai", "lat": 13.0827, "lon": 80.2707, "has_airport": True},
    "hyderabad": {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "has_airport": True},
    "ahmedabad": {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "has_airport": True},
    "jaipur": {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "has_airport": True},
}


# ─── Rajasthan Destination Clusters ──────────────────────────────────────────
# Key cities/regions in Rajasthan for transport distance computation

RAJASTHAN_HUBS: Dict[str, Dict] = {
    "jaipur": {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "has_airport": True, "has_rail": True},
    "udaipur": {"name": "Udaipur", "lat": 24.5854, "lon": 73.7125, "has_airport": True, "has_rail": True},
    "jodhpur": {"name": "Jodhpur", "lat": 26.2389, "lon": 73.0243, "has_airport": True, "has_rail": True},
    "jaisalmer": {"name": "Jaisalmer", "lat": 26.9157, "lon": 70.9083, "has_airport": False, "has_rail": True},
    "pushkar": {"name": "Pushkar", "lat": 26.4899, "lon": 74.5542, "has_airport": False, "has_rail": True},
    "mount_abu": {"name": "Mount Abu", "lat": 24.5926, "lon": 72.7156, "has_airport": False, "has_rail": True},
    "bikaner": {"name": "Bikaner", "lat": 28.0229, "lon": 73.3119, "has_airport": False, "has_rail": True},
    "ajmer": {"name": "Ajmer", "lat": 26.4499, "lon": 74.6399, "has_airport": False, "has_rail": True},
    "ranthambore": {"name": "Ranthambore", "lat": 26.0173, "lon": 76.5026, "has_airport": False, "has_rail": True},
    "chittorgarh": {"name": "Chittorgarh", "lat": 24.8887, "lon": 74.6269, "has_airport": False, "has_rail": True},
}


# ─── Scoring Defaults ────────────────────────────────────────────────────────
# Default weights for the multi-criteria scoring function.
# All weights should sum to 1.0.

DEFAULT_WEIGHTS = {
    "preference": 0.35,     # User interest relevance
    "emissions": 0.20,      # Lower emissions → higher score
    "popularity": 0.15,     # Moderate popularity preferred
    "seasonality": 0.15,    # Lower seasonal demand → higher score
    "feasibility": 0.15,    # Shorter travel time, lower cost → higher
}

# Score direction documentation
# "higher_is_better" — after normalisation, 1.0 = best
SCORE_DIRECTIONS = {
    "preference": "higher_is_better",      # More relevant = better
    "emissions": "lower_is_better",        # Less CO₂e = better (inverted in scoring)
    "popularity": "moderate_is_better",    # Very popular or very unknown both penalised
    "seasonality": "lower_is_better",      # Lower seasonal demand = better (inverted)
    "feasibility": "higher_is_better",     # More feasible = better
}

# Missing data handling — score to assign when a component is unavailable
MISSING_SCORE_DEFAULT = 0.5  # Neutral score
MISSING_SCORE_UNCERTAINTY = True  # Flag results with missing components

# Number of recommendations to return
DEFAULT_TOP_K = 10


# ─── Seasonal Demand Index ───────────────────────────────────────────────────
# Monthly relative demand for Rajasthan tourism
# Source: Derived heuristic based on:
#   - Known peak season: October–March (pleasant weather)
#   - Monsoon low season: July–September
#   - Summer low season: May–June (extreme heat)
#   - Tourism literature and Rajasthan Tourism Department reports
# Values: 0.0 (no demand) to 1.0 (peak demand)
# DATA TYPE: HEURISTIC ESTIMATE — not observed visitor counts

SEASONAL_DEMAND_INDEX = {
    1: 0.80,   # January — peak season (winter, festivals)
    2: 0.75,   # February — peak season (pleasant weather)
    3: 0.60,   # March — shoulder (warming up, Holi)
    4: 0.35,   # April — off-peak (getting hot)
    5: 0.15,   # May — low season (extreme heat, 40-45°C)
    6: 0.10,   # June — low season (pre-monsoon heat)
    7: 0.15,   # July — low season (monsoon begins)
    8: 0.15,   # August — low season (monsoon)
    9: 0.20,   # September — low season (monsoon ending)
    10: 0.65,  # October — shoulder/peak (post-monsoon, pleasant)
    11: 0.85,  # November — peak season (festivals, Pushkar Fair)
    12: 0.90,  # December — peak season (winter holidays, New Year)
}

SEASONAL_DEMAND_SOURCE = (
    "Heuristic estimate derived from Rajasthan Tourism Department reports, "
    "known climate patterns (peak: Oct-Mar, low: May-Sep), and tourism literature. "
    "NOT based on observed monthly visitor counts."
)


# ─── API Configuration ────────────────────────────────────────────────────────

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

# OpenRouteService
ORS_API_KEY = os.getenv("ORS_API_KEY", "")
ORS_BASE_URL = "https://api.openrouteservice.org"

# Open-Meteo (no API key needed)
OPEN_METEO_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Overpass API
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
