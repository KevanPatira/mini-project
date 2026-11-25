"""
Transport Routes & Fares Data Ingestion & Cleaning Pipeline.

Processes raw transport datasets from backend/data/raw:
1. Bus Routes in Rajasthan (Bus_Routes_Destination_Rajasthan.csv)
2. Indian Railways schedules & routes (Train_details_22122017.csv + stations.json)
3. Domestic Flight fares & durations (Airlin1/flights.csv)

Outputs processed tables into backend/data/processed:
- processed_bus_routes.csv
- processed_train_routes.csv
- processed_flight_routes.csv
- transport_fare_matrix.json
- transport_summary_metrics.json
"""

import os
import sys
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Standard origin cities supported by the system
ORIGIN_CITIES = {
    "delhi": {"name": "New Delhi", "lat": 28.6139, "lon": 77.2090, "has_airport": True},
    "mumbai": {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "has_airport": True},
    "bangalore": {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946, "has_airport": True},
    "kolkata": {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "has_airport": True},
    "chennai": {"name": "Chennai", "lat": 13.0827, "lon": 80.2707, "has_airport": True},
    "hyderabad": {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "has_airport": True},
    "ahmedabad": {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "has_airport": True},
    "jaipur": {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "has_airport": True},
}

# Key destination hubs in Rajasthan
RAJASTHAN_HUBS = {
    "jaipur": {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "has_airport": True},
    "udaipur": {"name": "Udaipur", "lat": 24.5854, "lon": 73.7125, "has_airport": True},
    "jodhpur": {"name": "Jodhpur", "lat": 26.2389, "lon": 73.0243, "has_airport": True},
    "jaisalmer": {"name": "Jaisalmer", "lat": 26.9157, "lon": 70.9083, "has_airport": False},
    "pushkar": {"name": "Pushkar", "lat": 26.4899, "lon": 74.5542, "has_airport": False},
    "mount_abu": {"name": "Mount Abu", "lat": 24.5926, "lon": 72.7156, "has_airport": False},
    "bikaner": {"name": "Bikaner", "lat": 28.0229, "lon": 73.3119, "has_airport": False},
    "ajmer": {"name": "Ajmer", "lat": 26.4499, "lon": 74.6399, "has_airport": False},
    "ranthambore": {"name": "Ranthambore", "lat": 26.0173, "lon": 76.5026, "has_airport": False},
    "chittorgarh": {"name": "Chittorgarh", "lat": 24.8887, "lon": 74.6269, "has_airport": False},
}

# City aliases for robust name normalization
CITY_ALIASES = {
    "aburoad": "mount_abu",
    "abu road": "mount_abu",
    "abu": "mount_abu",
    "mount abu": "mount_abu",
    "chittor": "chittorgarh",
    "chittorgarh": "chittorgarh",
    "kishangadh": "kishangarh",
    "kishangarh": "kishangarh",
    "beawer": "beawar",
    "beawar": "beawar",
    "sawai madhopur": "ranthambore",
    "swm": "ranthambore",
    "ranthambore": "ranthambore",
    "delhi": "delhi",
    "new delhi": "delhi",
    "dli": "delhi",
    "ndls": "delhi",
    "mumbai": "mumbai",
    "bombay": "mumbai",
    "bangalore": "bangalore",
    "bengaluru": "bangalore",
    "kolkata": "kolkata",
    "calcutta": "kolkata",
    "chennai": "chennai",
    "madras": "chennai",
    "hyderabad": "hyderabad",
    "ahmedabad": "ahmedabad",
    "amdavad": "ahmedabad",
    "jaipur": "jaipur",
    "udaipur": "udaipur",
    "jodhpur": "jodhpur",
    "ajmer": "ajmer",
    "bikaner": "bikaner",
    "jaisalmer": "jaisalmer",
    "pushkar": "pushkar",
    "baroda": "vadodara",
    "himmatnagar": "himatnagar",
}

# Emission factors (kg CO2e per passenger-km)
EMISSION_FACTORS = {
    "train": 0.040,   # Electric/diesel grid average
    "bus": 0.080,     # Inter-city bus
    "car": 0.140,     # Commercial car / taxi
    "flight": 0.255,  # Domestic jet
}


def normalize_city_name(name: str) -> str:
    """Normalize city name using dictionary lookup and string cleanup."""
    if not isinstance(name, str) or not name.strip():
        return ""
    clean = name.strip().lower()
    return CITY_ALIASES.get(clean, clean)


# ─── 1. Bus Data Ingestion ───────────────────────────────────────────────────

def parse_bus_duration(d_str: str) -> float:
    """Parse D:H:M or H:M:S string into decimal hours."""
    if not isinstance(d_str, str):
        return 0.0
    parts = d_str.strip().split(":")
    if len(parts) == 3:
        try:
            d = float(parts[0])
            h = float(parts[1])
            m = float(parts[2])
            return round(d * 24.0 + h + m / 60.0, 2)
        except (ValueError, TypeError):
            return 0.0
    return 0.0


def categorize_bus_type(b_type: str) -> Tuple[str, float]:
    """
    Categorize bus type and return (category_name, tariff_per_km).
    Tariffs based on RSRTC & private operator tariff regulations in Rajasthan:
    - Standard Non-AC: ₹1.25 / km (min ₹40)
    - Express / AC: ₹1.85 / km (min ₹150)
    - Volvo / Luxury Sleeper: ₹2.60 / km (min ₹300)
    """
    if not isinstance(b_type, str):
        return ("Standard Non-AC", 1.25)
    
    t_lower = b_type.lower()
    if "volvo" in t_lower or "multi axle" in t_lower or "b9r" in t_lower:
        return ("Volvo / Multi-Axle AC", 2.60)
    elif "a/c" in t_lower or "ac" in t_lower or "luxury" in t_lower:
        return ("Express AC", 1.85)
    else:
        return ("Standard Non-AC", 1.25)


def process_bus_data() -> pd.DataFrame:
    """Process Rajasthan bus routes, distances, durations, and tariffs."""
    raw_path = RAW_DIR / "Bus_Routes_Destination_Rajasthan.csv"
    if not raw_path.exists():
        logger.warning(f"Bus raw dataset not found at {raw_path}")
        return pd.DataFrame()

    logger.info("Processing Bus_Routes_Destination_Rajasthan.csv...")
    df = pd.read_csv(raw_path)

    # Normalize fields
    df["from_clean"] = df["From"].apply(normalize_city_name)
    df["to_clean"] = df["To"].apply(normalize_city_name)
    df["duration_hours"] = df["Duration"].apply(parse_bus_duration)
    
    # Filter valid distances and durations
    df = df[(df["Distance"] > 0) & (df["Distance"] <= 3000)].copy()
    # If duration is 0 or unparsed, approximate with 45 km/h
    mask_zero_dur = (df["duration_hours"] <= 0) | (df["duration_hours"] > 50)
    df.loc[mask_zero_dur, "duration_hours"] = (df.loc[mask_zero_dur, "Distance"] / 45.0).round(2)

    # Calculate fare per bus trip
    bus_meta = df["Bus Type"].apply(categorize_bus_type)
    df["bus_category"] = [m[0] for m in bus_meta]
    df["rate_per_km"] = [m[1] for m in bus_meta]
    
    # Compute fare with minimum floor
    def _compute_bus_fare(row):
        base = row["Distance"] * row["rate_per_km"]
        min_floor = 300.0 if "Volvo" in row["bus_category"] else (150.0 if "AC" in row["bus_category"] else 40.0)
        return round(max(min_floor, base), 1)

    df["fare_inr"] = df.apply(_compute_bus_fare, axis=1)

    # Save cleaned per-trip bus table
    output_path = PROCESSED_DIR / "processed_bus_routes.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} cleaned bus routes to {output_path}")

    # Aggregate by (from_clean, to_clean)
    agg_df = df.groupby(["from_clean", "to_clean"]).agg(
        trips_count=("Distance", "count"),
        median_distance_km=("Distance", "median"),
        median_duration_hours=("duration_hours", "median"),
        mean_fare_inr=("fare_inr", "mean"),
        min_fare_inr=("fare_inr", "min"),
        max_fare_inr=("fare_inr", "max"),
        operators=("Operator", lambda s: ", ".join(s.value_counts().head(3).index.tolist())),
    ).reset_index()

    agg_df["mean_fare_inr"] = agg_df["mean_fare_inr"].round(1)
    return agg_df


# ─── 2. Train Data Ingestion ─────────────────────────────────────────────────

def process_train_data() -> pd.DataFrame:
    """Process Indian Railways schedules to find real rail links to Rajasthan."""
    raw_csv = RAW_DIR / "Train_details_22122017.csv"
    if not raw_csv.exists():
        logger.warning(f"Train raw dataset not found at {raw_csv}")
        return pd.DataFrame()

    logger.info("Processing Train_details_22122017.csv (this may take a few seconds)...")
    df = pd.read_csv(
        raw_csv,
        usecols=["Train No", "Train Name", "SEQ", "Station Code", "Station Name", "Distance"],
        low_memory=False,
    )

    # Clean numeric fields
    df["Distance"] = pd.to_numeric(df["Distance"], errors="coerce").fillna(0)
    df["SEQ"] = pd.to_numeric(df["SEQ"], errors="coerce").fillna(0)
    df["Station Code"] = df["Station Code"].astype(str).str.strip().str.upper()

    # Station codes mapping
    origin_station_map = {
        "delhi": ["NDLS", "DLI", "NZM", "DEC", "ANVT", "DEE"],
        "mumbai": ["BSR", "BDTS", "CSMT", "MMCT", "KYN", "DR", "LTT"],
        "bangalore": ["SBC", "YPR", "BNC", "SMVB"],
        "kolkata": ["HWH", "SDAH", "KOAA", "SHM"],
        "chennai": ["MAS", "MS", "PER", "TBM"],
        "hyderabad": ["HYB", "SC", "KCG"],
        "ahmedabad": ["ADI", "SBIB", "SBT", "MAN"],
        "jaipur": ["JP", "GADJ", "DPA"],
    }

    dest_station_map = {
        "jaipur": ["JP", "GADJ", "DPA"],
        "udaipur": ["UDZ", "RPZ"],
        "jodhpur": ["JU", "BGKT", "RKB"],
        "jaisalmer": ["JSM"],
        "bikaner": ["BKN", "LGH"],
        "ajmer": ["AII", "MDJN"],
        "pushkar": ["PUHT", "AII"],
        "mount_abu": ["ABR"],
        "ranthambore": ["SWM"],
        "chittorgarh": ["COR"],
    }

    rail_records = []

    for orig_name, orig_codes in origin_station_map.items():
        o_df = df[df["Station Code"].isin(orig_codes)]
        if o_df.empty:
            continue
        o_train_set = set(o_df["Train No"].unique())

        for dest_name, dest_codes in dest_station_map.items():
            if orig_name == dest_name:
                continue
            d_df = df[df["Station Code"].isin(dest_codes)]
            if d_df.empty:
                continue
            d_train_set = set(d_df["Train No"].unique())

            common_trains = o_train_set.intersection(d_train_set)
            if not common_trains:
                continue

            pair_dists = []
            for t_no in list(common_trains)[:25]:
                sub = df[df["Train No"] == t_no].sort_values("SEQ")
                s_orig = sub[sub["Station Code"].isin(orig_codes)]
                s_dest = sub[sub["Station Code"].isin(dest_codes)]
                if not s_orig.empty and not s_dest.empty:
                    d_val = abs(float(s_dest.iloc[0]["Distance"]) - float(s_orig.iloc[0]["Distance"]))
                    if d_val > 5:
                        pair_dists.append(d_val)

            if pair_dists:
                med_dist = round(float(np.median(pair_dists)), 1)
                # Indian Railways average express train speed is ~55 km/h including stops
                est_duration = round(med_dist / 55.0, 2)
                
                # Indian Railways standard telescopic distance fares:
                # Sleeper (SL): ₹140 base + ~₹0.58/km
                # 3-Tier AC (3A): ₹495 base + ~₹1.50/km
                # 2-Tier AC (2A): ₹710 base + ~₹2.20/km
                fare_sl = round(140.0 + max(0.0, med_dist - 100.0) * 0.58, 1)
                fare_3a = round(495.0 + max(0.0, med_dist - 100.0) * 1.50, 1)
                fare_2a = round(710.0 + max(0.0, med_dist - 100.0) * 2.20, 1)
                # Weighted tourist blended train fare (0.4 SL + 0.6 3A)
                blended_fare = round(0.40 * fare_sl + 0.60 * fare_3a, 1)

                rail_records.append({
                    "origin": orig_name,
                    "destination": dest_name,
                    "direct_trains_count": len(common_trains),
                    "rail_distance_km": med_dist,
                    "scheduled_hours": est_duration,
                    "fare_sleeper_inr": fare_sl,
                    "fare_3ac_inr": fare_3a,
                    "fare_2ac_inr": fare_2a,
                    "blended_fare_inr": blended_fare,
                    "co2_emissions_kg": round(med_dist * EMISSION_FACTORS["train"], 2),
                })

    rail_df = pd.DataFrame(rail_records)
    out_csv = PROCESSED_DIR / "processed_train_routes.csv"
    rail_df.to_csv(out_csv, index=False)
    logger.info(f"Saved {len(rail_df)} direct rail connections to {out_csv}")
    return rail_df


# ─── 3. Flight Data Ingestion ────────────────────────────────────────────────

def parse_flight_duration(d_str: str) -> float:
    """Parse '2h 15min' or '14h 30m' string into decimal flight hours."""
    if not isinstance(d_str, str):
        return 0.0
    h_match = re.search(r"(\d+)\s*h", d_str)
    m_match = re.search(r"(\d+)\s*m", d_str)
    h = float(h_match.group(1)) if h_match else 0.0
    m = float(m_match.group(1)) if m_match else 0.0
    return round(h + m / 60.0, 2)


def process_flight_data() -> pd.DataFrame:
    """Process domestic flight dataset for routes into Rajasthan."""
    raw_path = RAW_DIR / "Airlin1" / "flights.csv"
    if not raw_path.exists():
        logger.warning(f"Flight raw dataset not found at {raw_path}")
        return pd.DataFrame()

    logger.info("Processing Airlin1/flights.csv...")
    df = pd.read_csv(raw_path)

    df["src_clean"] = df["Source"].apply(normalize_city_name)
    df["dest_clean"] = df["destination"].apply(normalize_city_name)
    df["duration_hours"] = df["Duration"].apply(parse_flight_duration)

    # Filter flights connecting to Jaipur
    jp_flights = df[(df["dest_clean"] == "jaipur") & (df["src_clean"].isin(ORIGIN_CITIES.keys()))].copy()

    # Aggregate by source city
    agg_df = jp_flights.groupby("src_clean").agg(
        flight_samples_count=("Price", "count"),
        median_price_inr=("Price", "median"),
        mean_price_inr=("Price", "mean"),
        min_price_inr=("Price", "min"),
        max_price_inr=("Price", "max"),
        median_flight_duration_h=("duration_hours", "median"),
        top_airlines=("airline", lambda s: ", ".join(s.value_counts().head(3).index.tolist())),
    ).reset_index()

    agg_df = agg_df.rename(columns={"src_clean": "origin"})
    agg_df["destination"] = "jaipur"
    agg_df["mean_price_inr"] = agg_df["mean_price_inr"].round(1)
    agg_df["total_travel_hours"] = (agg_df["median_flight_duration_h"] + 2.0).round(2)  # airport buffer

    out_csv = PROCESSED_DIR / "processed_flight_routes.csv"
    agg_df.to_csv(out_csv, index=False)
    logger.info(f"Saved {len(agg_df)} flight routes to {out_csv}")
    return agg_df


# ─── 4. Build Unified Transport Fare Matrix ──────────────────────────────────

def build_transport_matrix(bus_agg: pd.DataFrame, rail_df: pd.DataFrame, flight_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Construct comprehensive lookup matrix covering (origin, destination, mode).
    Provides exact empirical metrics with robust calibrated fallbacks.
    """
    matrix: Dict[str, Dict[str, Any]] = {}

    # 1. Bus Entries
    if not bus_agg.empty:
        for _, r in bus_agg.iterrows():
            f_city = r["from_clean"]
            t_city = r["to_clean"]
            key = f"{f_city}__{t_city}__bus"
            dist = float(r["median_distance_km"])
            dur = float(r["median_duration_hours"])
            fare = float(r["mean_fare_inr"])
            matrix[key] = {
                "origin": f_city,
                "destination": t_city,
                "mode": "bus",
                "distance_km": dist,
                "duration_hours": dur,
                "fare_inr": fare,
                "min_fare_inr": float(r["min_fare_inr"]),
                "co2_emissions_kg": round(dist * EMISSION_FACTORS["bus"], 2),
                "frequency_daily": int(r["trips_count"]),
                "data_source": "empirical_rajasthan_bus_routes",
            }

    # 2. Rail Entries
    if not rail_df.empty:
        for _, r in rail_df.iterrows():
            f_city = r["origin"]
            t_city = r["destination"]
            key = f"{f_city}__{t_city}__train"
            dist = float(r["rail_distance_km"])
            dur = float(r["scheduled_hours"])
            fare = float(r["blended_fare_inr"])
            matrix[key] = {
                "origin": f_city,
                "destination": t_city,
                "mode": "train",
                "distance_km": dist,
                "duration_hours": dur,
                "fare_inr": fare,
                "fare_sleeper_inr": float(r["fare_sleeper_inr"]),
                "fare_3ac_inr": float(r["fare_3ac_inr"]),
                "co2_emissions_kg": round(dist * EMISSION_FACTORS["train"], 2),
                "frequency_daily": int(r["direct_trains_count"]),
                "data_source": "empirical_indian_railways_schedule",
            }

    # 3. Flight Entries
    if not flight_df.empty:
        for _, r in flight_df.iterrows():
            f_city = r["origin"]
            t_city = r["destination"]
            key = f"{f_city}__{t_city}__flight"
            # Estimate straight-line flight distance
            o_coord = ORIGIN_CITIES.get(f_city, {})
            d_coord = RAJASTHAN_HUBS.get(t_city, {})
            if o_coord and d_coord:
                from app.sustainability.scoring import haversine_distance_km
                f_dist = round(haversine_distance_km(o_coord["lat"], o_coord["lon"], d_coord["lat"], d_coord["lon"]) * 1.1, 1)
            else:
                f_dist = 500.0

            dur = float(r["total_travel_hours"])
            fare = float(r["median_price_inr"])
            matrix[key] = {
                "origin": f_city,
                "destination": t_city,
                "mode": "flight",
                "distance_km": f_dist,
                "duration_hours": dur,
                "fare_inr": fare,
                "min_budget_fare_inr": float(r["min_price_inr"]),
                "co2_emissions_kg": round(f_dist * EMISSION_FACTORS["flight"], 2),
                "frequency_daily": int(r["flight_samples_count"]),
                "data_source": "empirical_flight_dataset",
            }

    # 4. Save JSON Matrix
    out_json = PROCESSED_DIR / "transport_fare_matrix.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2)
    logger.info(f"Saved consolidated transport fare matrix with {len(matrix)} entries to {out_json}")

    # Summary Metrics
    summary = {
        "total_od_pairs_in_matrix": len(matrix),
        "bus_routes_count": len([k for k in matrix if k.endswith("__bus")]),
        "train_routes_count": len([k for k in matrix if k.endswith("__train")]),
        "flight_routes_count": len([k for k in matrix if k.endswith("__flight")]),
        "calibrated_tariffs_inr_per_km": {
            "bus_standard": 1.25,
            "bus_volvo_ac": 2.60,
            "train_sleeper": 0.58,
            "train_3ac": 1.50,
            "car_outstation": 12.00,
            "car_intracity": 14.00,
        },
    }
    with open(PROCESSED_DIR / "transport_summary_metrics.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return matrix


def run_pipeline():
    """Run the complete transport routes and fares ingestion pipeline."""
    logger.info("=== Starting Transport Routes & Fares Ingestion Pipeline ===")
    bus_agg = process_bus_data()
    rail_df = process_train_data()
    flight_df = process_flight_data()
    matrix = build_transport_matrix(bus_agg, rail_df, flight_df)
    logger.info(f"=== Pipeline completed successfully! Total OD entries: {len(matrix)} ===")


if __name__ == "__main__":
    run_pipeline()
