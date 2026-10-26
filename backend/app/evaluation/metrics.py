"""
Evaluation Metrics Module.

Implements academic and quantitative evaluation metrics for the tourism recommendation system:
- Category Match Rate (CMR@K)
- Category Diversity (CD@K)
- Total Estimated Emissions (TEE)
- Popularity Gini Coefficient
- Geographic Spread (mean pairwise distance)
- Kendall's Tau Rank Correlation
- Top-K Overlap (Jaccard similarity)
"""

from typing import List, Dict, Set, Tuple
import numpy as np
from app.sustainability.scoring import haversine_distance_km


def compute_cmr_at_k(recommendations: List[Dict], user_interests: List[str]) -> float:
    """
    Category Match Rate (CMR@K): Fraction of top-K recommendations that
    share at least one interest category with the user.
    """
    if not recommendations:
        return 0.0
    user_set = set(i.lower() for i in user_interests)
    matches = 0
    for r in recommendations:
        att = r.get("attraction", r)
        cats = set(c.lower() for c in att.get("categories", []))
        if user_set.intersection(cats):
            matches += 1
    return round(matches / len(recommendations), 4)


def compute_category_diversity_at_k(recommendations: List[Dict]) -> int:
    """
    Category Diversity (CD@K): Number of distinct categories represented in top-K.
    """
    all_cats = set()
    for r in recommendations:
        att = r.get("attraction", r)
        for c in att.get("categories", []):
            all_cats.add(c.lower())
    return len(all_cats)


def compute_total_emissions(recommendations: List[Dict]) -> float:
    """
    Total Estimated Emissions (TEE) in kg CO2e for the recommended items.
    """
    total = sum(r.get("estimated_emissions_kg", 0.0) or 0.0 for r in recommendations)
    return round(total, 2)


def compute_gini_coefficient(values: List[float]) -> float:
    """
    Compute Gini coefficient of a distribution (e.g. popularity concentration).
    0 = perfect equality, 1 = complete inequality.
    """
    if not values:
        return 0.0
    array = np.array(values, dtype=np.float64)
    if np.amin(array) < 0:
        array -= np.amin(array)  # Shift to non-negative
    array += 1e-7  # Avoid division by zero
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return round(float((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array))), 4)


def compute_geographic_spread(recommendations: List[Dict]) -> float:
    """
    Geographic Spread: Average pairwise distance between recommended destinations (km).
    """
    if len(recommendations) < 2:
        return 0.0
    coords = []
    for r in recommendations:
        att = r.get("attraction", r)
        coords.append((att["latitude"], att["longitude"]))

    distances = []
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            d = haversine_distance_km(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            distances.append(d)

    return round(float(np.mean(distances)), 2) if distances else 0.0


def compute_unique_districts(recommendations: List[Dict]) -> int:
    """Number of distinct districts or cities in recommendations."""
    districts = set()
    for r in recommendations:
        att = r.get("attraction", r)
        dist = att.get("district") or att.get("city")
        if dist:
            districts.add(dist.lower())
    return len(districts)


def compute_jaccard_overlap(list_a: List[str], list_b: List[str]) -> float:
    """Jaccard similarity between two lists of attraction IDs."""
    set_a = set(list_a)
    set_b = set(list_b)
    if not set_a and not set_b:
        return 1.0
    union = set_a.union(set_b)
    if not union:
        return 0.0
    return round(len(set_a.intersection(set_b)) / len(union), 4)


def compute_kendall_tau(ranked_a: List[str], ranked_b: List[str]) -> float:
    """
    Compute Kendall's Tau rank correlation for items present in both rankings.
    """
    common = [item for item in ranked_a if item in ranked_b]
    if len(common) < 2:
        return 0.0

    rank_dict_b = {item: idx for idx, item in enumerate(ranked_b)}
    b_ranks = [rank_dict_b[item] for item in common]

    concordant = 0
    discordant = 0
    n = len(common)

    for i in range(n):
        for j in range(i + 1, n):
            if (b_ranks[i] < b_ranks[j]):
                concordant += 1
            elif (b_ranks[i] > b_ranks[j]):
                discordant += 1

    total_pairs = n * (n - 1) / 2
    if total_pairs == 0:
        return 1.0
    return round((concordant - discordant) / total_pairs, 4)


def compute_catalog_coverage(all_recommendations: List[List[Dict]], total_catalog_size: int = 45) -> float:
    """
    Catalog Coverage: Fraction of all available attractions recommended at least once
    across a set of recommendation runs (e.g., across all test personas).
    Measures macro-level catalog exploration vs severe concentration.
    """
    if total_catalog_size <= 0:
        return 0.0
    recommended_ids = set()
    for rec_list in all_recommendations:
        for r in rec_list:
            att = r.get("attraction", r)
            if isinstance(att, dict) and "id" in att:
                recommended_ids.add(att["id"])
    return round(len(recommended_ids) / total_catalog_size, 4)

