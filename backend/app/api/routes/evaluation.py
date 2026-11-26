"""
Academic Evaluation & Sensitivity Analysis Endpoints
"""

from fastapi import APIRouter
from app.api.deps import engine, experiment_runner
from app.data_ingestion.loader import get_data_quality_summary
from app.evaluation.runner import EVALUATION_PERSONAS

router = APIRouter(tags=["Evaluation"])


@router.get("/api/evaluation/summary")
def evaluation_summary():
    """Research dashboard data — dataset quality summary and coverage."""
    summary = get_data_quality_summary()
    return {"data_quality": summary}


@router.get("/api/evaluation/sensitivity")
def sensitivity_analysis(
    origin: str = "delhi",
    interests: str = "history,architecture",
    month: int = 11,
):
    """
    Run sensitivity analysis varying sustainability priority from 0 to 1.
    
    Returns how top-10 rankings change as sustainability weight increases.
    """
    interest_list = [i.strip() for i in interests.split(",")]
    
    results = {}
    for sp in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        try:
            recs = engine.recommend_multicriteria(
                user_interests=interest_list,
                origin_city=origin,
                travel_month=month,
                sustainability_priority=sp,
                top_k=10,
            )
            results[str(sp)] = {
                "top_10_ids": [r["attraction"]["id"] for r in recs],
                "top_10_names": [r["attraction"]["name"] for r in recs],
                "avg_preference_score": round(
                    sum(r["score_breakdown"]["preference_score"] for r in recs) / len(recs), 4
                ) if recs else 0,
                "avg_emission_score": round(
                    sum(r["score_breakdown"]["emission_score"] for r in recs) / len(recs), 4
                ) if recs else 0,
                "total_emissions_kg": round(
                    sum(r.get("estimated_emissions_kg", 0) or 0 for r in recs), 2
                ) if recs else 0,
                "weights": recs[0]["weights_used"] if recs else {},
            }
        except Exception as e:
            results[str(sp)] = {"error": str(e)}
    
    return {
        "sensitivity_analysis": results,
        "parameters": {
            "origin": origin,
            "interests": interest_list,
            "month": month,
        },
    }


@router.get("/api/evaluation/personas")
def get_personas():
    """Available research test personas (P1–P7)."""
    return {"personas": EVALUATION_PERSONAS}


@router.get("/api/evaluation/experiments")
def run_experiments():
    """Run full experimental matrix (C1–C5 × P1–P7) and return aggregated metrics."""
    results = experiment_runner.run_all_experiments()
    return results
