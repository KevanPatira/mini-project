"""
Data loader module — loads, validates, and prepares attraction data.

Handles both curated dataset and OSM-downloaded data.
Produces a clean pandas DataFrame ready for scoring and recommendation.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from app.config import PROCESSED_DATA_DIR
from app.data_ingestion.curated_attractions import get_curated_attractions

logger = logging.getLogger(__name__)


def load_attractions() -> pd.DataFrame:
    """
    Load the attraction dataset.
    
    Priority:
    1. Processed CSV if it exists and is up-to-date
    2. Curated Python dataset (always available)
    Enriched with authentic visitor review statistics (from Kaggle) when available.
    
    Returns:
        DataFrame with validated attraction data.
    """
    processed_path = PROCESSED_DATA_DIR / "attractions.csv"
    reviews_summary_path = PROCESSED_DATA_DIR / "attraction_reviews_summary.csv"
    
    if processed_path.exists():
        logger.info(f"Loading processed attractions from {processed_path}")
        df = pd.read_csv(processed_path)
        # Parse categories from string back to list
        if "categories" in df.columns:
            df["categories"] = df["categories"].apply(
                lambda x: x.split("|") if isinstance(x, str) else (list(x) if isinstance(x, (list, tuple)) else [])
            )
    else:
        logger.info("Loading curated attractions dataset")
        attractions = get_curated_attractions()
        df = pd.DataFrame(attractions)
        
        # Validate
        df = validate_attractions(df)
        
        # Save processed version
        save_df = df.copy()
        save_df["categories"] = save_df["categories"].apply(
            lambda x: "|".join(x) if isinstance(x, list) else x
        )
        save_df.to_csv(processed_path, index=False, encoding="utf-8")
        logger.info(f"Saved {len(df)} attractions to {processed_path}")

    # Enrich with real visitor reviews data if available
    if reviews_summary_path.exists():
        try:
            rev_df = pd.read_csv(reviews_summary_path)
            cols = ["canonical_id", "review_count", "avg_visitor_rating", "avg_sentiment_score"]
            existing_cols = [c for c in cols if c in rev_df.columns]
            if "canonical_id" in existing_cols:
                rev_sub = rev_df[existing_cols].rename(columns={"canonical_id": "id"})
                for col in ["review_count", "avg_visitor_rating", "avg_sentiment_score"]:
                    if col in df.columns:
                        df = df.drop(columns=[col])
                df = df.merge(rev_sub, on="id", how="left")
                logger.info(f"Enriched {len(df)} attractions with authentic visitor reviews data")
        except Exception as e:
            logger.warning(f"Could not merge review summary: {e}")

    return df


def validate_attractions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean the attractions DataFrame.
    
    Checks:
    - Required columns present
    - Coordinates within valid range
    - No duplicate IDs
    - Categories are non-empty lists
    """
    required_cols = ["id", "name", "latitude", "longitude", "city", "categories"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Check for duplicates
    dupes = df[df["id"].duplicated()]
    if len(dupes) > 0:
        logger.warning(f"Removing {len(dupes)} duplicate attraction IDs")
        df = df.drop_duplicates(subset=["id"])
    
    # Validate coordinates
    invalid_coords = df[
        (df["latitude"] < 20) | (df["latitude"] > 32) |
        (df["longitude"] < 68) | (df["longitude"] > 80)
    ]
    if len(invalid_coords) > 0:
        logger.warning(
            f"{len(invalid_coords)} attractions have coordinates outside Rajasthan range — keeping but flagging"
        )
    
    # Ensure categories are lists
    df["categories"] = df["categories"].apply(
        lambda x: x if isinstance(x, list) else [x] if isinstance(x, str) else []
    )
    
    empty_cats = df[df["categories"].apply(len) == 0]
    if len(empty_cats) > 0:
        logger.warning(f"{len(empty_cats)} attractions have no categories — assigning 'culture' as default")
        df.loc[df["categories"].apply(len) == 0, "categories"] = df.loc[
            df["categories"].apply(len) == 0, "categories"
        ].apply(lambda x: ["culture"])
    
    # Fill missing district with city
    if "district" in df.columns:
        df["district"] = df["district"].fillna(df["city"])
    else:
        df["district"] = df["city"]
    
    logger.info(
        f"Validated {len(df)} attractions across {df['city'].nunique()} cities, "
        f"{df['district'].nunique()} districts"
    )
    
    return df


def get_attraction_by_id(attraction_id: str, df: Optional[pd.DataFrame] = None) -> Optional[Dict]:
    """Get a single attraction by ID."""
    if df is None:
        df = load_attractions()
    
    row = df[df["id"] == attraction_id]
    if len(row) == 0:
        return None
    
    d = row.iloc[0].to_dict()
    def _clean_val(v):
        if v is None:
            return None
        if isinstance(v, (list, tuple, dict, set)):
            return v
        try:
            if pd.isna(v):
                return None
        except (ValueError, TypeError):
            pass
        return v

    return {k: _clean_val(v) for k, v in d.items()}


def get_attractions_by_city(city: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Get all attractions in a given city."""
    if df is None:
        df = load_attractions()
    return df[df["city"].str.lower() == city.lower()]


def get_data_quality_summary(df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Generate a data quality summary for the research dashboard.
    
    Returns counts and percentages of available vs. missing data fields.
    """
    if df is None:
        df = load_attractions()
    
    total = len(df)
    summary = {
        "total_attractions": total,
        "cities": df["city"].nunique(),
        "districts": df["district"].nunique(),
        "fields": {}
    }
    
    optional_fields = [
        "description", "opening_hours", "entry_fee",
        "estimated_visit_duration_hours", "heritage_status",
        "annual_visitors", "image_url", "wikidata_id"
    ]
    
    for field in optional_fields:
        if field in df.columns:
            non_null = df[field].notna().sum()
            summary["fields"][field] = {
                "available": int(non_null),
                "missing": int(total - non_null),
                "coverage_pct": round(100 * non_null / total, 1)
            }
    
    # Category distribution
    all_cats = []
    for cats in df["categories"]:
        if isinstance(cats, list):
            all_cats.extend(cats)
    from collections import Counter
    summary["category_distribution"] = dict(Counter(all_cats).most_common())
    
    return summary


# ─── Transport Fare Matrix Loader ────────────────────────────────────────────

_TRANSPORT_FARE_MATRIX = None


def load_transport_fare_matrix() -> Dict[str, Dict]:
    """
    Load precomputed empirical transport fare & schedule matrix.
    Generated from real Indian Railways, Rajasthan bus routes, and flight datasets.
    """
    global _TRANSPORT_FARE_MATRIX
    if _TRANSPORT_FARE_MATRIX is not None:
        return _TRANSPORT_FARE_MATRIX

    matrix_path = PROCESSED_DATA_DIR / "transport_fare_matrix.json"
    if matrix_path.exists():
        try:
            import json
            with open(matrix_path, "r", encoding="utf-8") as f:
                _TRANSPORT_FARE_MATRIX = json.load(f)
            logger.info(f"Loaded {len(_TRANSPORT_FARE_MATRIX)} empirical transport routes from {matrix_path}")
            return _TRANSPORT_FARE_MATRIX
        except Exception as e:
            logger.warning(f"Error loading transport fare matrix: {e}")

    _TRANSPORT_FARE_MATRIX = {}
    return _TRANSPORT_FARE_MATRIX


def get_transport_route_details(
    origin_city: str,
    dest_city: str,
    mode: str,
    distance_km: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Retrieve empirical transport route details (distance, duration, fare, emissions).
    Falls back to calibrated empirical tariffs when exact OD pair is unobserved.
    """
    matrix = load_transport_fare_matrix()
    f_norm = origin_city.strip().lower() if origin_city else ""
    t_norm = dest_city.strip().lower() if dest_city else ""
    m_norm = mode.strip().lower() if mode else "train"

    key = f"{f_norm}__{t_norm}__{m_norm}"
    if key in matrix:
        entry = matrix[key]
        return {
            "distance_km": entry["distance_km"],
            "duration_hours": entry["duration_hours"],
            "fare_inr": entry["fare_inr"],
            "data_source": entry.get("data_source", "empirical_dataset"),
            "frequency_daily": entry.get("frequency_daily", 1),
            "is_empirical": True,
        }

    # Reverse lookup for bidirectional routes (e.g. bus/train)
    rev_key = f"{t_norm}__{f_norm}__{m_norm}"
    if rev_key in matrix:
        entry = matrix[rev_key]
        return {
            "distance_km": entry["distance_km"],
            "duration_hours": entry["duration_hours"],
            "fare_inr": entry["fare_inr"],
            "data_source": entry.get("data_source", "empirical_dataset"),
            "frequency_daily": entry.get("frequency_daily", 1),
            "is_empirical": True,
        }

    # Calibrated empirical fallback tariff models
    dist = distance_km or 300.0
    if m_norm == "train":
        fare = round(140.0 + max(0.0, dist - 100.0) * 0.58, 1)  # Indian Railways distance slab
        dur = round(dist / 55.0, 2)
        src = "calibrated_railways_tariff"
    elif m_norm == "bus":
        fare = round(max(40.0, dist * 1.45), 1)
        dur = round(dist / 45.0, 2)
        src = "calibrated_bus_tariff"
    elif m_norm == "flight":
        fare = round(3200.0 + dist * 4.2, 1)
        dur = round((dist / 600.0) + 2.0, 2)
        src = "calibrated_flight_tariff"
    else:  # car / taxi
        rate = 14.0 if dist <= 30.0 else 12.0
        fare = round(dist * rate, 1)
        speed = 30.0 if dist <= 30.0 else 60.0
        dur = round(dist / speed, 2)
        src = "calibrated_commercial_taxi_tariff"

    return {
        "distance_km": dist,
        "duration_hours": dur,
        "fare_inr": fare,
        "data_source": src,
        "frequency_daily": None,
        "is_empirical": False,
    }

