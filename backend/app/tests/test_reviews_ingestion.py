"""
Tests for Visitor Reviews Ingestion & Provenance Module.
"""

import os
import pytest
from backend.scripts.ingest_visitor_reviews import (
    compute_text_sentiment,
    match_place_to_attraction,
    process_reviews,
)


def test_sentiment_scoring():
    pos_text = "Amazing historical fort with breathtaking views and clean architecture. A must visit!"
    neg_text = "Horrible experience, dirty, overcrowded and completely overpriced."
    neutral_text = "We visited in the afternoon for 2 hours."

    assert compute_text_sentiment(pos_text) > 0.0
    assert compute_text_sentiment(neg_text) < 0.0
    assert compute_text_sentiment(neutral_text) == 0.0
    assert compute_text_sentiment("") == 0.0


def test_attraction_matching():
    # Test verified alias
    match1 = match_place_to_attraction("Amber Fort", "Jaipur")
    assert match1 is not None
    assert match1[0] == "raj_001"

    # Test Palace of Winds alias
    match2 = match_place_to_attraction("Palace of Winds", "Jaipur")
    assert match2 is not None
    assert match2[0] == "raj_002"

    # Test Mehrangarh Fort (raj_014 in curated catalog)
    match3 = match_place_to_attraction("Mehrangarh Fort", "Jodhpur")
    assert match3 is not None
    assert match3[0] == "raj_014"

    # Test non-matching place
    match_none = match_place_to_attraction("Random Unrelated Spot", "London")
    assert match_none is None
