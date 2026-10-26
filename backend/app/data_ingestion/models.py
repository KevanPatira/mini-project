"""
Pydantic models for data validation across the application.

These models define the schema for attractions, transport routes,
user preferences, recommendation requests/responses, and evaluation results.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class TransportMode(str, Enum):
    TRAIN = "train"
    BUS = "bus"
    CAR = "car"
    FLIGHT = "flight"


class DataSourceType(str, Enum):
    """Classification of data provenance."""
    OBSERVED = "observed"          # Real measurements or official statistics
    ESTIMATED = "estimated"        # Computed from models or factors
    HEURISTIC = "heuristic"        # Expert-derived approximation
    SYNTHETIC = "synthetic"        # Generated for testing only


class ScoreDirection(str, Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    MODERATE_IS_BETTER = "moderate_is_better"


# ─── Data Models ──────────────────────────────────────────────────────────────

class Attraction(BaseModel):
    """A tourist attraction/destination."""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Attraction name")
    description: Optional[str] = Field(None, description="Brief description")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    city: str = Field(..., description="Nearest city/town")
    district: str = Field(..., description="District name")
    categories: List[str] = Field(..., description="Interest categories (e.g., history, nature)")
    osm_tags: Optional[Dict[str, str]] = Field(None, description="Original OSM tag values")
    
    # Optional metadata
    opening_hours: Optional[str] = None
    entry_fee: Optional[str] = None
    estimated_visit_duration_hours: Optional[float] = None
    heritage_status: Optional[str] = None
    
    # Popularity (with provenance)
    annual_visitors: Optional[int] = Field(None, description="Annual visitor count if available")
    visitor_data_source: Optional[DataSourceType] = None
    visitor_data_year: Optional[int] = None
    popularity_score_raw: Optional[float] = Field(None, ge=0, le=1)
    
    # Image
    image_url: Optional[str] = None
    wikidata_id: Optional[str] = None


class TransportRoute(BaseModel):
    """Transport route between two locations."""
    origin_id: str
    destination_id: str
    transport_mode: TransportMode
    distance_km: float = Field(..., ge=0)
    duration_hours: Optional[float] = Field(None, ge=0)
    estimated_cost_inr: Optional[float] = Field(None, ge=0)
    co2_emissions_kg: float = Field(..., ge=0, description="Estimated CO₂e in kg")
    data_source: DataSourceType = DataSourceType.ESTIMATED
    distance_source: str = Field(..., description="How distance was computed")


class SeasonalDemand(BaseModel):
    """Monthly seasonal demand indicator."""
    month: int = Field(..., ge=1, le=12)
    demand_index: float = Field(..., ge=0, le=1, description="0=no demand, 1=peak demand")
    data_source: DataSourceType = DataSourceType.HEURISTIC
    source_description: str


class WeatherData(BaseModel):
    """Monthly weather summary for a location."""
    city: str
    month: int = Field(..., ge=1, le=12)
    avg_max_temp_c: Optional[float] = None
    avg_min_temp_c: Optional[float] = None
    avg_rainfall_mm: Optional[float] = None
    comfort_score: Optional[float] = Field(None, ge=0, le=1)
    data_source: DataSourceType = DataSourceType.OBSERVED


# ─── API Request/Response Models ─────────────────────────────────────────────

class UserPreferences(BaseModel):
    """User's travel preferences for recommendation."""
    interests: List[str] = Field(..., min_length=1, description="Selected interest categories")
    origin_city: str = Field(..., description="Starting city identifier")
    travel_month: int = Field(..., ge=1, le=12, description="Intended month of travel")
    trip_duration_days: Optional[int] = Field(None, ge=1, le=30)
    budget_level: Optional[str] = Field("medium", pattern="^(low|medium|high)$")
    preferred_transport: Optional[TransportMode] = None
    sustainability_priority: float = Field(0.5, ge=0, le=1, description="0=ignore sustainability, 1=max sustainability")
    max_travel_hours: Optional[float] = Field(None, ge=0)
    
    @field_validator("interests")
    @classmethod
    def validate_interests(cls, v):
        from app.config import INTEREST_CATEGORIES
        valid = set(INTEREST_CATEGORIES.keys())
        for interest in v:
            if interest not in valid:
                raise ValueError(f"Unknown interest: {interest}. Valid: {sorted(valid)}")
        return v
    
    @field_validator("origin_city")
    @classmethod
    def validate_origin(cls, v):
        from app.config import ORIGIN_CITIES
        if v not in ORIGIN_CITIES:
            raise ValueError(f"Unknown origin: {v}. Valid: {sorted(ORIGIN_CITIES.keys())}")
        return v


class ScoreBreakdown(BaseModel):
    """Breakdown of how each component contributed to the final score."""
    preference_score: float = Field(..., ge=0, le=1)
    emission_score: float = Field(..., ge=0, le=1)
    popularity_score: float = Field(..., ge=0, le=1)
    seasonality_score: float = Field(..., ge=0, le=1)
    feasibility_score: float = Field(..., ge=0, le=1)
    
    # Data quality flags
    has_emission_data: bool = True
    has_popularity_data: bool = True
    has_seasonality_data: bool = True
    has_feasibility_data: bool = True


class RecommendationResult(BaseModel):
    """A single recommended destination with scores and explanation."""
    rank: int
    attraction: Attraction
    final_score: float = Field(..., ge=0, le=1)
    score_breakdown: ScoreBreakdown
    
    # Transport info
    transport_mode: Optional[TransportMode] = None
    distance_km: Optional[float] = None
    travel_hours: Optional[float] = None
    estimated_emissions_kg: Optional[float] = None
    estimated_cost_inr: Optional[float] = None
    
    # Explanation
    explanation: str = Field(..., description="Template-based explanation of why this was recommended")
    data_quality_notes: List[str] = Field(default_factory=list, description="Transparency notes about data quality")
    
    # Weights used
    weights_used: Dict[str, float] = Field(..., description="Weight configuration that produced this ranking")


class RecommendationResponse(BaseModel):
    """Full recommendation response."""
    recommendations: List[RecommendationResult]
    total_candidates: int
    configuration: str = Field(..., description="Which scoring configuration was used")
    weights: Dict[str, float]
    warnings: List[str] = Field(default_factory=list)


class ComparisonRequest(BaseModel):
    """Request to compare recommendations with different weight configurations."""
    preferences: UserPreferences
    configurations: List[Dict[str, float]] = Field(
        ..., 
        min_length=2,
        description="List of weight configs to compare"
    )


class ItineraryRequest(BaseModel):
    """Request for multi-stop itinerary generation."""
    preferences: UserPreferences
    selected_attraction_ids: Optional[List[str]] = Field(default_factory=list)
    optimize_for: str = Field("time", pattern="^(time|emissions|balanced)$")
    strategy: str = Field("2opt", pattern="^(2opt|drl)$")


class ItineraryStop(BaseModel):
    """A single stop in an itinerary."""
    order: int
    attraction: Attraction
    arrival_time: Optional[str] = None
    departure_time: Optional[str] = None
    visit_duration_hours: Optional[float] = None
    travel_from_previous_km: Optional[float] = None
    travel_from_previous_hours: Optional[float] = None
    transport_mode: Optional[TransportMode] = None
    transit_fare_inr: Optional[float] = None
    entry_fee_inr: Optional[float] = None
    total_leg_cost_inr: Optional[float] = None


class ItineraryResponse(BaseModel):
    """Generated itinerary."""
    stops: List[ItineraryStop]
    total_distance_km: float
    total_travel_hours: float
    total_emissions_kg: float
    total_days: int
    total_cost_inr: Optional[float] = None
    total_fare_inr: Optional[float] = None
    total_entry_fees_inr: Optional[float] = None
    remaining_budget_inr: Optional[float] = None
    strategy_used: Optional[str] = "2opt"
    provenance_mode: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


# ─── Evaluation Models ───────────────────────────────────────────────────────

class EvaluationMetrics(BaseModel):
    """Metrics from a single evaluation run."""
    configuration: str
    persona: str
    category_match_rate: float
    total_estimated_emissions_kg: float
    category_diversity: int
    geographic_spread_km: float
    popularity_gini: float
    avg_travel_hours: Optional[float] = None
    avg_preference_score: float
    top_k: int
