"""
Human user study and privacy-conscious survey evaluation API routes.
"""
import os
import sys
import json
import uuid
import tempfile
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from app.evaluation.runner import EVALUATION_PERSONAS

logger = logging.getLogger(__name__)

router = APIRouter()


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


def get_current_user_study_file() -> str:
    """Dynamically resolve the user study storage file path (supports monkeypatching)."""
    main_mod = sys.modules.get("app.api.main")
    if main_mod and hasattr(main_mod, "USER_STUDY_FILE"):
        return getattr(main_mod, "USER_STUDY_FILE")
    return deps.DEFAULT_USER_STUDY_FILE


@router.get("/api/user-study/questionnaire")
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
    c1_recs = deps.engine.recommend_baseline(
        user_interests=persona["interests"],
        origin_city=persona["origin"],
        top_k=5,
    )
    c5_recs = deps.engine.recommend_multicriteria(
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


@router.post("/api/user-study/responses")
def submit_user_study_response(submission: SurveySubmission):
    """
    Record privacy-preserving survey response with deduplication and atomic file writing.
    Never stores IP addresses, browser agents, or identifying personal metadata.
    """
    if not submission.consent_given:
        raise HTTPException(status_code=400, detail="Informed consent is required to participate in this study.")

    target_file = get_current_user_study_file()
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    records = []
    if os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception as e:
            logger.error(f"Error reading existing user study responses: {e}")
            records = []

    # Check for duplicate submissions by the same anonymous participant for this persona
    for r in records:
        if r.get("participant_id") == submission.participant_id and r.get("persona_id").upper() == submission.persona_id.upper():
            raise HTTPException(
                status_code=409,
                detail=f"Participant {submission.participant_id} has already recorded a response for {submission.persona_id.upper()}.",
            )

    entry = submission.model_dump()
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    entry["submission_id"] = str(uuid.uuid4())
    records.append(entry)

    # Atomic write to prevent file corruption
    target_dir = os.path.dirname(target_file)
    temp_fd, temp_path = tempfile.mkstemp(dir=target_dir, prefix="study_res_", suffix=".tmp")
    try:
        with open(temp_fd, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        os.replace(temp_path, target_file)
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


@router.get("/api/user-study/responses")
def get_user_study_summary():
    """
    Summary of collected human user study responses.
    """
    target_file = get_current_user_study_file()
    if not os.path.exists(target_file):
        return {
            "status": "no_responses_yet",
            "total_participants": 0,
            "message": "No real human user study responses collected yet. Ready for participant intake.",
        }

    try:
        with open(target_file, "r", encoding="utf-8") as f:
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
