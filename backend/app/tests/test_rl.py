"""
Comprehensive Unit and Regression Tests for Deep Reinforcement Learning (DRL) Integration.

Covers:
1. Monument matcher & data provenance preservation
2. StateEncoder numerical bounds and dimensionality
3. Reward function components, normalization, and w_budget > w_emissions invariant
4. TourismItineraryEnv action masking, budget/time constraints, and termination
5. DQNAgent MLP forward/backward, experience replay, target sync, and checkpoint save/load
6. FastAPI DRL endpoints and schema compatibility
"""

import os
import json
import tempfile
import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.data_ingestion.loader import load_attractions
from app.data_ingestion.monument_matcher import MonumentMatcher
from app.rl.state import StateEncoder
from app.rl.reward import ItineraryRewardCalculator
from app.rl.environment import TourismItineraryEnv
from app.rl.agent import DQNAgent, QNetwork
from app.rl.evaluation import generate_drl_itinerary
from app.api.main import app


class TestMonumentMatcherAndData:
    """Test data ingestion, name normalization, and monument matching logic."""

    @pytest.fixture
    def matcher(self):
        return MonumentMatcher()

    def test_exact_alias_matching(self, matcher):
        cid, method, conf, notes = matcher.match_name("Amber Fort", "Jaipur")
        assert cid == "raj_001"
        assert conf >= 0.90
        assert method in ["exact", "alias_verified"]

    def test_city_disambiguation(self, matcher):
        # Disambiguates City Palace Jaipur (raj_003) vs City Palace Udaipur (raj_015)
        j_cid, _, _, _ = matcher.match_name("City Palace", "Jaipur")
        u_cid, _, _, _ = matcher.match_name("City Palace", "Udaipur")
        assert j_cid == "raj_003"
        assert u_cid == "raj_015"

    def test_fuzzy_matching_with_confidence(self, matcher):
        cid, method, conf, notes = matcher.match_name("Jantar Mantar Observatory", "Jaipur")
        assert cid == "raj_004"
        assert conf >= 0.65

    def test_unmatched_record_handling(self, matcher):
        cid, method, conf, notes = matcher.match_name("Random Nonexistent Structure XYZ", "Nowhere")
        assert cid is None or conf < 0.60
        assert method in ["unmatched", "none"]


class TestStateEncoder:
    """Test state vector construction, normalization, and bounds."""

    def test_state_encoder_dimensions_and_bounds(self):
        attractions = load_attractions().to_dict("records")
        encoder = StateEncoder(attractions)

        # Expected: 2 (coords) + 45 (visited) + 1 (rem_hours) + 1 (budget) + 1 (day) + 1 (day_hours) + 10 (pref) + 2 (season) + 1 (stops) = 64
        assert encoder.state_dim == 64

        visited = np.zeros(len(attractions), dtype=np.int32)
        visited[0] = 1
        s = encoder.encode(
            current_lat=26.9124,
            current_lon=75.7873,
            visited_mask=visited,
            remaining_hours=20.0,
            total_hours=36.0,
            remaining_budget=12000.0,
            total_budget=15000.0,
            current_day=2,
            max_days=4,
            day_hours_remaining=5.0,
            max_day_hours=9.0,
            user_interests=["history", "culture"],
            travel_month=11,
            stops_count=2,
        )

        assert isinstance(s, np.ndarray)
        assert s.shape == (64,)
        assert np.all(np.isfinite(s))
        # Visited mask check
        assert s[2] == 1.0
        assert s[3] == 0.0


class TestRewardCalculator:
    """Test multi-objective reward calculation and priority invariants."""

    def test_priority_invariant_budget_greater_than_emissions(self):
        calc = ItineraryRewardCalculator()
        assert calc.w_b > calc.w_e, "Budget weight must strictly exceed emissions weight (w_b > w_e)"
        assert calc.w_b == 0.12
        assert calc.w_e == 0.08

    def test_reward_components_bounded(self):
        calc = ItineraryRewardCalculator()
        att = {
            "categories": ["history", "architecture"],
            "annual_visitors": 2000000,
        }
        res = calc.compute_step_reward(
            attraction=att,
            user_interests=["history"],
            travel_hours=2.0,
            leg_cost_inr=800.0,
            leg_emissions_kg=15.0,
            current_visited_categories=set(),
        )

        assert "total" in res
        assert "components" in res
        assert -2.0 <= res["total"] <= 2.0
        assert res["components"]["preference_reward"] > 0.0
        assert res["components"]["budget_penalty"] < 0.0

    def test_terminal_stop_reward(self):
        calc = ItineraryRewardCalculator()
        # Premature stop penalty
        early_res = calc.compute_step_reward(
            attraction={},
            user_interests=["history"],
            travel_hours=0,
            leg_cost_inr=0,
            leg_emissions_kg=0,
            current_visited_categories=set(),
            is_terminal_stop_action=True,
            stops_count=1,
            min_stops_target=4,
        )
        assert early_res["total"] < 0.0

        # Successful complete stop bonus
        done_res = calc.compute_step_reward(
            attraction={},
            user_interests=["history"],
            travel_hours=0,
            leg_cost_inr=0,
            leg_emissions_kg=0,
            current_visited_categories=set(),
            is_terminal_stop_action=True,
            stops_count=5,
            min_stops_target=4,
        )
        assert done_res["total"] > 0.0


class TestTourismEnvironment:
    """Test MDP environment constraints, action masking, and step dynamics."""

    def test_action_masking_prevents_revisits(self):
        env = TourismItineraryEnv()
        state, info = env.reset(origin_city="delhi", budget_inr=15000.0)

        mask = info["action_mask"]
        assert mask[0] == 1  # Initially unvisited

        # Step into attraction 0
        _, _, _, _, next_info = env.step(0)
        next_mask = next_info["action_mask"]
        assert next_mask[0] == 0, "Visited attraction must be masked to prevent duplicate visits"

    def test_action_masking_enforces_budget_ceiling(self):
        env = TourismItineraryEnv()
        # Set tiny budget of only 50 INR (insufficient for any transit + entry fee)
        state, info = env.reset(origin_city="delhi", budget_inr=50.0)
        mask = info["action_mask"]

        # Only STOP action (last action) should be feasible
        attraction_actions = mask[:-1]
        assert np.sum(attraction_actions) == 0, "No attraction should be valid when budget is exhausted"
        assert mask[-1] == 1, "STOP action must remain valid"

    def test_step_invalid_action_penalized_and_terminates(self):
        env = TourismItineraryEnv()
        env.reset(budget_inr=50.0)
        # Force invalid attraction action
        _, reward, done, _, info = env.step(0)
        assert done is True
        assert reward == -1.0
        assert "error" in info


class TestDQNAgent:
    """Test neural network forward/backward, experience replay, and serialization."""

    def test_agent_initialization_and_forward(self):
        agent = DQNAgent(state_dim=64, action_dim=46, hidden_dims=(128, 64), seed=42)
        state = np.zeros(64, dtype=np.float32)
        mask = np.ones(46, dtype=np.int32)
        mask[0] = 0  # Invalidate action 0

        action = agent.select_action(state, mask, epsilon=0.0)
        assert action != 0, "Masked action 0 must never be chosen in exploitation"
        assert 0 <= action < 46

    def test_replay_buffer_and_train_step(self):
        agent = DQNAgent(state_dim=64, action_dim=46, hidden_dims=(128, 64), seed=42)
        state = np.random.randn(64).astype(np.float32)
        next_state = np.random.randn(64).astype(np.float32)
        mask = np.ones(46, dtype=np.int32)

        # Populate buffer with 40 synthetic transitions
        for _ in range(40):
            agent.replay_buffer.push(state, 1, 0.5, next_state, False, mask)

        loss = agent.train_step(batch_size=32)
        assert loss is not None
        assert isinstance(loss, float)
        assert loss >= 0.0

    def test_checkpoint_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_path = os.path.join(tmpdir, "test_agent.json")
            agent1 = DQNAgent(state_dim=64, action_dim=46, hidden_dims=(128, 64), seed=123)
            agent1.save(ckpt_path, extra_meta={"test_flag": True})

            agent2 = DQNAgent(state_dim=64, action_dim=46, hidden_dims=(128, 64), seed=999)
            success = agent2.load(ckpt_path)
            assert success is True

            # Verify parameter equality
            for k in agent1.online_net.params:
                np.testing.assert_allclose(agent1.online_net.params[k], agent2.online_net.params[k])


class TestDRLIntegration:
    """Integration tests for DRL itinerary builder and FastAPI endpoints."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_generate_drl_itinerary_schema(self):
        res = generate_drl_itinerary(
            origin_city="delhi",
            travel_month=11,
            trip_duration_days=4,
            budget_inr=15000.0,
            user_interests=["history", "architecture"],
        )
        assert res["strategy_used"] == "drl"
        assert res["total_stops"] > 0
        assert res["budget_violation"] is False
        assert res["duration_violation"] is False
        assert res["total_cost_inr"] <= 15000.0
        assert len(res["stops"]) == res["total_stops"]

    def test_api_rl_status(self, client):
        resp = client.get("/api/rl/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["algorithm"] == "Deep Q-Network (DQN) with Action Masking"
        assert data["training_mode"] == "Mode B (Simulator-Based MDP grounded in authentic Rajasthan data)"
        assert data["state_dimension"] == 64
        assert data["action_space"] == 46

    def test_api_rl_benchmark(self, client):
        resp = client.get("/api/rl/benchmark")
        assert resp.status_code == 200
        data = resp.json()
        assert "aggregate_comparison" in data
        assert "DRL_ModeB_Agent" in data["aggregate_comparison"]
        assert "C1_Baseline_TSP" in data["aggregate_comparison"]
        assert "C5_Sustainable_TSP" in data["aggregate_comparison"]

    def test_api_itinerary_with_drl_strategy(self, client):
        payload = {
            "preferences": {
                "interests": ["history", "culture"],
                "origin_city": "delhi",
                "travel_month": 11,
                "trip_duration_days": 4,
                "budget_level": "medium",
                "preferred_transport": "train",
            },
            "selected_attraction_ids": [],
            "optimize_for": "balanced",
            "strategy": "drl",
        }
        resp = client.post("/api/itinerary", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["strategy_used"] == "drl"
        assert len(data["stops"]) > 0
        assert data["total_cost_inr"] > 0
