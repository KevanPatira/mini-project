"""
FastAPI application — main entry point.

Provides modularized REST API endpoints for:
- Destination listing and details (/api/destinations)
- Recommendations and comparisons (/api/recommend, /api/compare)
- Itinerary generation (/api/itinerary)
- Reinforcement learning status and benchmarks (/api/rl/*)
- Evaluation summaries (/api/evaluation/*)
- User study questionnaire and submission (/api/user-study/*)
- Health check and system metadata (/api/health, /api/meta/*)
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.api import deps
from app.api.routes import (
    meta,
    destinations,
    recommendations,
    evaluation,
    itinerary,
    rl,
    user_study,
)

# Re-export key objects for backwards compatibility with tests and callers
engine = deps.engine
itinerary_builder = deps.itinerary_builder
experiment_runner = deps.experiment_runner
USER_STUDY_FILE = deps.DEFAULT_USER_STUDY_FILE
SurveyQuestionRating = user_study.SurveyQuestionRating
SurveySubmission = user_study.SurveySubmission

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

# Mount modular routers
app.include_router(meta.router)
app.include_router(destinations.router)
app.include_router(recommendations.router)
app.include_router(evaluation.router)
app.include_router(itinerary.router)
app.include_router(rl.router)
app.include_router(user_study.router)
