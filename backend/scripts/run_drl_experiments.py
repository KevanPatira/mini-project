"""
CLI Script to Run the DRL vs Baseline (C1 & C5) Benchmark Experiment.

Usage:
    python backend/scripts/run_drl_experiments.py
"""

import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rl.evaluation import benchmark_drl_vs_baselines


def main():
    print("Executing Empirical Benchmark: DRL vs C1 & C5 Baselines...")
    res = benchmark_drl_vs_baselines()
    print("\nBenchmark experiment completed successfully!")


if __name__ == "__main__":
    main()
