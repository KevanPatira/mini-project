"""
Evaluation Runner Module.

Executes reproducible experiments defined in EXPERIMENT_PLAN.md:
- Runs Configurations C1 through C5
- Evaluates across Personas P1 through P7
- Computes comprehensive evaluation metrics (CMR@10, TEE, Diversity, Gini, Geographic Spread)
- Runs sensitivity sweep over sustainability weight lambda in [0.0, 1.0]
- Exports results to JSON and CSV
"""

import json
import os
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

from app.recommendation.engine import RecommendationEngine
from app.evaluation.metrics import (
    compute_cmr_at_k,
    compute_category_diversity_at_k,
    compute_total_emissions,
    compute_gini_coefficient,
    compute_geographic_spread,
    compute_unique_districts,
    compute_jaccard_overlap,
    compute_kendall_tau,
    compute_catalog_coverage,
)

logger = logging.getLogger(__name__)

# Standard user personas from EXPERIMENT_PLAN.md
EVALUATION_PERSONAS = [
    {
        "id": "P1",
        "name": "Heritage Explorer",
        "origin": "delhi",
        "interests": ["history", "architecture", "culture"],
        "budget": "medium",
        "duration_days": 5,
        "sustainability_priority": 0.5,
        "travel_month": 11,
    },
    {
        "id": "P2",
        "name": "Nature Enthusiast",
        "origin": "mumbai",
        "interests": ["nature", "wildlife", "adventure"],
        "budget": "high",
        "duration_days": 7,
        "sustainability_priority": 0.8,
        "travel_month": 12,
    },
    {
        "id": "P3",
        "name": "Budget Backpacker",
        "origin": "bangalore",
        "interests": ["history", "culture", "nature", "food"],
        "budget": "low",
        "duration_days": 10,
        "sustainability_priority": 0.2,
        "travel_month": 1,
    },
    {
        "id": "P4",
        "name": "Cultural Foodie",
        "origin": "kolkata",
        "interests": ["food", "culture", "shopping", "history"],
        "budget": "medium",
        "duration_days": 4,
        "sustainability_priority": 0.5,
        "travel_month": 10,
    },
    {
        "id": "P5",
        "name": "Eco-conscious Traveller",
        "origin": "chennai",
        "interests": ["nature", "history", "culture"],
        "budget": "medium",
        "duration_days": 6,
        "sustainability_priority": 0.95,
        "travel_month": 2,
    },
    {
        "id": "P6",
        "name": "Weekend Tripper",
        "origin": "jaipur",
        "interests": ["history", "culture", "relaxation"],
        "budget": "low",
        "duration_days": 2,
        "sustainability_priority": 0.3,
        "travel_month": 3,
    },
    {
        "id": "P7",
        "name": "Family Vacationer",
        "origin": "delhi",
        "interests": ["nature", "history", "wildlife", "culture"],
        "budget": "high",
        "duration_days": 5,
        "sustainability_priority": 0.5,
        "travel_month": 12,
    },
]


class ExperimentRunner:
    """Orchestrates research experiments and metric compilation."""

    def __init__(self, engine: Optional[RecommendationEngine] = None):
        self.engine = engine or RecommendationEngine()
        self.results_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "results")
        )
        os.makedirs(self.results_dir, exist_ok=True)

    def run_all_experiments(self) -> Dict[str, Any]:
        """Run full test matrix: all personas x all 5 configurations + ablation + sensitivity sweep."""
        matrix_results = []
        detailed_comparisons = {}
        config_recs_map: Dict[str, List[List[Dict]]] = {
            "C1_baseline": [],
            "C2_pref_emissions": [],
            "C3_pref_emis_pop": [],
            "C4_pref_emis_pop_seas": [],
            "C5_full": [],
        }

        for persona in EVALUATION_PERSONAS:
            p_id = persona["id"]
            comparisons = self.engine.compare_configurations(
                user_interests=persona["interests"],
                origin_city=persona["origin"],
                travel_month=persona["travel_month"],
                sustainability_priority=persona["sustainability_priority"],
                top_k=10,
            )
            detailed_comparisons[p_id] = comparisons

            # Compute metrics for each configuration
            for config_id, recs in comparisons.items():
                if config_id in config_recs_map:
                    config_recs_map[config_id].append(recs)

                cmr = compute_cmr_at_k(recs, persona["interests"])
                cd = compute_category_diversity_at_k(recs)
                emissions = compute_total_emissions(recs)
                spread = compute_geographic_spread(recs)
                districts = compute_unique_districts(recs)

                # Popularities for Gini (using proxy fallback for unlisted items)
                pop_vals = [
                    (r["attraction"].get("annual_visitors") or 300000) for r in recs
                ]
                gini = compute_gini_coefficient(pop_vals)

                # Preference scores
                pref_scores = [r["score_breakdown"]["preference_score"] for r in recs]
                avg_pref = round(sum(pref_scores) / len(pref_scores), 4) if pref_scores else 0.0

                # Sustainability / emission scores
                emis_scores = [r["score_breakdown"]["emission_score"] for r in recs]
                avg_emis = round(sum(emis_scores) / len(emis_scores), 4) if emis_scores else 0.0

                matrix_results.append({
                    "persona_id": p_id,
                    "persona_name": persona["name"],
                    "origin": persona["origin"],
                    "config_id": config_id,
                    "cmr_at_10": cmr,
                    "category_diversity": cd,
                    "total_emissions_kg": emissions,
                    "avg_preference_score": avg_pref,
                    "avg_emission_score": avg_emis,
                    "popularity_gini": gini,
                    "geographic_spread_km": spread,
                    "unique_districts": districts,
                    "top_attraction": recs[0]["attraction"]["name"] if recs else None,
                })

        # Run sensitivity analysis for Persona P1 across lambda in [0.0, 1.0]
        sensitivity = self.run_sensitivity_sweep(
            origin="delhi",
            interests=["history", "architecture", "culture"],
            month=11,
        )

        # Aggregate summary across configurations
        summary_df = pd.DataFrame(matrix_results)
        config_summary_df = (
            summary_df.groupby("config_id")
            .agg({
                "cmr_at_10": "mean",
                "category_diversity": "mean",
                "total_emissions_kg": "mean",
                "avg_preference_score": "mean",
                "avg_emission_score": "mean",
                "popularity_gini": "mean",
                "geographic_spread_km": "mean",
                "unique_districts": "mean",
            })
            .round(3)
        )

        # Calculate catalog coverage for each configuration
        catalog_coverage = {}
        for cfg_id, rec_lists in config_recs_map.items():
            catalog_coverage[cfg_id] = compute_catalog_coverage(rec_lists, total_catalog_size=45)
        config_summary_df["catalog_coverage"] = pd.Series(catalog_coverage)

        config_summary = config_summary_df.to_dict(orient="index")

        # Build formal ablation summary
        ablation_summary = []
        c1_emiss = config_summary.get("C1_baseline", {}).get("total_emissions_kg", 0.0)
        c1_pref = config_summary.get("C1_baseline", {}).get("avg_preference_score", 0.0)
        c1_gini = config_summary.get("C1_baseline", {}).get("popularity_gini", 0.0)

        for cfg_key in ["C1_baseline", "C2_pref_emissions", "C3_pref_emis_pop", "C4_pref_emis_pop_seas", "C5_full"]:
            row = config_summary.get(cfg_key, {})
            emiss = row.get("total_emissions_kg", 0.0)
            pref = row.get("avg_preference_score", 0.0)
            gini = row.get("popularity_gini", 0.0)
            
            emiss_reduction = round((1.0 - (emiss / c1_emiss)) * 100, 2) if c1_emiss > 0 else 0.0
            pref_retained = round((pref / c1_pref) * 100, 2) if c1_pref > 0 else 100.0

            ablation_summary.append({
                "configuration": cfg_key,
                "total_emissions_kg": emiss,
                "emissions_reduction_pct_vs_c1": emiss_reduction,
                "avg_preference_score": pref,
                "preference_retention_pct_vs_c1": pref_retained,
                "popularity_gini": gini,
                "category_diversity": row.get("category_diversity", 0.0),
                "geographic_spread_km": row.get("geographic_spread_km", 0.0),
                "catalog_coverage": row.get("catalog_coverage", 0.0),
            })

        ablation_df = pd.DataFrame(ablation_summary)

        full_output = {
            "matrix_results": matrix_results,
            "config_summary": config_summary,
            "ablation_summary": ablation_summary,
            "sensitivity_sweep": sensitivity,
            "personas": EVALUATION_PERSONAS,
            "metadata": {
                "total_catalog_size": 45,
                "origin_coverage": ["delhi", "mumbai", "bangalore", "kolkata", "chennai", "jaipur"],
                "data_provenance": "Observed coordinates (OSM/Wikidata) + Heuristic/Estimated proxy metrics",
                "visitor_counts_status": "9 observed/estimated, 36 median-imputed proxy",
            }
        }

        # Save to disk
        json_path = os.path.join(self.results_dir, "experiment_results.json")
        csv_path = os.path.join(self.results_dir, "matrix_results.csv")
        summary_csv_path = os.path.join(self.results_dir, "config_summary.csv")
        ablation_csv_path = os.path.join(self.results_dir, "ablation_summary.csv")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(full_output, f, indent=2)

        summary_df.to_csv(csv_path, index=False)
        config_summary_df.to_csv(summary_csv_path)
        ablation_df.to_csv(ablation_csv_path, index=False)

        logger.info(f"Saved evaluation results to {json_path}")
        return full_output

    def run_sensitivity_sweep(
        self,
        origin: str = "delhi",
        interests: List[str] = None,
        month: int = 11,
        steps: int = 11,
    ) -> List[Dict]:
        """Sweep sustainability priority lambda from 0.0 to 1.0 across full multi-metric spectrum."""
        interests = interests or ["history", "architecture", "culture"]
        sweep_results = []

        # Get C1 baseline with origin city for emissions comparison
        base_recs = self.engine.recommend_baseline(
            user_interests=interests,
            origin_city=origin,
            top_k=10,
        )
        baseline_ids = [r["attraction"]["id"] for r in base_recs]

        for step in range(steps):
            sp = round(step / (steps - 1), 2)
            recs = self.engine.recommend_multicriteria(
                user_interests=interests,
                origin_city=origin,
                travel_month=month,
                sustainability_priority=sp,
                top_k=10,
            )
            top_ids = [r["attraction"]["id"] for r in recs]
            emissions = compute_total_emissions(recs)
            cmr = compute_cmr_at_k(recs, interests)
            diversity = compute_category_diversity_at_k(recs)
            spread = compute_geographic_spread(recs)
            jaccard = compute_jaccard_overlap(baseline_ids, top_ids)
            tau = compute_kendall_tau(baseline_ids, top_ids)

            pop_vals = [(r["attraction"].get("annual_visitors") or 300000) for r in recs]
            gini = compute_gini_coefficient(pop_vals)

            pref_scores = [r["score_breakdown"]["preference_score"] for r in recs]
            avg_pref = round(sum(pref_scores) / len(pref_scores), 4) if pref_scores else 0.0

            sweep_results.append({
                "sustainability_priority": sp,
                "total_emissions_kg": emissions,
                "category_match_rate": cmr,
                "category_diversity": diversity,
                "geographic_spread_km": spread,
                "popularity_gini": gini,
                "avg_preference_score": avg_pref,
                "jaccard_overlap_with_baseline": jaccard,
                "kendall_tau": tau,
                "top_10_names": [r["attraction"]["name"] for r in recs],
            })

        return sweep_results
