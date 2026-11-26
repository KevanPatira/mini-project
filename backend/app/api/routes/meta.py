"""
Metadata & System Health Endpoints
"""

import json
from fastapi import APIRouter
from app.config import INTEREST_CATEGORIES, ORIGIN_CITIES, SEASONAL_DEMAND_INDEX, PROCESSED_DATA_DIR
from app.api.deps import engine
from app.itinerary.ors_client import check_ors_status

router = APIRouter(tags=["Metadata"])


@router.get("/api/health")
def health_check():
    """Service health check."""
    return {
        "status": "ok",
        "service": "sustainable-tourism-recommender",
        "version": "0.1.0",
        "total_attractions": len(engine.attractions_df),
    }


@router.get("/api/meta/categories")
def get_categories():
    """Available interest categories."""
    return {
        "categories": list(INTEREST_CATEGORIES.keys()),
        "descriptions": {
            "history": "Historical sites, monuments, forts, ruins",
            "architecture": "Architectural marvels, palaces, unique buildings",
            "nature": "Natural landscapes, gardens, lakes, parks",
            "wildlife": "Wildlife sanctuaries, national parks, zoos",
            "culture": "Museums, galleries, cultural experiences",
            "religion": "Temples, mosques, religious sites",
            "adventure": "Theme parks, trekking, desert safaris",
            "food": "Food markets, culinary experiences",
            "shopping": "Markets, bazaars, handicraft shops",
            "relaxation": "Spas, peaceful lakes, gardens",
        },
    }


@router.get("/api/meta/origins")
def get_origins():
    """Available origin cities."""
    return {
        "origins": {
            k: {"name": v["name"], "lat": v["lat"], "lon": v["lon"]}
            for k, v in ORIGIN_CITIES.items()
        }
    }


@router.get("/api/meta/seasonal-demand")
def get_seasonal_demand():
    """Monthly seasonal demand index for Rajasthan."""
    return {
        "demand_index": SEASONAL_DEMAND_INDEX,
        "data_source": "heuristic",
        "description": "Monthly relative tourism demand (0=lowest, 1=peak). Based on known climate patterns and tourism literature.",
    }


@router.get("/api/meta/routing-status")
def get_routing_status():
    """Check OpenRouteService routing status and API key connectivity."""
    return check_ors_status()


@router.get("/api/meta/transport-summary")
def get_transport_summary():
    """Summary of empirical transport routes, fares, and coverage across Rajasthan."""
    summary_path = PROCESSED_DATA_DIR / "transport_summary_metrics.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"status": "uninitialized"}
