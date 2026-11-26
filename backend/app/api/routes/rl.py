"""
Reinforcement Learning inspection and benchmark API routes.
"""
import os
import json
from fastapi import APIRouter, HTTPException
from app.rl.evaluation import DEFAULT_CHECKPOINT

router = APIRouter()


@router.get("/api/rl/status")
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


@router.get("/api/rl/benchmark")
def get_rl_benchmark_results():
    """Returns precomputed empirical benchmark results comparing DRL vs C1 & C5."""
    results_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "results", "drl_experiment_results.json")
    )
    if not os.path.exists(results_path):
        raise HTTPException(
            status_code=404,
            detail="Benchmark results not found. Run scripts/run_drl_experiments.py first.",
        )

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@router.get("/api/rl/training-curves")
def get_rl_training_curves():
    """Returns episodic returns and training loss history."""
    curves_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "results", "drl_training_curves.json")
    )
    if not os.path.exists(curves_path):
        raise HTTPException(
            status_code=404,
            detail="Training curves not found. Run scripts/train_drl.py first.",
        )

    with open(curves_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"curves": data}
