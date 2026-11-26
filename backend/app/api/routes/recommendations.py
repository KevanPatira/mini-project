"""
Recommendation & Ablation Comparison Endpoints
"""

from fastapi import APIRouter, HTTPException
from app.data_ingestion.models import UserPreferences, ComparisonRequest
from app.api.deps import engine

router = APIRouter(tags=["Recommendations"])


@router.post("/api/recommend")
def get_recommendations(preferences: UserPreferences):
    """
    Get ranked destination recommendations based on user preferences.
    
    Uses multi-criteria sustainability-aware ranking by default.
    Set sustainability_priority=0 for baseline interest-only ranking.
    """
    try:
        if preferences.sustainability_priority == 0:
            results = engine.recommend_baseline(
                user_interests=preferences.interests,
                top_k=10,
            )
            config = "C1_baseline"
        else:
            results = engine.recommend_multicriteria(
                user_interests=preferences.interests,
                origin_city=preferences.origin_city,
                travel_month=preferences.travel_month,
                sustainability_priority=preferences.sustainability_priority,
                preferred_transport=preferences.preferred_transport.value if preferences.preferred_transport else None,
                max_travel_hours=preferences.max_travel_hours,
                budget_level=preferences.budget_level or "medium",
                top_k=10,
            )
            config = "C5_full"
        
        warnings = []
        if preferences.sustainability_priority > 0 and preferences.travel_month in [5, 6, 7, 8]:
            warnings.append(
                f"Month {preferences.travel_month} is low/off season in Rajasthan. "
                "Fewer tourism services may be available, but crowd levels will be lower."
            )
        
        return {
            "recommendations": results,
            "total_candidates": len(engine.attractions_df),
            "configuration": config,
            "weights": results[0]["weights_used"] if results else {},
            "warnings": warnings,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/compare")
def compare_recommendations(request: ComparisonRequest):
    """
    Compare recommendations across all configurations (C1–C5).
    
    Returns ranked results for each configuration to enable
    side-by-side comparison of how sustainability components affect rankings.
    """
    try:
        results = engine.compare_configurations(
            user_interests=request.preferences.interests,
            origin_city=request.preferences.origin_city,
            travel_month=request.preferences.travel_month,
            sustainability_priority=request.preferences.sustainability_priority,
            preferred_transport=request.preferences.preferred_transport.value if request.preferences.preferred_transport else None,
            top_k=10,
        )
        return {
            "comparisons": results,
            "configurations": list(results.keys()),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
