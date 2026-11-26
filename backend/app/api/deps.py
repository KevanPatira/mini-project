"""
Shared singleton instances and dependencies for FastAPI routes.
"""

import os
import logging
from app.recommendation.engine import RecommendationEngine
from app.itinerary.builder import ItineraryBuilder
from app.evaluation.runner import ExperimentRunner

logger = logging.getLogger(__name__)

# Initialize core recommendation engine, itinerary builder, and experiment runner
engine = RecommendationEngine()
itinerary_builder = ItineraryBuilder(engine.attractions_df)
experiment_runner = ExperimentRunner(engine)

# Default path for persistent user study survey responses
DEFAULT_USER_STUDY_FILE = os.getenv(
    "USER_STUDY_FILE",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "results", "user_study_responses.json")
    )
)
