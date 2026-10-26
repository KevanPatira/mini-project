"""
Monument Matching and Provenance Pipeline.

Ingests authentic Indian tourism data and transport GIS layers, performs
exact, alias, and fuzzy matching between external monument records and the
canonical 45-attraction Rajasthan catalog, assigns strict provenance classes,
and generates machine-readable mapping registries and audit reports.
"""

import os
import sys
import csv
import io
import json
import zipfile
import sqlite3
import difflib
from typing import Dict, List, Tuple, Any, Optional

from app.data_ingestion.curated_attractions import RAJASTHAN_ATTRACTIONS

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKSPACE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

KAGGLE_ZIP = os.path.join(WORKSPACE_DIR, "kaggle_indian_tourist_places_dataset.zip")
GPKG_FILE = os.path.join(WORKSPACE_DIR, "central-zone-261022-free.gpkg", "central-zone.gpkg")

# Known verified aliases for cultural monuments in Rajasthan
VERIFIED_ALIASES = {
    "amber fort": "raj_001",
    "amer fort": "raj_001",
    "amber palace": "raj_001",
    "hawa mahal": "raj_002",
    "palace of winds": "raj_002",
    "city palace": "raj_003",  # In Jaipur context
    "city palace jaipur": "raj_003",
    "city palace, jaipur": "raj_003",
    "jantar mantar": "raj_004",
    "jantar mantar jaipur": "raj_004",
    "jantar mantar, jaipur": "raj_004",
    "nahargarh": "raj_005",
    "nahargarh fort": "raj_005",
    "jal mahal": "raj_006",
    "water palace": "raj_006",
    "albert hall": "raj_007",
    "albert hall museum": "raj_007",
    "jaigarh fort": "raj_008",
    "jaigarh": "raj_008",
    "birla mandir": "raj_009",
    "laxmi narayan temple": "raj_009",
    "mehrangarh": "raj_010",
    "mehrangarh fort": "raj_010",
    "jaswant thada": "raj_011",
    "umaid bhawan palace": "raj_012",
    "umaid bhawan": "raj_012",
    "mandore gardens": "raj_013",
    "city palace udaipur": "raj_015",
    "city palace, udaipur": "raj_015",
    "lake pichola": "raj_016",
    "pichola lake": "raj_016",
    "saheliyon ki bari": "raj_017",
    "jagdish temple": "raj_018",
    "jaisalmer fort": "raj_021",
    "sonar qila": "raj_021",
    "golden fort": "raj_021",
    "patwon ki haveli": "raj_022",
    "sam sand dunes": "raj_023",
    "junagarh fort": "raj_025",
    "junagarh": "raj_025",
    "karni mata temple": "raj_026",
    "deshnoke rat temple": "raj_026",
    "ajmer sharif dargah": "raj_028",
    "dargah sharif": "raj_028",
    "brahma temple": "raj_029",
    "pushkar brahma temple": "raj_029",
    "pushkar lake": "raj_030",
    "ranthambore national park": "raj_031",
    "ranthambore tiger reserve": "raj_031",
    "chittorgarh fort": "raj_033",
    "chittor fort": "raj_033",
    "bhangarh fort": "raj_035",
    "sariska tiger reserve": "raj_036",
    "sariska": "raj_036",
    "keoladeo national park": "raj_037",
    "bharatpur bird sanctuary": "raj_037",
    "dilwara temples": "raj_041",
    "dilwara jain temples": "raj_041",
    "ranakpur jain temple": "raj_042",
    "ranakpur temple": "raj_042",
}


def normalize_name(name: str) -> str:
    """Normalize string by removing punctuation, extra spaces, and lowercasing."""
    if not name:
        return ""
    cleaned = "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in name)
    return " ".join(cleaned.split())


class MonumentMatcher:
    """Pipeline for ingestion, matching, and provenance recording."""

    def __init__(self):
        self.catalog = RAJASTHAN_ATTRACTIONS
        self.catalog_by_id = {a["id"]: a for a in self.catalog}
        self.normalized_catalog = {normalize_name(a["name"]): a for a in self.catalog}

    def match_name(self, source_name: str, city_hint: Optional[str] = None) -> Tuple[Optional[str], str, float, str]:
        """
        Match a raw name against canonical catalog.
        Returns: (canonical_id, method, confidence, notes)
        """
        norm = normalize_name(source_name)
        if not norm:
            return None, "none", 0.0, "Empty source name"

        # Special city disambiguation: "City Palace" exists in Jaipur (raj_003) and Udaipur (raj_015)
        if norm == "city palace":
            if city_hint and normalize_name(city_hint) == "udaipur":
                return "raj_015", "alias_verified", 0.98, "Disambiguated to City Palace Udaipur via city hint"
            return "raj_003", "alias_verified", 0.98, "Matched City Palace Jaipur via default/alias"

        # 1. Exact match against canonical name
        if norm in self.normalized_catalog:
            return self.normalized_catalog[norm]["id"], "exact", 1.0, "Exact string match with canonical name"

        # 2. Verified alias dictionary match
        if norm in VERIFIED_ALIASES:
            return VERIFIED_ALIASES[norm], "alias_verified", 0.95, f"Matched verified alias '{norm}'"

        # 3. Fuzzy matching against canonical names and aliases
        candidates = []
        for c_norm, item in self.normalized_catalog.items():
            ratio = difflib.SequenceMatcher(None, norm, c_norm).ratio()
            candidates.append((ratio, item["id"], item["name"]))

        for alias, cid in VERIFIED_ALIASES.items():
            ratio = difflib.SequenceMatcher(None, norm, alias).ratio()
            candidates.append((ratio, cid, self.catalog_by_id[cid]["name"]))

        candidates.sort(key=lambda x: x[0], reverse=True)
        best_ratio, best_id, best_name = candidates[0]

        if best_ratio >= 0.82:
            return best_id, "fuzzy_high", round(best_ratio, 3), f"High-confidence fuzzy match to '{best_name}'"
        elif best_ratio >= 0.65:
            return best_id, "fuzzy_low_ambiguous", round(best_ratio, 3), f"Ambiguous fuzzy match to '{best_name}', flagged for manual review"
        else:
            return None, "unmatched", round(best_ratio, 3), "Below similarity threshold"

    def process_kaggle_dataset(self) -> Dict[str, Any]:
        """
        Extract and clean Rajasthan records from Kaggle Indian Tourist Places dataset.
        Generates cleaned dataset and matching registry.
        """
        os.makedirs(DATA_RAW_DIR, exist_ok=True)
        os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

        if not os.path.exists(KAGGLE_ZIP):
            return {"error": f"Dataset zip not found at {KAGGLE_ZIP}"}

        records = []
        with zipfile.ZipFile(KAGGLE_ZIP) as z:
            with z.open("indian_tourist_places_dataset.csv") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="ignore"))
                for row in reader:
                    records.append(row)

        # Raw file backup
        raw_out = os.path.join(DATA_RAW_DIR, "indian_tourist_places_raw.csv")
        if not os.path.exists(raw_out) and records:
            with open(raw_out, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)

        # Match unique places across India
        unique_places = {}
        for r in records:
            key = (r.get("place_name", "").strip(), r.get("city", "").strip(), r.get("state", "").strip())
            if key not in unique_places:
                unique_places[key] = {
                    "count": 0,
                    "rows": [],
                    "place_name": key[0],
                    "city": key[1],
                    "state": key[2],
                    "category": r.get("category"),
                    "lat": r.get("latitude"),
                    "lon": r.get("longitude"),
                }
            unique_places[key]["count"] += 1
            unique_places[key]["rows"].append(r)

        mapping_rows = []
        matched_catalog_ids = set()
        matched_rajasthan_records = []

        for key, p_data in unique_places.items():
            name, city, state = key
            cid, method, conf, notes = self.match_name(name, city_hint=city)

            review_status = "accepted" if conf >= 0.82 else ("needs_review" if conf >= 0.65 else "unmatched")
            provenance = "sourced" if review_status == "accepted" else "unknown"

            canon_name = self.catalog_by_id[cid]["name"] if cid else ""

            mapping_rows.append({
                "source_name": name,
                "source_city": city,
                "source_state": state,
                "visit_records_count": p_data["count"],
                "canonical_attraction_id": cid or "",
                "canonical_name": canon_name,
                "matching_method": method,
                "match_confidence": conf,
                "review_status": review_status,
                "provenance_class": provenance,
                "source_reference": "Kaggle Indian Tourist Places Dataset (2024)",
                "notes": notes,
            })

            if cid and review_status == "accepted":
                matched_catalog_ids.add(cid)
                for r in p_data["rows"]:
                    cleaned_r = dict(r)
                    cleaned_r["canonical_attraction_id"] = cid
                    cleaned_r["canonical_name"] = canon_name
                    cleaned_r["provenance_class"] = "sourced"
                    matched_rajasthan_records.append(cleaned_r)

        # Export mapping registry CSV
        registry_path = os.path.join(DATA_PROCESSED_DIR, "monument_matching_registry.csv")
        fieldnames = [
            "source_name", "source_city", "source_state", "visit_records_count",
            "canonical_attraction_id", "canonical_name", "matching_method",
            "match_confidence", "review_status", "provenance_class",
            "source_reference", "notes"
        ]
        with open(registry_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(mapping_rows)

        # Export cleaned Rajasthan records CSV
        cleaned_path = os.path.join(DATA_PROCESSED_DIR, "cleaned_tourist_places_rajasthan.csv")
        if matched_rajasthan_records:
            with open(cleaned_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=matched_rajasthan_records[0].keys())
                writer.writeheader()
                writer.writerows(matched_rajasthan_records)

        summary = {
            "total_raw_records": len(records),
            "unique_places_india": len(unique_places),
            "total_mappings_generated": len(mapping_rows),
            "accepted_matches": len([m for m in mapping_rows if m["review_status"] == "accepted"]),
            "unmatched_places": len([m for m in mapping_rows if m["review_status"] == "unmatched"]),
            "catalog_coverage_matched": f"{len(matched_catalog_ids)} / {len(self.catalog)} ({len(matched_catalog_ids)/len(self.catalog)*100:.1f}%)",
            "matched_rajasthan_visit_records": len(matched_rajasthan_records),
            "registry_file": registry_path,
            "cleaned_data_file": cleaned_path,
        }

        report_path = os.path.join(DATA_PROCESSED_DIR, "monument_matching_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

    def process_gpkg_transport(self) -> Dict[str, Any]:
        """
        Extract railway and transport infrastructure stations from central-zone.gpkg.
        Exports filtered station dataset for intermodal connectivity.
        """
        os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
        if not os.path.exists(GPKG_FILE):
            return {"error": f"GPKG not found at {GPKG_FILE}"}

        conn = sqlite3.connect(GPKG_FILE)
        cur = conn.cursor()

        # Query all transport features
        cur.execute("SELECT fid, osm_id, fclass, name FROM gis_osm_transport_free WHERE name IS NOT NULL AND name != ''")
        rows = cur.fetchall()

        stations = []
        for r in rows:
            stations.append({
                "fid": r[0],
                "osm_id": r[1],
                "transport_type": r[2],
                "station_name": r[3],
                "provenance_class": "observed",
                "source": "OpenStreetMap Geofabrik Central Zone (2026-10-22)",
            })

        out_path = os.path.join(DATA_PROCESSED_DIR, "central_zone_stations.csv")
        if stations:
            with open(out_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=stations[0].keys())
                writer.writeheader()
                writer.writerows(stations)

        summary = {
            "total_transport_stations_extracted": len(stations),
            "output_file": out_path,
        }
        return summary


def run_pipeline():
    matcher = MonumentMatcher()
    print("Executing Monument Matching & Dataset Cleaning Pipeline...")
    res_kaggle = matcher.process_kaggle_dataset()
    print("Kaggle Processing Result:", json.dumps(res_kaggle, indent=2))
    res_gpkg = matcher.process_gpkg_transport()
    print("GPKG Processing Result:", json.dumps(res_gpkg, indent=2))


if __name__ == "__main__":
    run_pipeline()
