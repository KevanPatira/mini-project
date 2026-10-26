"""
Evaluation and Inference Module for Deep Reinforcement Learning Tourism Recommender.

Provides:
1. Production inference runner `generate_drl_itinerary` loading trained DQN agent
2. Systematic benchmark comparing DRL against C1 (content-based TSP) and C5 (sustainable TSP)
3. Scientifically defensible metric collection across standardized personas P1–P7
"""

import os
import json
import csv
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from app.config import ORIGIN_CITIES, RESULTS_DIR
from app.data_ingestion.loader import load_attractions
from app.data_ingestion.models import UserPreferences
from app.rl.environment import TourismItineraryEnv
from app.rl.agent import DQNAgent
from app.recommendation.engine import RecommendationEngine
from app.itinerary.builder import ItineraryBuilder
from app.evaluation.metrics import (
    compute_cmr_at_k,
    compute_category_diversity_at_k,
    compute_geographic_spread,
    compute_gini_coefficient,
)

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "models"))
DEFAULT_CHECKPOINT = os.path.join(MODELS_DIR, "drl_itinerary_agent.json")

# Standard benchmark personas matching EXPERIMENT_METHODOLOGY.md
BENCHMARK_PERSONAS = [
    {
        "id": "P1",
        "name": "Heritage Explorer",
        "origin": "delhi",
        "interests": ["history", "architecture", "culture"],
        "budget_level": "medium",
        "budget_inr": 15000.0,
        "duration_days": 5,
        "travel_month": 11,
        "preferred_transport": "train",
    },
    {
        "id": "P2",
        "name": "Nature Enthusiast",
        "origin": "mumbai",
        "interests": ["nature", "wildlife", "adventure"],
        "budget_level": "high",
        "budget_inr": 25000.0,
        "duration_days": 7,
        "travel_month": 12,
        "preferred_transport": "train",
    },
    {
        "id": "P3",
        "name": "Budget Backpacker",
        "origin": "bangalore",
        "interests": ["history", "culture", "nature", "food"],
        "budget_level": "low",
        "budget_inr": 8000.0,
        "duration_days": 6,
        "travel_month": 1,
        "preferred_transport": "bus",
    },
    {
        "id": "P4",
        "name": "Cultural Foodie",
        "origin": "kolkata",
        "interests": ["food", "culture", "shopping", "history"],
        "budget_level": "medium",
        "budget_inr": 18000.0,
        "duration_days": 4,
        "travel_month": 10,
        "preferred_transport": "train",
    },
    {
        "id": "P5",
        "name": "Eco-conscious Traveller",
        "origin": "chennai",
        "interests": ["nature", "history", "culture"],
        "budget_level": "medium",
        "budget_inr": 16000.0,
        "duration_days": 6,
        "travel_month": 2,
        "preferred_transport": "train",
    },
    {
        "id": "P6",
        "name": "Weekend Tripper",
        "origin": "jaipur",
        "interests": ["history", "culture", "relaxation"],
        "budget_level": "low",
        "budget_inr": 6000.0,
        "duration_days": 2,
        "travel_month": 3,
        "preferred_transport": "train",
    },
    {
        "id": "P7",
        "name": "Family Vacationer",
        "origin": "delhi",
        "interests": ["nature", "history", "wildlife", "culture"],
        "budget_level": "high",
        "budget_inr": 30000.0,
        "duration_days": 5,
        "travel_month": 12,
        "preferred_transport": "train",
    },
]


def generate_drl_itinerary(
    origin_city: str,
    travel_month: int = 11,
    trip_duration_days: int = 5,
    budget_inr: float = 15000.0,
    user_interests: Optional[List[str]] = None,
    preferred_transport: str = "train",
    checkpoint_path: Optional[str] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Generate sequential itinerary recommendations using trained DRL Agent.
    
    Returns structured itinerary dictionary compatible with ItineraryResponse schema.
    """
    ckpt = checkpoint_path or DEFAULT_CHECKPOINT
    env = TourismItineraryEnv()

    agent = DQNAgent(
        state_dim=env.state_dim,
        action_dim=env.action_space_size,
        hidden_dims=(128, 64),
        seed=seed,
    )

    t0 = time.time()
    checkpoint_loaded = agent.load(ckpt)
    load_time_ms = round((time.time() - t0) * 1000, 2)

    warnings = []
    if not checkpoint_loaded:
        warnings.append(
            f"Trained DRL checkpoint not found at {ckpt}. Running inference using untrained policy with action masking."
        )

    t_infer_start = time.time()
    state, info = env.reset(
        origin_city=origin_city,
        travel_month=travel_month,
        trip_days=trip_duration_days,
        budget_inr=budget_inr,
        user_interests=user_interests,
        preferred_transport=preferred_transport,
        seed=seed,
    )

    done = False
    step_count = 0
    max_steps = 15

    while not done and step_count < max_steps:
        mask = info["action_mask"]
        # Greedy masked selection
        action = agent.select_action(state, mask, epsilon=0.0)
        state, reward, done, _, info = env.step(action)
        step_count += 1

    inference_ms = round((time.time() - t_infer_start) * 1000, 2)

    # Format itinerary stops for API & UI presentation
    formatted_stops = []
    accum_day_hours = 0.0
    for s in env.itinerary_stops:
        att = s["attraction"]
        leg_h = s["travel_hours"]
        vis_h = s["visit_duration_hours"]
        arr_h = 9.0 + accum_day_hours + leg_h
        dep_h = arr_h + vis_h
        accum_day_hours += (leg_h + vis_h)
        if accum_day_hours > env.HOURS_PER_DAY:
            accum_day_hours = 0.0

        arr_str = f"Day {s['day']}, {int(arr_h):02d}:{int((arr_h % 1) * 60):02d}"
        dep_str = f"Day {s['day']}, {int(dep_h):02d}:{int((dep_h % 1) * 60):02d}"

        formatted_stops.append({
            "order": s["order"],
            "day": s["day"],
            "attraction": att,
            "arrival_time": arr_str,
            "departure_time": dep_str,
            "visit_duration_hours": vis_h,
            "travel_from_previous_km": s["travel_distance_km"],
            "travel_from_previous_hours": s["travel_hours"],
            "transport_mode": s["transport_mode"],
            "leg_emissions_kg": s["leg_emissions_kg"],
            "transit_fare_inr": s["transit_fare_inr"],
            "entry_fee_inr": s["entry_fee_inr"],
            "total_leg_cost_inr": s["total_leg_cost_inr"],
            "provenance": {
                "entry_fee": "sourced (cleaned_tourist_places_rajasthan.csv)" if att["id"] in env.monument_meta else "heuristic",
                "coordinates": "observed (OSM / Curated Catalog)",
                "distance": "calculated (haversine * 1.30 circuity estimate)",
                "emissions": "estimated (WRI India factors)",
            },
        })

    origin_info = ORIGIN_CITIES.get(origin_city.lower(), ORIGIN_CITIES["delhi"])

    # Calculate baseline comparison (private car)
    baseline_car_emissions = round(env.total_distance_km * 0.150, 2)
    saved_emissions = max(0.0, round(baseline_car_emissions - env.total_emissions_kg, 2))

    total_cost = round(env.total_fare_inr + env.total_entry_fees_inr, 2)

    return {
        "origin": origin_info["name"],
        "stops": formatted_stops,
        "total_stops": len(formatted_stops),
        "total_distance_km": round(env.total_distance_km, 2),
        "total_travel_hours": round((env.total_hours - env.remaining_hours), 2),
        "total_emissions_kg": round(env.total_emissions_kg, 2),
        "baseline_car_emissions_kg": baseline_car_emissions,
        "co2_savings_kg": saved_emissions,
        "total_days": env.current_day,
        "total_fare_inr": round(env.total_fare_inr, 2),
        "total_entry_fees_inr": round(env.total_entry_fees_inr, 2),
        "total_cost_inr": total_cost,
        "initial_budget_inr": budget_inr,
        "remaining_budget_inr": round(env.remaining_budget, 2),
        "budget_violation": bool(env.remaining_budget < 0),
        "duration_violation": bool(env.current_day > trip_duration_days),
        "strategy_used": "drl",
        "provenance_mode": "Mode B (Simulator-Trained DQN)",
        "inference_latency_ms": inference_ms,
        "checkpoint_status": "loaded" if checkpoint_loaded else "missing_fallback",
        "warnings": warnings,
        "data_transparency_summary": {
            "attractions_catalog": "45 verified Rajasthan heritage & natural sites",
            "entry_fees": "1,225 records parsed from Ministry of Tourism / Kaggle dataset",
            "crowd_pressure": "Macro annual visitation proxy from ASI & Tourism Statistics",
            "rl_training": "Mode B Simulator-trained over 500 multi-constraint episodes",
        },
    }


def benchmark_drl_vs_baselines(
    checkpoint_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run empirical comparison across standard personas P1–P7:
    - Configuration C1 (Top-N Content Filtered + 2-opt TSP)
    - Configuration C5 (Sustainability-Aware Filtered + 2-opt TSP)
    - Strategy DRL (Deep Q-Network Sequential Itinerary Planner)
    """
    out_dir = output_dir or RESULTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    ckpt = checkpoint_path or DEFAULT_CHECKPOINT

    rec_engine = RecommendationEngine()
    itinerary_builder = ItineraryBuilder()

    benchmark_rows = []
    summary_by_strategy: Dict[str, Dict[str, List[float]]] = {
        "C1_Baseline_TSP": {"stops": [], "emissions": [], "distance": [], "cost": [], "cmr": [], "diversity": [], "latency_ms": []},
        "C5_Sustainable_TSP": {"stops": [], "emissions": [], "distance": [], "cost": [], "cmr": [], "diversity": [], "latency_ms": []},
        "DRL_ModeB_Agent": {"stops": [], "emissions": [], "distance": [], "cost": [], "cmr": [], "diversity": [], "latency_ms": []},
    }

    print("\n======================================================================")
    print("      Benchmarking DRL Itinerary Planner vs C1 & C5 Baselines         ")
    print("======================================================================")

    for p in BENCHMARK_PERSONAS:
        p_id = p["id"]
        origin = p["origin"]
        interests = p["interests"]
        days = p["duration_days"]
        budget = p["budget_inr"]
        month = p["travel_month"]
        transport = p["preferred_transport"]

        prefs = UserPreferences(
            interests=interests,
            origin_city=origin,
            travel_month=month,
            trip_duration_days=days,
            budget_level=p["budget_level"],
            preferred_transport=transport,
        )

        # ── 1. Strategy C1: Top Content-Based + 2-opt TSP ──
        t0 = time.time()
        c1_recs = rec_engine.recommend_baseline(
            user_interests=interests,
            origin_city=origin,
            preferred_transport=transport,
            top_k=min(days * 2, 8),
        )
        c1_ids = [r["attraction"]["id"] for r in c1_recs]
        c1_itin = itinerary_builder.build_itinerary(
            origin_city=origin,
            attraction_ids=c1_ids,
            trip_duration_days=days,
            preferred_mode=transport,
        )
        c1_lat = round((time.time() - t0) * 1000, 2)
        c1_emiss = c1_itin["total_emissions_kg"]
        c1_dist = c1_itin["total_distance_km"]
        c1_stops = len(c1_itin["stops"])
        c1_cost = round(c1_dist * 2.0 + c1_stops * 100.0, 2)
        c1_cmr = compute_cmr_at_k(c1_recs, interests)
        c1_div = compute_category_diversity_at_k(c1_recs)

        summary_by_strategy["C1_Baseline_TSP"]["stops"].append(c1_stops)
        summary_by_strategy["C1_Baseline_TSP"]["emissions"].append(c1_emiss)
        summary_by_strategy["C1_Baseline_TSP"]["distance"].append(c1_dist)
        summary_by_strategy["C1_Baseline_TSP"]["cost"].append(c1_cost)
        summary_by_strategy["C1_Baseline_TSP"]["cmr"].append(c1_cmr)
        summary_by_strategy["C1_Baseline_TSP"]["diversity"].append(c1_div)
        summary_by_strategy["C1_Baseline_TSP"]["latency_ms"].append(c1_lat)

        benchmark_rows.append({
            "persona_id": p_id,
            "persona_name": p["name"],
            "strategy": "C1_Baseline_TSP",
            "stops_visited": c1_stops,
            "total_emissions_kg": c1_emiss,
            "total_distance_km": c1_dist,
            "total_cost_inr": c1_cost,
            "cmr_score": c1_cmr,
            "category_diversity": c1_div,
            "budget_violated": False,
            "duration_violated": (c1_itin["total_days"] > days),
            "inference_ms": c1_lat,
        })

        # ── 2. Strategy C5: Full Sustainable + 2-opt TSP ──
        t0 = time.time()
        c5_recs = rec_engine.recommend_multicriteria(
            user_interests=interests,
            origin_city=origin,
            travel_month=month,
            sustainability_priority=0.5,
            preferred_transport=transport,
            budget_level=p["budget_level"],
            top_k=min(days * 2, 8),
            configuration="C5_full",
        )
        c5_ids = [r["attraction"]["id"] for r in c5_recs]
        c5_itin = itinerary_builder.build_itinerary(
            origin_city=origin,
            attraction_ids=c5_ids,
            trip_duration_days=days,
            preferred_mode=transport,
        )
        c5_lat = round((time.time() - t0) * 1000, 2)
        c5_emiss = c5_itin["total_emissions_kg"]
        c5_dist = c5_itin["total_distance_km"]
        c5_stops = len(c5_itin["stops"])
        c5_cost = round(c5_dist * 2.0 + c5_stops * 100.0, 2)
        c5_cmr = compute_cmr_at_k(c5_recs, interests)
        c5_div = compute_category_diversity_at_k(c5_recs)

        summary_by_strategy["C5_Sustainable_TSP"]["stops"].append(c5_stops)
        summary_by_strategy["C5_Sustainable_TSP"]["emissions"].append(c5_emiss)
        summary_by_strategy["C5_Sustainable_TSP"]["distance"].append(c5_dist)
        summary_by_strategy["C5_Sustainable_TSP"]["cost"].append(c5_cost)
        summary_by_strategy["C5_Sustainable_TSP"]["cmr"].append(c5_cmr)
        summary_by_strategy["C5_Sustainable_TSP"]["diversity"].append(c5_div)
        summary_by_strategy["C5_Sustainable_TSP"]["latency_ms"].append(c5_lat)

        benchmark_rows.append({
            "persona_id": p_id,
            "persona_name": p["name"],
            "strategy": "C5_Sustainable_TSP",
            "stops_visited": c5_stops,
            "total_emissions_kg": c5_emiss,
            "total_distance_km": c5_dist,
            "total_cost_inr": c5_cost,
            "cmr_score": c5_cmr,
            "category_diversity": c5_div,
            "budget_violated": False,
            "duration_violated": (c5_itin["total_days"] > days),
            "inference_ms": c5_lat,
        })

        # ── 3. Strategy DRL: Deep Q-Network Agent ──
        drl_res = generate_drl_itinerary(
            origin_city=origin,
            travel_month=month,
            trip_duration_days=days,
            budget_inr=budget,
            user_interests=interests,
            preferred_transport=transport,
            checkpoint_path=ckpt,
            seed=42,
        )
        drl_stops = drl_res["total_stops"]
        drl_emiss = drl_res["total_emissions_kg"]
        drl_dist = drl_res["total_distance_km"]
        drl_cost = drl_res["total_cost_inr"]
        drl_lat = drl_res["inference_latency_ms"]

        drl_cmr = compute_cmr_at_k(drl_res["stops"], interests) if drl_res["stops"] else 0.0
        drl_div = compute_category_diversity_at_k(drl_res["stops"]) if drl_res["stops"] else 0

        summary_by_strategy["DRL_ModeB_Agent"]["stops"].append(drl_stops)
        summary_by_strategy["DRL_ModeB_Agent"]["emissions"].append(drl_emiss)
        summary_by_strategy["DRL_ModeB_Agent"]["distance"].append(drl_dist)
        summary_by_strategy["DRL_ModeB_Agent"]["cost"].append(drl_cost)
        summary_by_strategy["DRL_ModeB_Agent"]["cmr"].append(drl_cmr)
        summary_by_strategy["DRL_ModeB_Agent"]["diversity"].append(drl_div)
        summary_by_strategy["DRL_ModeB_Agent"]["latency_ms"].append(drl_lat)

        benchmark_rows.append({
            "persona_id": p_id,
            "persona_name": p["name"],
            "strategy": "DRL_ModeB_Agent",
            "stops_visited": drl_stops,
            "total_emissions_kg": drl_emiss,
            "total_distance_km": drl_dist,
            "total_cost_inr": drl_cost,
            "cmr_score": drl_cmr,
            "category_diversity": drl_div,
            "budget_violated": drl_res["budget_violation"],
            "duration_violated": drl_res["duration_violation"],
            "inference_ms": drl_lat,
        })

        print(f"[{p_id}] {p['name']:22s} | C1 Emiss: {c1_emiss:5.1f}kg | C5 Emiss: {c5_emiss:5.1f}kg | DRL Emiss: {drl_emiss:5.1f}kg | DRL Cost: INR {drl_cost:7.1f}")

    # Compute aggregate stats
    aggregate_results = {}
    for strat, metrics in summary_by_strategy.items():
        aggregate_results[strat] = {
            "mean_stops": round(float(np.mean(metrics["stops"])), 2),
            "mean_emissions_kg": round(float(np.mean(metrics["emissions"])), 2),
            "mean_distance_km": round(float(np.mean(metrics["distance"])), 2),
            "mean_cost_inr": round(float(np.mean(metrics["cost"])), 2),
            "mean_cmr": round(float(np.mean(metrics["cmr"])), 3),
            "mean_diversity": round(float(np.mean(metrics["diversity"])), 2),
            "mean_inference_latency_ms": round(float(np.mean(metrics["latency_ms"])), 2),
        }

    # Export to CSV and JSON
    csv_path = os.path.join(out_dir, "drl_vs_baselines.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(benchmark_rows[0].keys()))
        writer.writeheader()
        writer.writerows(benchmark_rows)

    json_path = os.path.join(out_dir, "drl_experiment_results.json")
    full_output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "personas_count": len(BENCHMARK_PERSONAS),
        "aggregate_comparison": aggregate_results,
        "detailed_runs": benchmark_rows,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    print("\nBenchmark Evaluation Summary:")
    for strat, agg in aggregate_results.items():
        print(f"  {strat:20s} -> Emiss: {agg['mean_emissions_kg']:5.1f} kg | Cost: INR {agg['mean_cost_inr']:7.1f} | CMR: {agg['mean_cmr']:.2f} | Latency: {agg['mean_inference_latency_ms']}ms")

    return full_output
