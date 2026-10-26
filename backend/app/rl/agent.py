"""
Deep Q-Network (DQN) Agent for Sustainable Itinerary Recommendation.

Implements a pure-NumPy Multi-Layer Perceptron (MLP) with:
- He initialization & ReLU activations
- Vectorized forward & backward passes
- Adam optimizer with gradient clipping
- Experience Replay Buffer
- Target Network with periodic hard synchronization
- Action-masked epsilon-greedy exploration and Bellman target calculation
- Deterministic JSON checkpoint serialization and deserialization
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

logger = logging.getLogger(__name__)


class AdamOptimizer:
    """Vectorized Adam Optimizer for NumPy neural network layers."""

    def __init__(self, lr: float = 0.001, beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m: Dict[str, np.ndarray] = {}
        self.v: Dict[str, np.ndarray] = {}
        self.t = 0

    def step(self, params: Dict[str, np.ndarray], grads: Dict[str, np.ndarray]):
        self.t += 1
        lr_t = self.lr * np.sqrt(1.0 - self.beta2 ** self.t) / (1.0 - self.beta1 ** self.t)

        for key in params:
            if key not in grads:
                continue
            g = grads[key]

            if key not in self.m:
                self.m[key] = np.zeros_like(g)
                self.v[key] = np.zeros_like(g)

            # Update biased first & second moment estimates
            self.m[key] = self.beta1 * self.m[key] + (1.0 - self.beta1) * g
            self.v[key] = self.beta2 * self.v[key] + (1.0 - self.beta2) * (g ** 2)

            # Parameter update with clipped step
            update = lr_t * self.m[key] / (np.sqrt(self.v[key]) + self.eps)
            params[key] -= update


class QNetwork:
    """
    Two-hidden-layer MLP for Q-value estimation: Q(s, a).
    Architecture: input_dim -> hidden_dim1 -> hidden_dim2 -> output_dim
    """

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden_dims: Tuple[int, int] = (128, 64),
        seed: Optional[int] = None,
    ):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.hidden_dims = hidden_dims
        h1, h2 = hidden_dims

        rng = np.random.default_rng(seed)

        # He / Kaiming normal initialization for ReLU
        self.params: Dict[str, np.ndarray] = {
            "W1": (rng.standard_normal((input_dim, h1)) * np.sqrt(2.0 / input_dim)).astype(np.float32),
            "b1": np.zeros(h1, dtype=np.float32),
            "W2": (rng.standard_normal((h1, h2)) * np.sqrt(2.0 / h1)).astype(np.float32),
            "b2": np.zeros(h2, dtype=np.float32),
            "W3": (rng.standard_normal((h2, output_dim)) * np.sqrt(2.0 / h2)).astype(np.float32),
            "b3": np.zeros(output_dim, dtype=np.float32),
        }

    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Forward pass for a batch of states (N, input_dim).
        Returns Q-values (N, output_dim) and cache for backprop.
        """
        if x.ndim == 1:
            x = x.reshape(1, -1)

        z1 = np.dot(x, self.params["W1"]) + self.params["b1"]
        a1 = np.maximum(0.0, z1)  # ReLU

        z2 = np.dot(a1, self.params["W2"]) + self.params["b2"]
        a2 = np.maximum(0.0, z2)  # ReLU

        q = np.dot(a2, self.params["W3"]) + self.params["b3"]  # Linear output

        cache = {"x": x, "z1": z1, "a1": a1, "z2": z2, "a2": a2, "q": q}
        return q, cache

    def backward(self, cache: Dict[str, np.ndarray], dL_dq: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Backward pass computing parameter gradients.
        dL_dq: Gradient of loss w.r.t Q-values (N, output_dim).
        """
        N = cache["x"].shape[0]

        # Layer 3 gradients
        dW3 = np.dot(cache["a2"].T, dL_dq) / N
        db3 = np.sum(dL_dq, axis=0) / N

        # Layer 2 gradients
        da2 = np.dot(dL_dq, self.params["W3"].T)
        dz2 = da2 * (cache["z2"] > 0)
        dW2 = np.dot(cache["a1"].T, dz2) / N
        db2 = np.sum(dz2, axis=0) / N

        # Layer 1 gradients
        da1 = np.dot(dz2, self.params["W2"].T)
        dz1 = da1 * (cache["z1"] > 0)
        dW1 = np.dot(cache["x"].T, dz1) / N
        db1 = np.sum(dz1, axis=0) / N

        # Gradient clipping to prevent gradient explosions in RL
        grads = {"W1": dW1, "b1": db1, "W2": dW2, "b2": db2, "W3": dW3, "b3": db3}
        for k in grads:
            grads[k] = np.clip(grads[k], -5.0, 5.0)

        return grads

    def copy_weights_from(self, source_net: "QNetwork"):
        """Synchronize weights from another network."""
        for k in self.params:
            self.params[k] = np.copy(source_net.params[k])


class ReplayBuffer:
    """Fixed-capacity ring buffer for off-policy transition experience replay."""

    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer: List[Tuple[np.ndarray, int, float, np.ndarray, bool, np.ndarray]] = []
        self.position = 0

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        next_action_mask: np.ndarray,
    ):
        item = (state, action, reward, next_state, done, next_action_mask)
        if len(self.buffer) < self.capacity:
            self.buffer.append(item)
        else:
            self.buffer[self.position] = item
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        states, actions, rewards, next_states, dones, masks = [], [], [], [], [], []

        for idx in indices:
            s, a, r, ns, d, m = self.buffer[idx]
            states.append(s)
            actions.append(a)
            rewards.append(r)
            next_states.append(ns)
            dones.append(d)
            masks.append(m)

        return (
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.int32),
            np.array(rewards, dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones, dtype=np.bool_),
            np.array(masks, dtype=np.int32),
        )

    def __len__(self) -> int:
        return len(self.buffer)


class DQNAgent:
    """
    Deep Q-Network Agent for sequential tourism itinerary recommendation.
    
    Enforces valid action selection through action masking during both
    exploration/exploitation and Bellman target calculation.
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dims: Tuple[int, int] = (128, 64),
        learning_rate: float = 0.001,
        gamma: float = 0.95,
        epsilon_start: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.995,
        target_update_freq: int = 100,
        buffer_capacity: int = 10000,
        seed: Optional[int] = 42,
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dims = hidden_dims
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.target_update_freq = target_update_freq
        self.step_counter = 0

        self.rng = np.random.default_rng(seed)

        # Networks
        self.online_net = QNetwork(state_dim, action_dim, hidden_dims=hidden_dims, seed=seed)
        self.target_net = QNetwork(state_dim, action_dim, hidden_dims=hidden_dims, seed=seed)
        self.target_net.copy_weights_from(self.online_net)

        self.optimizer = AdamOptimizer(lr=learning_rate)
        self.replay_buffer = ReplayBuffer(capacity=buffer_capacity)

    def select_action(
        self,
        state: np.ndarray,
        action_mask: np.ndarray,
        epsilon: Optional[float] = None,
    ) -> int:
        """
        Select action using action-masked epsilon-greedy strategy.
        action_mask: binary vector where 1 = valid, 0 = infeasible.
        """
        eps = self.epsilon if epsilon is None else epsilon
        valid_actions = np.where(action_mask == 1)[0]

        if len(valid_actions) == 0:
            # Fallback to stop action (last index) if all actions masked
            return self.action_dim - 1

        # Exploration: random valid action
        if self.rng.random() < eps:
            return int(self.rng.choice(valid_actions))

        # Exploitation: masked argmax of Q-values
        q_vals, _ = self.online_net.forward(state)
        q_row = q_vals[0].copy()

        # Invalidate illegal actions with negative infinity
        q_row[action_mask == 0] = -1e9
        return int(np.argmax(q_row))

    def train_step(self, batch_size: int = 32) -> Optional[float]:
        """
        Sample minibatch from replay buffer, compute masked Bellman target,
        and update online Q-network via Adam.
        """
        if len(self.replay_buffer) < batch_size:
            return None

        states, actions, rewards, next_states, dones, next_masks = self.replay_buffer.sample(batch_size)

        # 1. Compute target Q-values Q_target(s', a')
        next_q, _ = self.target_net.forward(next_states)  # (batch_size, action_dim)

        # Mask invalid actions in target calculation
        next_q_masked = np.copy(next_q)
        next_q_masked[next_masks == 0] = -1e9
        max_next_q = np.max(next_q_masked, axis=1)

        # For states with zero valid actions, target max Q is 0.0
        no_valid_next = (np.sum(next_masks, axis=1) == 0)
        max_next_q[no_valid_next] = 0.0

        # Bellman target: y = r if done else r + gamma * max_a' Q_target(s', a')
        targets = rewards + (1.0 - dones.astype(np.float32)) * self.gamma * max_next_q

        # 2. Forward pass online network
        current_q, cache = self.online_net.forward(states)

        # 3. Compute loss and gradient w.r.t chosen action: L = 0.5 * (Q(s, a) - y)^2
        dL_dq = np.zeros_like(current_q)
        batch_indices = np.arange(batch_size)
        errors = current_q[batch_indices, actions] - targets

        # Huber loss derivative for robust training
        huber_delta = 1.0
        abs_errors = np.abs(errors)
        linear_mask = (abs_errors > huber_delta)
        dL_dq[batch_indices, actions] = np.where(linear_mask, huber_delta * np.sign(errors), errors)

        loss = float(np.mean(np.where(linear_mask, huber_delta * (abs_errors - 0.5 * huber_delta), 0.5 * (errors ** 2))))

        # 4. Backward pass & Adam step
        grads = self.online_net.backward(cache, dL_dq)
        self.optimizer.step(self.online_net.params, grads)

        # 5. Periodic target network update
        self.step_counter += 1
        if self.step_counter % self.target_update_freq == 0:
            self.target_net.copy_weights_from(self.online_net)

        return loss

    def decay_epsilon(self):
        """Exponential epsilon decay."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self, filepath: str, extra_meta: Optional[Dict[str, Any]] = None):
        """Save agent parameters and configuration to JSON file."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        serializable_params = {
            k: self.online_net.params[k].tolist() for k in self.online_net.params
        }
        data = {
            "model_type": "DQN_NumPy",
            "state_dim": self.state_dim,
            "action_dim": self.action_dim,
            "hidden_dims": list(self.hidden_dims),
            "gamma": self.gamma,
            "epsilon": float(self.epsilon),
            "step_counter": self.step_counter,
            "weights": serializable_params,
            "metadata": extra_meta or {},
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved DRL agent checkpoint to {filepath}")

    def load(self, filepath: str) -> bool:
        """Load agent weights from JSON checkpoint."""
        if not os.path.exists(filepath):
            logger.warning(f"Checkpoint file not found at {filepath}")
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("state_dim") != self.state_dim or data.get("action_dim") != self.action_dim:
                logger.error(f"Dimension mismatch loading checkpoint from {filepath}")
                return False

            for k, val in data["weights"].items():
                if k in self.online_net.params:
                    self.online_net.params[k] = np.array(val, dtype=np.float32)
            self.target_net.copy_weights_from(self.online_net)
            self.epsilon = data.get("epsilon", self.epsilon_min)
            self.step_counter = data.get("step_counter", 0)
            logger.info(f"Successfully loaded DRL agent checkpoint from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load checkpoint from {filepath}: {e}")
            return False
