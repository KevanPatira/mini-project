"""
Itinerary generation API routes (2-opt heuristic & DRL).
"""
import logging
from fastapi import APIRouter, HTTPException
from app.data_ingestion.models import ItineraryRequest
from app.api.deps import engine, itinerary_builder
from app.rl.evaluation import generate_drl_itinerary

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/itinerary")
def generate_itinerary(request: ItineraryRequest):
    """
    Generate an optimized day-by-day travel itinerary with carbon accounting.
    Supports classical 2-opt TSP heuristics or Deep Reinforcement Learning (DRL).
    """
    try:
        if request.strategy == "drl":
            budget_map = {"low": 8000.0, "medium": 16000.0, "high": 30000.0}
            budget_inr = budget_map.get(request.preferences.budget_level, 16000.0)

            itinerary = generate_drl_itinerary(
                origin_city=request.preferences.origin_city,
                travel_month=request.preferences.travel_month,
                trip_duration_days=request.preferences.trip_duration_days or 5,
                budget_inr=budget_inr,
                user_interests=request.preferences.interests,
                preferred_transport=request.preferences.preferred_transport.value if request.preferences.preferred_transport else "train",
                selected_attraction_ids=request.selected_attraction_ids,
            )
            return itinerary

        # Default: 2-opt TSP baseline
        if not request.selected_attraction_ids:
            # If no attractions were manually selected, pre-filter top recommendations
            recs = engine.recommend_multicriteria(
                user_interests=request.preferences.interests,
                origin_city=request.preferences.origin_city,
                travel_month=request.preferences.travel_month,
                sustainability_priority=request.preferences.sustainability_priority,
                preferred_transport=request.preferences.preferred_transport.value if request.preferences.preferred_transport else None,
                budget_level=request.preferences.budget_level or "medium",
                top_k=min((request.preferences.trip_duration_days or 5) * 2, 8),
            )
            request.selected_attraction_ids = [r["attraction"]["id"] for r in recs]

        itinerary = itinerary_builder.build_itinerary(
            origin_city=request.preferences.origin_city,
            attraction_ids=request.selected_attraction_ids,
            trip_duration_days=request.preferences.trip_duration_days,
            optimize_for=request.optimize_for,
            preferred_mode=request.preferences.preferred_transport.value if request.preferences.preferred_transport else None,
        )
        itinerary["strategy_used"] = "2opt"
        itinerary["provenance_mode"] = "Heuristic Greedy + 2-Opt TSP"
        return itinerary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
