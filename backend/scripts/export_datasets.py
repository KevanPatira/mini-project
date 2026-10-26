"""
Data Export Utility.

Exports the curated attractions, transport emission factors, and monthly weather
benchmarks to CSV files in backend/data/ for transparency and external analysis.
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.data_ingestion.curated_attractions import RAJASTHAN_ATTRACTIONS
from app.config import EMISSION_FACTORS, SEASONAL_DEMAND_INDEX, ORIGIN_CITIES

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))


def export_all():
    # 1. Attractions CSV
    attractions_path = os.path.join(DATA_DIR, "processed", "attractions_rajasthan.csv")
    records = []
    for a in RAJASTHAN_ATTRACTIONS:
        rec = dict(a)
        rec["categories"] = ";".join(rec["categories"])
        records.append(rec)
    df_att = pd.DataFrame(records)
    df_att.to_csv(attractions_path, index=False)
    print(f"Exported {len(df_att)} attractions to {attractions_path}")

    # 2. Emission Factors CSV
    emissions_path = os.path.join(DATA_DIR, "emissions", "transport_emission_factors.csv")
    emis_records = [
        {
            "transport_mode": mode,
            "emission_factor_g_co2_per_pkm": factor,
            "source": "WRI India / India GHG Program (2023-24)",
            "occupancy_assumption": "National standard average",
        }
        for mode, factor in EMISSION_FACTORS.items()
    ]
    pd.DataFrame(emis_records).to_csv(emissions_path, index=False)
    print(f"Exported emission factors to {emissions_path}")

    # 3. Seasonal Demand & Weather benchmarks CSV
    weather_path = os.path.join(DATA_DIR, "weather", "rajasthan_seasonal_benchmarks.csv")
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    # Climate norms for Rajasthan (composite across Jaipur/Jodhpur/Udaipur)
    avg_max_temps = [22, 26, 32, 38, 41, 40, 34, 32, 33, 33, 29, 24]
    avg_min_temps = [8, 11, 16, 22, 27, 28, 26, 24, 23, 19, 13, 9]
    avg_rain_mm = [7, 5, 4, 3, 12, 55, 210, 220, 75, 12, 4, 3]

    weather_records = []
    for m in range(1, 13):
        weather_records.append({
            "month_num": m,
            "month_name": months[m - 1],
            "seasonal_demand_index": SEASONAL_DEMAND_INDEX[m],
            "avg_max_temp_c": avg_max_temps[m - 1],
            "avg_min_temp_c": avg_min_temps[m - 1],
            "rainfall_mm": avg_rain_mm[m - 1],
            "tourism_season": "Peak" if SEASONAL_DEMAND_INDEX[m] >= 0.8 else ("Moderate" if SEASONAL_DEMAND_INDEX[m] >= 0.4 else "Off-peak"),
            "data_provenance": "Open-Meteo & IMD Historical Norms / Heuristic demand",
        })
    pd.DataFrame(weather_records).to_csv(weather_path, index=False)
    print(f"Exported seasonal benchmarks to {weather_path}")


if __name__ == "__main__":
    export_all()
