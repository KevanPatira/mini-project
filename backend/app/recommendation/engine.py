"""
Recommendation engine — baseline and multi-criteria ranking.

Provides two recommendation strategies:
1. Baseline: Preference-only ranking (interest category matching)
2. Multi-criteria: Sustainability-aware ranking with emissions, popularity,
   seasonality, and feasibility components.

The engine is transparent about score computation and data quality.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple

from app.config import (
    ORIGIN_CITIES,
    DEFAULT_WEIGHTS,
    DEFAULT_TOP_K,
    MISSING_SCORE_DEFAULT,
    EMISSION_FACTORS,
)
from app.data_ingestion.loader import load_attractions
from app.sustainability.scoring import (
    haversine_distance_km,
    estimate_road_distance_km,
    compute_emissions_kg,
    compute_emission_score,
    compute_preference_score,
    compute_popularity_score,
    compute_seasonality_score,
    compute_feasibility_score,
    compute_composite_score,
    normalise_emission_scores,
    adjust_weights_for_priority,
)

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Core recommendation engine supporting multiple ranking strategies.
    """
    
    def __init__(self):
        self.attractions_df = load_attractions()
        logger.info(f"Recommendation engine initialised with {len(self.attractions_df)} attractions")
    
    def recommend_baseline(
        self,
        user_interests: List[str],
        origin_city: Optional[str] = None,
        preferred_transport: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[Dict]:
        """
        Baseline recommender: rank by preference relevance only.
        
        This is Configuration C1 in the experiment plan.
        If origin_city is provided, transport emissions and travel hours are
        computed post-hoc for honest comparison against sustainable configurations.
        """
        df = self.attractions_df.copy()
        
        # Compute preference scores
        df["preference_score"] = df["categories"].apply(
            lambda cats: compute_preference_score(cats, user_interests)
        )
        
        # Sort by preference score (descending)
        df = df.sort_values("preference_score", ascending=False)
        
        origin_lat, origin_lon = None, None
        if origin_city and origin_city.lower() in ORIGIN_CITIES:
            origin_info = ORIGIN_CITIES[origin_city.lower()]
            origin_lat, origin_lon = origin_info["lat"], origin_info["lon"]

        results = []
        for _, row in df.head(top_k).iterrows():
            emissions_kg = None
            travel_hours = None
            rec_mode = None

            if origin_lat is not None and origin_lon is not None:
                details = compute_emission_score(
                    origin_lat, origin_lon,
                    row["latitude"], row["longitude"],
                    transport_mode=preferred_transport,
                )
                rec_mode = preferred_transport or details.get("recommended_mode")
                if rec_mode and rec_mode in details:
                    emissions_kg = details[rec_mode].get("emissions_kg")
                    travel_hours = details[rec_mode].get("travel_hours")

            results.append({
                "rank": len(results) + 1,
                "attraction": self._attraction_to_dict(row),
                "final_score": row["preference_score"],
                "score_breakdown": {
                    "preference_score": row["preference_score"],
                    "emission_score": MISSING_SCORE_DEFAULT,
                    "popularity_score": MISSING_SCORE_DEFAULT,
                    "seasonality_score": MISSING_SCORE_DEFAULT,
                    "feasibility_score": MISSING_SCORE_DEFAULT,
                    "has_emission_data": bool(emissions_kg is not None),
                    "has_popularity_data": False,
                    "has_seasonality_data": False,
                    "has_feasibility_data": False,
                },
                "estimated_emissions_kg": emissions_kg,
                "recommended_transport": rec_mode,
                "travel_hours": travel_hours,
                "explanation": self._generate_explanation(
                    row, user_interests, "baseline"
                ),
                "data_quality_notes": ["Baseline mode: only preference relevance used for ranking"],
                "weights_used": {"preference": 1.0, "emissions": 0, "popularity": 0, "seasonality": 0, "feasibility": 0},
                "configuration": "C1_baseline",
            })
        
        return results
    
    def recommend_multicriteria(
        self,
        user_interests: List[str],
        origin_city: str,
        travel_month: int,
        sustainability_priority: float = 0.5,
        preferred_transport: Optional[str] = None,
        max_travel_hours: Optional[float] = None,
        budget_level: str = "medium",
        top_k: int = DEFAULT_TOP_K,
        configuration: str = "C5_full",
    ) -> List[Dict]:
        """
        Multi-criteria recommender with sustainability scoring.
        
        Supports configurations C2–C5 via the 'configuration' parameter.
        """
        df = self.attractions_df.copy()
        
        # Get origin coordinates
        origin = ORIGIN_CITIES.get(origin_city)
        if not origin:
            raise ValueError(f"Unknown origin city: {origin_city}")
        
        origin_lat, origin_lon = origin["lat"], origin["lon"]
        
        # Determine weights based on configuration and user priority
        weights = self._get_weights_for_config(configuration, sustainability_priority)
        
        # ── 1. Preference Scores ──
        df["preference_score"] = df["categories"].apply(
            lambda cats: compute_preference_score(cats, user_interests)
        )
        
        # ── 2. Emission Scores ──
        if weights.get("emissions", 0) > 0:
            emission_details = []
            for _, row in df.iterrows():
                details = compute_emission_score(
                    origin_lat, origin_lon,
                    row["latitude"], row["longitude"],
                    transport_mode=preferred_transport,
                )
                emission_details.append(details)
            
            df["emission_details"] = emission_details
            
            # Extract emissions for the recommended (or preferred) mode
            def get_best_emissions(details):
                if not details:
                    return None
                mode = preferred_transport or details.get("recommended_mode")
                if mode and mode in details:
                    return details[mode]["emissions_kg"]
                return None
            
            df["emissions_kg"] = df["emission_details"].apply(get_best_emissions)
            
            # Normalise emission scores (lower = better → inverted)
            valid_emissions = df["emissions_kg"].dropna().tolist()
            if valid_emissions:
                all_emissions = df["emissions_kg"].fillna(df["emissions_kg"].median()).tolist()
                df["emission_score"] = normalise_emission_scores(all_emissions)
            else:
                df["emission_score"] = MISSING_SCORE_DEFAULT
        else:
            df["emission_score"] = MISSING_SCORE_DEFAULT
            df["emission_details"] = [{}] * len(df)
            df["emissions_kg"] = None
        
        # ── 3. Popularity Scores ──
        if weights.get("popularity", 0) > 0:
            all_visitors = df["annual_visitors"].tolist() if "annual_visitors" in df.columns else []
            df["popularity_score"] = df.apply(
                lambda row: compute_popularity_score(
                    row.get("annual_visitors"),
                    all_visitors,
                ),
                axis=1,
            )
        else:
            df["popularity_score"] = MISSING_SCORE_DEFAULT
        
        # ── 4. Seasonality Scores ──
        if weights.get("seasonality", 0) > 0:
            df["seasonality_score"] = df.apply(
                lambda row: compute_seasonality_score(travel_month, row.to_dict()),
                axis=1,
            )
        else:
            df["seasonality_score"] = MISSING_SCORE_DEFAULT
        
        # ── 5. Feasibility Scores ──
        if weights.get("feasibility", 0) > 0:
            def calc_feasibility(row):
                details = row.get("emission_details", {})
                mode = preferred_transport or details.get("recommended_mode")
                if mode and mode in details:
                    return compute_feasibility_score(
                        details[mode].get("travel_hours"),
                        details[mode].get("estimated_cost_inr"),
                        max_travel_hours=max_travel_hours,
                        budget_level=budget_level,
                    )
                return MISSING_SCORE_DEFAULT
            
            df["feasibility_score"] = df.apply(calc_feasibility, axis=1)
        else:
            df["feasibility_score"] = MISSING_SCORE_DEFAULT
        
        # ── 6. Composite Score ──
        df["final_score"] = df.apply(
            lambda row: compute_composite_score(
                row["preference_score"],
                row["emission_score"],
                row["popularity_score"],
                row["seasonality_score"],
                row["feasibility_score"],
                weights=weights,
            ),
            axis=1,
        )
        
        # Sort by final score (descending)
        df = df.sort_values("final_score", ascending=False)
        
        # Filter out infeasible (score 0) if using feasibility
        if max_travel_hours:
            df = df[df["feasibility_score"] > 0]
        
        # Build results
        results = []
        for _, row in df.head(top_k).iterrows():
            details = row.get("emission_details", {})
            mode = preferred_transport or details.get("recommended_mode")
            mode_details = details.get(mode, {}) if mode else {}
            
            result = {
                "rank": len(results) + 1,
                "attraction": self._attraction_to_dict(row),
                "final_score": round(row["final_score"], 4),
                "score_breakdown": {
                    "preference_score": round(row["preference_score"], 4),
                    "emission_score": round(row["emission_score"], 4),
                    "popularity_score": round(row["popularity_score"], 4),
                    "seasonality_score": round(row["seasonality_score"], 4),
                    "feasibility_score": round(row["feasibility_score"], 4),
                    "has_emission_data": row["emissions_kg"] is not None and not pd.isna(row.get("emissions_kg")),
                    "has_popularity_data": row.get("annual_visitors") is not None,
                    "has_seasonality_data": True,
                    "has_feasibility_data": bool(mode_details),
                },
                "transport_mode": mode,
                "distance_km": mode_details.get("distance_km"),
                "travel_hours": mode_details.get("travel_hours"),
                "estimated_emissions_kg": mode_details.get("emissions_kg"),
                "estimated_cost_inr": mode_details.get("estimated_cost_inr"),
                "explanation": self._generate_explanation(
                    row, user_interests, configuration, weights, mode
                ),
                "data_quality_notes": self._generate_quality_notes(row),
                "weights_used": weights,
                "configuration": configuration,
            }
            results.append(result)
        
        return results
    
    def compare_configurations(
        self,
        user_interests: List[str],
        origin_city: str,
        travel_month: int,
        sustainability_priority: float = 0.5,
        preferred_transport: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> Dict[str, List[Dict]]:
        """
        Run all configurations and return results for comparison.
        """
        results = {}
        
        # C1: Baseline
        results["C1_baseline"] = self.recommend_baseline(
            user_interests=user_interests,
            origin_city=origin_city,
            preferred_transport=preferred_transport,
            top_k=top_k,
        )
        
        # C2–C5: Multi-criteria with different component sets
        configs = {
            "C2_pref_emissions": {"preference": 0.6, "emissions": 0.4, "popularity": 0, "seasonality": 0, "feasibility": 0},
            "C3_pref_emis_pop": {"preference": 0.5, "emissions": 0.25, "popularity": 0.25, "seasonality": 0, "feasibility": 0},
            "C4_pref_emis_pop_seas": {"preference": 0.4, "emissions": 0.2, "popularity": 0.2, "seasonality": 0.2, "feasibility": 0},
            "C5_full": None,  # Uses sustainability_priority
        }
        
        for config_name, weights in configs.items():
            try:
                if weights:
                    # Override weights for specific configs
                    result = self.recommend_multicriteria(
                        user_interests=user_interests,
                        origin_city=origin_city,
                        travel_month=travel_month,
                        sustainability_priority=sustainability_priority,
                        preferred_transport=preferred_transport,
                        top_k=top_k,
                        configuration=config_name,
                    )
                else:
                    result = self.recommend_multicriteria(
                        user_interests=user_interests,
                        origin_city=origin_city,
                        travel_month=travel_month,
                        sustainability_priority=sustainability_priority,
                        preferred_transport=preferred_transport,
                        top_k=top_k,
                        configuration=config_name,
                    )
                results[config_name] = result
            except Exception as e:
                logger.error(f"Error in config {config_name}: {e}")
                results[config_name] = []
        
        return results
    
    def _get_weights_for_config(
        self, configuration: str, sustainability_priority: float
    ) -> Dict[str, float]:
        """Get weights based on experimental configuration."""
        config_weights = {
            "C1_baseline": {"preference": 1.0, "emissions": 0, "popularity": 0, "seasonality": 0, "feasibility": 0},
            "C2_pref_emissions": {"preference": 0.6, "emissions": 0.4, "popularity": 0, "seasonality": 0, "feasibility": 0},
            "C3_pref_emis_pop": {"preference": 0.5, "emissions": 0.25, "popularity": 0.25, "seasonality": 0, "feasibility": 0},
            "C4_pref_emis_pop_seas": {"preference": 0.4, "emissions": 0.2, "popularity": 0.2, "seasonality": 0.2, "feasibility": 0},
        }
        
        if configuration in config_weights:
            return config_weights[configuration]
        
        # C5 or custom: use sustainability priority to adjust weights
        return adjust_weights_for_priority(sustainability_priority)
    
    def _clean_val(self, val):
        if val is None:
            return None
        if isinstance(val, (list, tuple, dict, set)):
            return val
        try:
            if pd.isna(val):
                return None
        except (ValueError, TypeError):
            pass
        return val

    def _attraction_to_dict(self, row) -> Dict:
        """Convert a DataFrame row to an attraction dict, ensuring no NaN values leak into JSON."""
        return {
            "id": str(row["id"]),
            "name": str(row["name"]),
            "description": self._clean_val(row.get("description")),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "city": str(row["city"]),
            "district": self._clean_val(row.get("district")) or str(row["city"]),
            "categories": row["categories"] if isinstance(row["categories"], list) else [],
            "heritage_status": self._clean_val(row.get("heritage_status")),
            "estimated_visit_duration_hours": float(row["estimated_visit_duration_hours"]) if not pd.isna(row.get("estimated_visit_duration_hours", np.nan)) else None,
            "entry_fee": self._clean_val(row.get("entry_fee")),
            "annual_visitors": int(row["annual_visitors"]) if not pd.isna(row.get("annual_visitors", np.nan)) else None,
            "visitor_data_source": self._clean_val(row.get("visitor_data_source")),
        }
    
    def _generate_explanation(
        self, row, user_interests, configuration, weights=None, transport_mode=None
    ) -> str:
        """
        Generate a template-based explanation for why this destination was recommended.
        
        No LLM needed — uses deterministic templates.
        """
        name = row["name"]
        cats = row["categories"] if isinstance(row["categories"], list) else []
        matched = set(cats) & set(user_interests)
        
        parts = []
        
        # Preference match
        if matched:
            parts.append(f"{name} matches your interest in {', '.join(sorted(matched))}")
        else:
            parts.append(f"{name} is a notable attraction in {row['city']}")
        
        if configuration == "baseline":
            return ". ".join(parts) + "."
        
        # Emission info
        if weights and weights.get("emissions", 0) > 0:
            emission_score = row.get("emission_score", MISSING_SCORE_DEFAULT)
            if emission_score > 0.7:
                parts.append("with relatively low estimated travel emissions")
            elif emission_score < 0.3:
                parts.append("though travel emissions are relatively high")
        
        # Popularity
        if weights and weights.get("popularity", 0) > 0:
            pop_score = row.get("popularity_score", MISSING_SCORE_DEFAULT)
            if pop_score > 0.7:
                parts.append("and has a moderate visitor volume (not overcrowded)")
            elif pop_score < 0.3:
                parts.append("though it's a very popular (potentially crowded) destination")
        
        # Seasonality
        if weights and weights.get("seasonality", 0) > 0:
            seas_score = row.get("seasonality_score", MISSING_SCORE_DEFAULT)
            if seas_score > 0.7:
                parts.append("This is an off-peak travel period, which is ideal")
            elif seas_score < 0.3:
                parts.append("Note: this is peak tourist season, expect higher crowds")
        
        return ". ".join(parts) + "."
    
    def _generate_quality_notes(self, row) -> List[str]:
        """Generate data quality transparency notes."""
        notes = []
        
        if pd.isna(row.get("annual_visitors", np.nan)):
            notes.append("Popularity: no visitor count data available; using neutral score")
        else:
            src = row.get("visitor_data_source", "unknown")
            notes.append(f"Popularity: visitor count is {src}")
        
        if row.get("emission_details"):
            notes.append("Emissions: estimated using national average factors (WRI India)")
        
        notes.append("Seasonality: based on heuristic demand index, not observed monthly counts")
        
        if pd.isna(row.get("estimated_visit_duration_hours", np.nan)):
            notes.append("Visit duration: not available")
        
        return notes
    
    def get_all_destinations(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Return all destinations, optionally filtered."""
        df = self.attractions_df.copy()
        
        if filters:
            if "city" in filters:
                df = df[df["city"].str.lower() == filters["city"].lower()]
            if "category" in filters:
                df = df[df["categories"].apply(lambda cats: filters["category"] in cats)]
        
        return [self._attraction_to_dict(row) for _, row in df.iterrows()]
