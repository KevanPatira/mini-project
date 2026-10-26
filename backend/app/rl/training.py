"""
Training Workflow for Deep Reinforcement Learning Tourism Recommender.

Executes episodic simulation training of the DQN Agent under varied traveler
personas and spatiotemporal constraints. Logs loss and rewards, computes
evaluation metrics periodically, and serializes trained checkpoints.
"""

import os
import json
import csv
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from app.config import ORIGIN_CITIES, INTEREST_CATEGORIES
from app.rl.environment import TourismItineraryEnv
from app.rl.agent import DQNAgent

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "models"))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "results"))


def sample_training_scenario(rng: np.random.Generator) -> Dict[str, Any]:
    """Sample diverse, realistic tourist scenario parameters for training."""
    origin_cities = list(ORIGIN_CITIES.keys())
    origin = rng.choice(origin_cities)
    trip_days = int(rng.integers(2, 8))  # 2 to 7 days
    
    # Realistic Indian tourist budget ranges: 4,000 to 25,000 INR
    budget_level = rng.choice(["low", "medium", "high"])
    if budget_level == "low":
        budget = float(rng.uniform(4000.0, 9000.0))
    elif budget_level == "medium":
        budget = float(rng.uniform(10000.0, 18000.0))
    else:
        budget = float(rng.uniform(20000.0, 35000.0))

    # Sample 1 to 4 interest categories
    all_categories = list(INTEREST_CATEGORIES.keys())
    k_interests = int(rng.integers(1, 4))
    interests = rng.choice(all_categories, size=k_interests, replace=False).tolist()

    travel_month = int(rng.integers(1, 13))
    transport = rng.choice(["train", "bus", "car"])

    return {
        "origin_city": origin,
        "trip_days": trip_days,
        "budget_inr": budget,
        "user_interests": interests,
        "travel_month": travel_month,
        "preferred_transport": transport,
    }


def train_dqn(
    episodes: int = 500,
    batch_size: int = 32,
    lr: float = 0.001,
    gamma: float = 0.95,
    epsilon_start: float = 1.0,
    epsilon_min: float = 0.05,
    epsilon_decay: float = 0.992,
    target_update_freq: int = 50,
    eval_freq: int = 50,
    checkpoint_path: Optional[str] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Train DRL agent in simulated Rajasthan Tourism MDP.
    
    Returns training log dictionary and paths to saved artifacts.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    if checkpoint_path is None:
        checkpoint_path = os.path.join(MODELS_DIR, "drl_itinerary_agent.json")

    rng = np.random.default_rng(seed)
    np.random.seed(seed)

    # Initialize environment and agent
    env = TourismItineraryEnv()
    agent = DQNAgent(
        state_dim=env.state_dim,
        action_dim=env.action_space_size,
        hidden_dims=(128, 64),
        learning_rate=lr,
        gamma=gamma,
        epsilon_start=epsilon_start,
        epsilon_min=epsilon_min,
        epsilon_decay=epsilon_decay,
        target_update_freq=target_update_freq,
        buffer_capacity=10000,
        seed=seed,
    )

    training_logs: List[Dict[str, Any]] = []
    best_eval_return = -float("inf")
    start_time = time.time()

    print(f"Starting DQN Training: {episodes} episodes | State Dim: {env.state_dim} | Action Dim: {env.action_space_size}")

    for ep in range(1, episodes + 1):
        scenario = sample_training_scenario(rng)
        state, info = env.reset(
            origin_city=scenario["origin_city"],
            travel_month=scenario["travel_month"],
            trip_days=scenario["trip_days"],
            budget_inr=scenario["budget_inr"],
            user_interests=scenario["user_interests"],
            preferred_transport=scenario["preferred_transport"],
        )

        episode_reward = 0.0
        step_losses = []
        done = False
        steps = 0

        while not done:
            mask = info["action_mask"]
            action = agent.select_action(state, mask)
            next_state, reward, done, _, step_info = env.step(action)
            next_mask = step_info.get("action_mask", np.zeros(env.action_space_size, dtype=np.int32))

            # Push transition into experience replay
            agent.replay_buffer.push(state, action, reward, next_state, done, next_mask)

            # Optimization step
            loss = agent.train_step(batch_size=batch_size)
            if loss is not None:
                step_losses.append(loss)

            state = next_state
            info = step_info
            episode_reward += reward
            steps += 1

        agent.decay_epsilon()
        avg_loss = float(np.mean(step_losses)) if step_losses else 0.0

        log_entry = {
            "episode": ep,
            "return": round(float(episode_reward), 4),
            "steps": steps,
            "loss": round(avg_loss, 4),
            "epsilon": round(float(agent.epsilon), 4),
            "remaining_budget": round(float(env.remaining_budget), 2),
            "remaining_hours": round(float(env.remaining_hours), 2),
            "total_stops": len(env.itinerary_stops),
        }
        training_logs.append(log_entry)

        # Periodic Evaluation (Greedy policy, epsilon=0.0)
        if ep % eval_freq == 0 or ep == episodes:
            eval_return, eval_stops = evaluate_policy(env, agent, n_episodes=5, seed=seed + ep)
            print(
                f"Ep {ep:4d}/{episodes} | Return: {episode_reward:6.2f} | Eval Return: {eval_return:6.2f} "
                f"| Stops: {eval_stops:.1f} | Loss: {avg_loss:6.4f} | Eps: {agent.epsilon:.3f}"
            )

            # Save best checkpoint based on validation performance
            if eval_return > best_eval_return:
                best_eval_return = eval_return
                agent.save(
                    checkpoint_path,
                    extra_meta={
                        "trained_episodes": ep,
                        "best_eval_return": best_eval_return,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "mode": "Mode B (Simulator-Trained)",
                    },
                )

    total_training_time = round(time.time() - start_time, 2)
    print(f"Training completed in {total_training_time}s. Best Eval Return: {best_eval_return:.2f}")

    # Export training curve logs
    curves_json_path = os.path.join(RESULTS_DIR, "drl_training_curves.json")
    with open(curves_json_path, "w", encoding="utf-8") as f:
        json.dump(training_logs, f, indent=2)

    curves_csv_path = os.path.join(RESULTS_DIR, "drl_training_curves.csv")
    with open(curves_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(training_logs[0].keys()))
        writer.writeheader()
        writer.writerows(training_logs)

    return {
        "status": "success",
        "episodes": episodes,
        "training_time_seconds": total_training_time,
        "best_eval_return": best_eval_return,
        "checkpoint_path": checkpoint_path,
        "curves_json": curves_json_path,
        "curves_csv": curves_csv_path,
    }


def evaluate_policy(
    env: TourismItineraryEnv,
    agent: DQNAgent,
    n_episodes: int = 5,
    seed: int = 100,
) -> Tuple[float, float]:
    """Run greedy evaluation episodes without exploration."""
    eval_returns = []
    eval_stops = []
    rng = np.random.default_rng(seed)

    for _ in range(n_episodes):
        scenario = sample_training_scenario(rng)
        state, info = env.reset(
            origin_city=scenario["origin_city"],
            travel_month=scenario["travel_month"],
            trip_days=scenario["trip_days"],
            budget_inr=scenario["budget_inr"],
            user_interests=scenario["user_interests"],
            preferred_transport=scenario["preferred_transport"],
        )

        ep_ret = 0.0
        done = False
        while not done:
            mask = info["action_mask"]
            # Pure exploitation
            action = agent.select_action(state, mask, epsilon=0.0)
            next_state, reward, done, _, info = env.step(action)
            ep_ret += reward
            state = next_state

        eval_returns.append(ep_ret)
        eval_stops.append(len(env.itinerary_stops))

    return float(np.mean(eval_returns)), float(np.mean(eval_stops))
