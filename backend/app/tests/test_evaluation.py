"""
Tests for Evaluation Metrics and Runner.
"""

import pytest
from app.evaluation.metrics import (
    compute_cmr_at_k,
    compute_category_diversity_at_k,
    compute_total_emissions,
    compute_gini_coefficient,
    compute_geographic_spread,
    compute_unique_districts,
    compute_jaccard_overlap,
    compute_kendall_tau,
)


def test_cmr_at_k():
    recs = [
        {"attraction": {"categories": ["history", "culture"]}},
        {"attraction": {"categories": ["nature"]}},
        {"attraction": {"categories": ["food"]}},
    ]
    # 2 out of 3 match "history" or "nature"
    cmr = compute_cmr_at_k(recs, ["history", "nature"])
    assert cmr == pytest.approx(2 / 3, 0.01)

    # 0 match
    assert compute_cmr_at_k(recs, ["religion"]) == 0.0


def test_category_diversity():
    recs = [
        {"attraction": {"categories": ["history", "culture"]}},
        {"attraction": {"categories": ["nature", "wildlife"]}},
    ]
    assert compute_category_diversity_at_k(recs) == 4


def test_total_emissions():
    recs = [
        {"estimated_emissions_kg": 12.5},
        {"estimated_emissions_kg": 7.5},
    ]
    assert compute_total_emissions(recs) == 20.0


def test_gini_coefficient():
    # Equal distribution has Gini ~ 0
    equal_vals = [100.0, 100.0, 100.0, 100.0]
    assert compute_gini_coefficient(equal_vals) < 0.01

    # Highly unequal distribution has higher Gini
    unequal_vals = [1.0, 2.0, 3.0, 1000.0]
    assert compute_gini_coefficient(unequal_vals) > 0.5


def test_jaccard_overlap():
    a = ["1", "2", "3", "4"]
    b = ["3", "4", "5", "6"]
    # Intersection 2, Union 6 => 2/6 = 0.3333
    assert compute_jaccard_overlap(a, b) == pytest.approx(0.3333, 0.01)
    assert compute_jaccard_overlap(a, a) == 1.0


def test_kendall_tau():
    a = ["a", "b", "c", "d"]
    # Identical
    assert compute_kendall_tau(a, a) == 1.0
    # Completely reversed
    assert compute_kendall_tau(a, ["d", "c", "b", "a"]) == -1.0
