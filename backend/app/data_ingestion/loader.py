"""
Data loader module — loads, validates, and prepares attraction data.

Handles both curated dataset and OSM-downloaded data.
Produces a clean pandas DataFrame ready for scoring and recommendation.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import List, Optional, Dict

from app.config import PROCESSED_DATA_DIR
from app.data_ingestion.curated_attractions import get_curated_attractions

logger = logging.getLogger(__name__)


def load_attractions() -> pd.DataFrame:
    """
    Load the attraction dataset.
    
    Priority:
    1. Processed CSV if it exists and is up-to-date
    2. Curated Python dataset (always available)
    
    Returns:
        DataFrame with validated attraction data.
    """
    processed_path = PROCESSED_DATA_DIR / "attractions.csv"
    
    if processed_path.exists():
        logger.info(f"Loading processed attractions from {processed_path}")
        df = pd.read_csv(processed_path)
        # Parse categories from string back to list
        if "categories" in df.columns:
            df["categories"] = df["categories"].apply(
                lambda x: x.split("|") if isinstance(x, str) else (list(x) if isinstance(x, (list, tuple)) else [])
            )
        return df
    
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
