"""
CLI Script to Train the Deep Reinforcement Learning Tourism Recommender Agent.

Usage:
    python backend/scripts/train_drl.py --episodes 500 --seed 42
"""

import argparse
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rl.training import train_dqn


def main():
    parser = argparse.ArgumentParser(description="Train AuraTour DRL Tourism Recommendation Agent")
    parser.add_argument("--episodes", type=int, default=500, help="Number of training episodes (default: 500)")
    parser.add_argument("--batch-size", type=int, default=32, help="Minibatch size for replay buffer (default: 32)")
    parser.add_argument("--lr", type=float, default=0.001, help="Adam learning rate (default: 0.001)")
    parser.add_argument("--gamma", type=float, default=0.95, help="Reward discount factor (default: 0.95)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--output", type=str, default=None, help="Custom path for saving agent JSON checkpoint")

    args = parser.parse_args()

    print("======================================================================")
    print("       AuraTour DRL Sequential Itinerary Planner Training             ")
    print("======================================================================")
    print(f"Episodes:    {args.episodes}")
    print(f"Batch Size:  {args.batch_size}")
    print(f"LR:          {args.lr}")
    print(f"Gamma:       {args.gamma}")
    print(f"Seed:        {args.seed}")
    print("----------------------------------------------------------------------")

    res = train_dqn(
        episodes=args.episodes,
        batch_size=args.batch_size,
        lr=args.lr,
        gamma=args.gamma,
        seed=args.seed,
        checkpoint_path=args.output,
    )

    print("\nTraining Finished Successfully!")
    print(f"Checkpoint saved to: {res['checkpoint_path']}")
    print(f"Training curves:     {res['curves_csv']}")


if __name__ == "__main__":
    main()
