"""
FastAPI application — main entry point.

Provides REST API endpoints for:
- Destination listing and details
- Recommendation (baseline and multi-criteria)
- Configuration comparison
- Evaluation summaries
- Health check
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import logging

from app.config import CORS_ORIGINS, INTEREST_CATEGORIES, ORIGIN_CITIES, SEASONAL_DEMAND_INDEX
from app.data_ingestion.models import (
    UserPreferences,
    RecommendationResponse,
    ComparisonRequest,
    ItineraryRequest,
)
from app.recommendation.engine import RecommendationEngine
from app.itinerary.builder import ItineraryBuilder
from app.evaluation.runner import ExperimentRunner, EVALUATION_PERSONAS
from app.data_ingestion.loader import load_attractions, get_data_quality_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sustainable Tourism Recommendation System",
    description=(
        "A multi-criteria tourism recommendation API that balances traveller preferences "
        "with sustainability indicators including transportation emissions, destination "
        "popularity, and seasonal tourism demand. Geographic scope: Rajasthan, India."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialise recommendation engine & builders
engine = RecommendationEngine()
itinerary_builder = ItineraryBuilder(engine.attractions_df)
experiment_runner = ExperimentRunner(engine)


# ─── Health & Meta ───────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    """Service health check."""
    return {
        "status": "ok",
        "service": "sustainable-tourism-recommender",
        "version": "0.1.0",
        "total_attractions": len(engine.attractions_df),
    }


@app.get("/api/meta/categories")
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


@app.get("/api/meta/origins")
def get_origins():
    """Available origin cities."""
    return {
        "origins": {
            k: {"name": v["name"], "lat": v["lat"], "lon": v["lon"]}
            for k, v in ORIGIN_CITIES.items()
        }
    }


@app.get("/api/meta/seasonal-demand")
def get_seasonal_demand():
    """Monthly seasonal demand index for Rajasthan."""
    return {
        "demand_index": SEASONAL_DEMAND_INDEX,
        "data_source": "heuristic",
        "description": "Monthly relative tourism demand (0=lowest, 1=peak). Based on known climate patterns and tourism literature.",
    }


# ─── Destinations ────────────────────────────────────────────────────────────

@app.get("/api/destinations")
def list_destinations(
    city: Optional[str] = None,
    category: Optional[str] = None,
):
    """List available destinations with optional filters."""
    filters = {}
    if city:
        filters["city"] = city
    if category:
        filters["category"] = category
    
    destinations = engine.get_all_destinations(filters)
    return {
        "destinations": destinations,
        "total": len(destinations),
        "filters_applied": filters,
    }


@app.get("/api/destinations/{attraction_id}")
def get_destination(attraction_id: str):
    """Get detailed information about a specific destination."""
    from app.data_ingestion.loader import get_attraction_by_id
    attraction = get_attraction_by_id(attraction_id)
    if not attraction:
        raise HTTPException(status_code=404, detail=f"Attraction not found: {attraction_id}")
    return {"destination": attraction}


# ─── Recommendations ─────────────────────────────────────────────────────────

@app.post("/api/recommend")
def get_recommendations(preferences: UserPreferences):
    """
    Get ranked destination recommendations based on user preferences.
    
    Uses the multi-criteria sustainability-aware ranking by default.
    Set sustainability_priority=0 for preference-only ranking.
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


@app.post("/api/compare")
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


# ─── Evaluation ──────────────────────────────────────────────────────────────

@app.get("/api/evaluation/summary")
def evaluation_summary():
    """
    Research dashboard data — dataset quality summary and coverage.
    """
    summary = get_data_quality_summary()
    return {"data_quality": summary}


@app.get("/api/evaluation/sensitivity")
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


@app.get("/api/evaluation/personas")
def get_personas():
    """Available research test personas (P1–P7)."""
    return {"personas": EVALUATION_PERSONAS}


@app.get("/api/evaluation/experiments")
def run_experiments():
    """
    Run full experimental matrix (C1–C5 × P1–P7) and return aggregated metrics.
    """
    results = experiment_runner.run_all_experiments()
    return results


# ─── Itinerary ───────────────────────────────────────────────────────────────

from app.rl.evaluation import generate_drl_itinerary, DEFAULT_CHECKPOINT


@app.post("/api/itinerary")
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


@app.get("/api/rl/status")
def get_rl_status():
    """Returns RL model architecture, training configuration, and checkpoint status."""
    has_checkpoint = os.path.exists(DEFAULT_CHECKPOINT)
    checkpoint_meta = {}
    if has_checkpoint:
        try:
            with open(DEFAULT_CHECKPOINT, "r", encoding="utf-8") as f:
                ckpt_data = json.load(f)
                checkpoint_meta = ckpt_data.get("metadata", {})
                checkpoint_meta["step_counter"] = ckpt_data.get("step_counter", 0)
        except Exception:
            pass

    return {
        "status": "ready" if has_checkpoint else "uninitialized",
        "algorithm": "Deep Q-Network (DQN) with Action Masking",
        "architecture": "MLP (64 -> 128 -> 64 -> 46)",
        "training_mode": "Mode B (Simulator-Based MDP grounded in authentic Rajasthan data)",
        "action_space": 46,
        "state_dimension": 64,
        "checkpoint_exists": has_checkpoint,
        "checkpoint_path": DEFAULT_CHECKPOINT,
        "checkpoint_metadata": checkpoint_meta,
        "constraints_enforced": [
            "Hard budget ceiling via action masking",
            "Hard daily sightseeing hours (9h/day)",
            "No duplicate attraction visits",
            "Terminates on explicit STOP or resource exhaustion",
        ],
        "reward_weights": {
            "w_preference": 0.40,
            "w_diversity": 0.15,
            "w_travel_time": 0.15,
            "w_crowding": 0.10,
            "w_budget": 0.12,
            "w_emissions": 0.08,
            "priority_invariant": "w_budget (0.12) > w_emissions (0.08)",
        },
    }


@app.get("/api/rl/benchmark")
def get_rl_benchmark_results():
    """Returns precomputed empirical benchmark results comparing DRL vs C1 & C5."""
    results_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "results", "drl_experiment_results.json")
    )
    if not os.path.exists(results_path):
        raise HTTPException(status_code=404, detail="Benchmark results not found. Run scripts/run_drl_experiments.py first.")
    
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@app.get("/api/rl/training-curves")
def get_rl_training_curves():
    """Returns episodic returns and training loss history."""
    curves_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "results", "drl_training_curves.json")
    )
    if not os.path.exists(curves_path):
        raise HTTPException(status_code=404, detail="Training curves not found. Run scripts/train_drl.py first.")
    
    with open(curves_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"curves": data}


# ─── User Study Support (Step 5) ──────────────────────────────────────────────

# ─── User Study Support (Step 5 & Task 1-2) ───────────────────────────────────

import os
import json
import uuid
import tempfile
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class SurveyQuestionRating(BaseModel):
    relevance: int = Field(..., ge=1, le=5, description="1=Irrelevant, 5=Highly relevant")
    perceived_sustainability: int = Field(..., ge=1, le=5, description="1=Un-sustainable, 5=Highly sustainable")
    usefulness: int = Field(..., ge=1, le=5, description="1=Impractical, 5=Very useful")
    trust: int = Field(..., ge=1, le=5, description="1=Not credible, 5=Highly trustworthy")
    feasibility: int = Field(..., ge=1, le=5, description="1=Infeasible route, 5=Smooth feasible route")
    willingness_to_visit: int = Field(..., ge=1, le=5, description="1=Would not visit, 5=Eager to visit")

class SurveySubmission(BaseModel):
    participant_id: str = Field(..., min_length=4, max_length=64, description="Anonymous participant UUID/hash")
    persona_id: str = Field(..., pattern="^[pP][1-7]$")
    questionnaire_id: Optional[str] = None
    blinded_a_is: str = Field(..., pattern="^(C1_baseline|C5_full)$")
    consent_given: bool = Field(True, description="Confirmation of voluntary informed consent")
    ratings_system_a: SurveyQuestionRating
    ratings_system_b: SurveyQuestionRating
    preferred_system: str = Field(..., pattern="^(System A|System B|No preference)$")
    qualitative_feedback: Optional[str] = Field(None, max_length=1000)


USER_STUDY_FILE = os.getenv(
    "USER_STUDY_FILE",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "results", "user_study_responses.json")
    )
)

@app.get("/api/user-study/questionnaire")
def get_user_study_questionnaire(persona_id: str = "P1"):
    """
    Generate a privacy-conscious blinded A/B questionnaire comparing C1 (Baseline) and C5 (Multi-criteria).
    Does not reveal algorithm names or loaded sustainability marketing in descriptions to prevent bias.
    """
    matched = [p for p in EVALUATION_PERSONAS if p["id"].upper() == persona_id.upper()]
    if not matched:
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found. Valid: P1-P7")
    
    persona = matched[0]
    
    # Generate C1 and C5 recommendations
    c1_recs = engine.recommend_baseline(
        user_interests=persona["interests"],
        origin_city=persona["origin"],
        top_k=5,
    )
    c5_recs = engine.recommend_multicriteria(
        user_interests=persona["interests"],
        origin_city=persona["origin"],
        travel_month=persona["travel_month"],
        sustainability_priority=persona["sustainability_priority"],
        top_k=5,
    )

    # Randomly assign System A and System B to eliminate presentation order bias
    swap = (uuid.uuid4().int % 2) == 1
    system_a = c5_recs if swap else c1_recs
    system_b = c1_recs if swap else c5_recs
    blinded_mapping = {
        "System A": "C5_full" if swap else "C1_baseline",
        "System B": "C1_baseline" if swap else "C5_full",
    }

    # Format items neutrally so textual descriptions do not unblind algorithmic strategies
    def format_for_display(recs):
        return [
            {
                "rank": idx + 1,
                "name": r["attraction"]["name"],
                "city": r["attraction"]["city"],
                "district": r["attraction"].get("district", r["attraction"]["city"]),
                "categories": r["attraction"]["categories"],
                "estimated_visit_duration_hours": r["attraction"].get("estimated_visit_duration_hours"),
                "estimated_emissions_kg": r.get("estimated_emissions_kg"),
                "recommended_transport": r.get("recommended_transport"),
                "travel_hours": r.get("travel_hours"),
                "description": r["attraction"].get("description"),
            }
            for idx, r in enumerate(recs)
        ]

    return {
        "questionnaire_id": str(uuid.uuid4()),
        "study_purpose": "This academic study evaluates user perceptions of tourism recommendation strategies in Rajasthan, India. Your evaluation helps quantify how travelers value interest alignment, travel logistics, and environmental sustainability.",
        "consent_info": {
            "required": True,
            "statement": "I participate voluntarily in this anonymous study. No identifying personal data, cookies, or IP addresses will be logged.",
        },
        "scenario": {
            "persona_id": persona["id"],
            "persona_name": persona["name"],
            "origin": persona["origin"],
            "interests": persona["interests"],
            "travel_month": persona["travel_month"],
            "duration_days": persona["duration_days"],
            "budget": persona["budget"],
        },
        "system_a_items": format_for_display(system_a),
        "system_b_items": format_for_display(system_b),
        "blinded_mapping": blinded_mapping,
        "likert_scale": {
            "1": "Very Poor / Strongly Disagree",
            "2": "Poor / Disagree",
            "3": "Neutral",
            "4": "Good / Agree",
            "5": "Excellent / Strongly Agree",
        },
        "questions": [
            {"key": "relevance", "text": "Interest Relevance: Do these destinations match the traveller's stated interests?"},
            {"key": "perceived_sustainability", "text": "Perceived Sustainability: Does this itinerary appear environmentally and socially responsible?"},
            {"key": "usefulness", "text": "Practical Usefulness: Is this set of recommendations practical, varied, and appealing?"},
            {"key": "trust", "text": "Trust & Credibility: Do the recommendations and logistics feel credible and well-chosen?"},
            {"key": "feasibility", "text": "Itinerary Feasibility: Is the geographic spread and travel time realistic for the duration?"},
            {"key": "willingness_to_visit", "text": "Willingness to Visit: Would the traveller be excited to actually follow this journey?"},
        ],
    }


@app.post("/api/user-study/responses")
def submit_user_study_response(submission: SurveySubmission):
    """
    Record privacy-preserving survey response with deduplication and atomic file writing.
    Never stores IP addresses, browser agents, or identifying personal metadata.
    """
    if not submission.consent_given:
        raise HTTPException(status_code=400, detail="Informed consent is required to participate in this study.")

    os.makedirs(os.path.dirname(USER_STUDY_FILE), exist_ok=True)
    records = []
    if os.path.exists(USER_STUDY_FILE):
        try:
            with open(USER_STUDY_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception as e:
            logger.error(f"Error reading existing user study responses: {e}")
            records = []

    # Check for duplicate submissions by the same anonymous participant for this persona
    for r in records:
        if r.get("participant_id") == submission.participant_id and r.get("persona_id").upper() == submission.persona_id.upper():
            raise HTTPException(
                status_code=409,
                detail=f"Participant {submission.participant_id} has already recorded a response for {submission.persona_id.upper()}."
            )

    entry = submission.model_dump()
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    entry["submission_id"] = str(uuid.uuid4())
    records.append(entry)

    # Atomic write to prevent file corruption
    target_dir = os.path.dirname(USER_STUDY_FILE)
    temp_fd, temp_path = tempfile.mkstemp(dir=target_dir, prefix="study_res_", suffix=".tmp")
    try:
        with open(temp_fd, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        os.replace(temp_path, USER_STUDY_FILE)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Atomic file write failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to safely commit survey submission.")

    return {
        "status": "success",
        "message": "Survey response recorded securely and anonymously.",
        "submission_id": entry["submission_id"],
        "total_responses": len(records),
    }


@app.get("/api/user-study/responses")
def get_user_study_summary():
    """
    Summary of collected human user study responses.
    """
    if not os.path.exists(USER_STUDY_FILE):
        return {
            "status": "no_responses_yet",
            "total_participants": 0,
            "message": "No real human user study responses collected yet. Ready for participant intake.",
        }

    try:
        with open(USER_STUDY_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read responses: {e}")

    if not records:
        return {
            "status": "no_responses_yet",
            "total_participants": 0,
            "message": "No real human user study responses collected yet. Ready for participant intake.",
        }

    # Aggregate by true configuration
    dimensions = ["relevance", "perceived_sustainability", "usefulness", "trust", "feasibility", "willingness_to_visit"]
    c1_scores = {k: [] for k in dimensions}
    c5_scores = {k: [] for k in dimensions}
    preferred_counts = {"C1_baseline": 0, "C5_full": 0, "No preference": 0}

    for r in records:
        blinded_a = r["blinded_a_is"]  # "C1_baseline" or "C5_full"
        blinded_b = "C5_full" if blinded_a == "C1_baseline" else "C1_baseline"
        
        ratings_a = r["ratings_system_a"]
        ratings_b = r["ratings_system_b"]

        if blinded_a == "C1_baseline":
            c1_r, c5_r = ratings_a, ratings_b
        else:
            c1_r, c5_r = ratings_b, ratings_a

        for k in dimensions:
            if k in c1_r:
                c1_scores[k].append(c1_r[k])
            if k in c5_r:
                c5_scores[k].append(c5_r[k])

        pref = r.get("preferred_system")
        if pref == "System A":
            preferred_counts[blinded_a] += 1
        elif pref == "System B":
            preferred_counts[blinded_b] += 1
        else:
            preferred_counts["No preference"] += 1

    def mean_or_zero(lst):
        return round(sum(lst) / len(lst), 2) if lst else 0.0

    return {
        "status": "active",
        "total_participants": len(records),
        "mean_ratings": {
            "C1_baseline": {k: mean_or_zero(v) for k, v in c1_scores.items()},
            "C5_full": {k: mean_or_zero(v) for k, v in c5_scores.items()},
        },
        "preference_distribution": preferred_counts,
    }



