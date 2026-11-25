"""
Visitor Reviews Ingestion & Provenance Pipeline.

Ingests the 'Indian Places to Visit Reviews Data' dataset (from Kaggle: 1.48M reviews),
matches visitor reviews against the canonical 45-attraction Rajasthan catalog,
computes authentic sentiment/rating statistics, and outputs processed datasets
for the recommendation engine and DRL state representations.
"""

import os
import sys
import csv
import io
import json
import zipfile
import re
import time
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict

# Add backend to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.data_ingestion.curated_attractions import RAJASTHAN_ATTRACTIONS
from app.data_ingestion.monument_matcher import MonumentMatcher, normalize_name

DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

RAJASTHAN_CITIES = {
    "jaipur", "udaipur", "jodhpur", "jaisalmer", "bikaner", "pushkar",
    "ajmer", "chittorgarh", "mount abu", "alwar", "sawai madhopur",
    "bharatpur", "shekhawati", "mandawa", "bundee", "bundi", "ranthambore"
}

# Positive and negative word sets for lightweight, fast sentiment scoring
POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "wonderful", "beautiful", "stunning",
    "magnificent", "must", "visit", "love", "loved", "lovely", "peaceful", "clean",
    "awesome", "best", "superb", "spectacular", "historic", "breathtaking", "divine"
}
NEGATIVE_WORDS = {
    "bad", "terrible", "horrible", "awful", "worst", "dirty", "overcrowded",
    "crowded", "expensive", "waste", "poor", "overpriced", "noisy", "disappointing",
    "scam", "cheat", "rude", "unpleasant", "maintenance"
}

_MATCHER = MonumentMatcher()
_MATCH_CACHE: Dict[Tuple[str, str], Optional[Tuple[str, str, str]]] = {}


def compute_text_sentiment(text: str) -> float:
    """
    Lightweight sentiment scoring returning a value between -1.0 and +1.0.
    """
    if not text or not isinstance(text, str):
        return 0.0
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    if not words:
        return 0.0
    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return round((pos_count - neg_count) / total, 3)


def locate_reviews_dataset() -> Optional[Tuple[str, bool]]:
    """
    Find Review_db.csv or a zip containing it in common locations.
    Returns (path, is_zip) or None.
    """
    candidates = [
        os.path.join(DATA_RAW_DIR, "Review_db.csv"),
        os.path.join(DATA_RAW_DIR, "indian-places-to-visit-reviews-data.zip"),
        os.path.join(WORKSPACE_DIR, "Review_db.csv"),
        os.path.join(WORKSPACE_DIR, "indian-places-to-visit-reviews-data.zip"),
        os.path.join(os.path.expanduser("~"), "Downloads", "Review_db.csv"),
        os.path.join(os.path.expanduser("~"), "Downloads", "indian-places-to-visit-reviews-data.zip"),
    ]
    for p in candidates:
        if os.path.exists(p):
            is_zip = p.lower().endswith(".zip")
            return (p, is_zip)
    return None


def match_place_to_attraction(place_name: str, city_name: str) -> Optional[Tuple[str, str, str]]:
    """
    Match a place and city against the canonical 45 attractions with memoization.
    """
    cache_key = (place_name, city_name)
    if cache_key in _MATCH_CACHE:
        return _MATCH_CACHE[cache_key]

    norm_city = normalize_name(city_name)
    cid, method, conf, notes = _MATCHER.match_name(place_name, city_hint=city_name)
    result = None
    if cid and conf >= 0.70:
        attr = _MATCHER.catalog_by_id.get(cid)
        if attr:
            # If city is supplied, verify it matches or is Rajasthan
            if not norm_city or any(rc in norm_city for rc in RAJASTHAN_CITIES) or norm_city in normalize_name(attr["city"]):
                result = (cid, attr["name"], f"{method}_{conf:.2f}")

    _MATCH_CACHE[cache_key] = result
    return result


def process_reviews(file_path: str, is_zip: bool) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Stream and process 1.48M review records, filter Rajasthan monuments, match canonical IDs,
    and aggregate sentiment/rating statistics with progress reporting.
    """
    matched_reviews = []
    attraction_stats = defaultdict(lambda: {
        "ratings": [],
        "sentiment_scores": [],
        "reviews": [],
        "canonical_name": "",
        "city": "",
    })

    t_start = time.time()
    row_count = 0

    def handle_row(row: Dict[str, str]):
        nonlocal row_count
        row_count += 1
        if row_count % 200000 == 0:
            elapsed = time.time() - t_start
            print(f"[*] Streamed {row_count:,} reviews ({elapsed:.1f}s) | Matched so far: {len(matched_reviews):,}")

        place = row.get("Place") or row.get("place") or row.get("place_name") or ""
        city = row.get("City") or row.get("city") or ""
        review_text = row.get("Review") or row.get("review") or row.get("Raw_Review") or ""
        raw_rating = row.get("Rating") or row.get("rating") or ""
        reviewer = row.get("Name") or row.get("name") or "Anonymous"
        date_str = row.get("Date") or row.get("date") or ""

        if not place:
            return

        match = match_place_to_attraction(place, city)
        if not match:
            return

        canonical_id, canonical_name, match_method = match

        try:
            rating = float(raw_rating) if raw_rating else None
        except ValueError:
            rating = None

        sentiment = compute_text_sentiment(review_text)

        matched_reviews.append({
            "canonical_id": canonical_id,
            "canonical_name": canonical_name,
            "original_place": place,
            "city": city,
            "rating": rating,
            "sentiment_score": sentiment,
            "reviewer_name": reviewer,
            "review_date": date_str,
            "review_snippet": review_text[:250].replace("\n", " ") if review_text else "",
            "match_method": match_method,
        })

        if rating is not None:
            attraction_stats[canonical_id]["ratings"].append(rating)
        attraction_stats[canonical_id]["sentiment_scores"].append(sentiment)
        attraction_stats[canonical_id]["canonical_name"] = canonical_name
        attraction_stats[canonical_id]["city"] = city
        if review_text and len(attraction_stats[canonical_id]["reviews"]) < 20:
            attraction_stats[canonical_id]["reviews"].append(review_text[:150])

    if is_zip:
        with zipfile.ZipFile(file_path, "r") as z:
            csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
            for cf in csv_files:
                with z.open(cf) as raw_f:
                    text_f = io.TextIOWrapper(raw_f, encoding="utf-8", errors="ignore")
                    reader = csv.DictReader(text_f)
                    for row in reader:
                        handle_row(row)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                handle_row(row)

    print(f"[+] Total reviews processed: {row_count:,} in {time.time() - t_start:.2f}s")
    return matched_reviews, attraction_stats


def run_pipeline():
    print("=" * 70)
    print("Sustainable Tourism - Visitor Reviews Ingestion & Provenance Pipeline")
    print("Dataset: Indian Places to Visit Reviews Data (Kaggle: ritvik1909)")
    print("=" * 70)

    dataset_loc = locate_reviews_dataset()
    if not dataset_loc:
        print("[!] Dataset file (Review_db.csv or zip) not found in expected locations.")
        print("    Please download the dataset from:")
        print("    https://www.kaggle.com/datasets/ritvik1909/indian-places-to-visit-reviews-data")
        print("    and place 'Review_db.csv' into 'backend/data/raw/'.")
        return False

    path, is_zip = dataset_loc
    print(f"[*] Processing dataset from: {path} (is_zip={is_zip})")

    matched_reviews, stats = process_reviews(path, is_zip)
    print(f"[+] Total reviews matched to Rajasthan attractions: {len(matched_reviews):,}")
    print(f"[+] Unique canonical attractions covered: {len(stats)} / 45")

    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

    # 1. Save detailed reviews
    reviews_csv = os.path.join(DATA_PROCESSED_DIR, "rajasthan_visitor_reviews.csv")
    if matched_reviews:
        with open(reviews_csv, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "canonical_id", "canonical_name", "original_place", "city",
                "rating", "sentiment_score", "reviewer_name", "review_date",
                "review_snippet", "match_method"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matched_reviews)
        print(f"[+] Exported individual reviews to: {reviews_csv}")

    # 2. Save aggregated statistics
    summary_csv = os.path.join(DATA_PROCESSED_DIR, "attraction_reviews_summary.csv")
    summary_rows = []
    for c_id, data in sorted(stats.items()):
        ratings = data["ratings"]
        sentiments = data["sentiment_scores"]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
        avg_sentiment = round(sum(sentiments) / len(sentiments), 3) if sentiments else None
        summary_rows.append({
            "canonical_id": c_id,
            "canonical_name": data["canonical_name"],
            "city": data["city"],
            "review_count": len(sentiments),
            "avg_visitor_rating": avg_rating,
            "avg_sentiment_score": avg_sentiment,
            "rating_std_dev": round(float(pd_std(ratings)), 3) if len(ratings) > 1 else 0.0,
        })

    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "canonical_id", "canonical_name", "city", "review_count",
            "avg_visitor_rating", "avg_sentiment_score", "rating_std_dev"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"[+] Exported aggregated review summary to: {summary_csv}")
    print("[+] Provenance pipeline finished successfully.")
    return True


def pd_std(vals: List[float]) -> float:
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    var = sum((x - mean) ** 2 for x in vals) / (len(vals) - 1)
    return var ** 0.5


if __name__ == "__main__":
    run_pipeline()
