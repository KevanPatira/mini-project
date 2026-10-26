"""
Inspect and Explore the two user-provided datasets:
1. central-zone-261022-free.gpkg/central-zone.gpkg (OSM Central Zone Railway and Transport Network)
2. kaggle_indian_tourist_places_dataset.zip (Kaggle Indian Tourist Places Dataset)
"""

import os
import sys
import sqlite3
import zipfile
import csv
import io
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def explore_tourism_dataset():
    zip_path = os.path.join(BASE_DIR, "kaggle_indian_tourist_places_dataset.zip")
    print("=" * 70)
    print("1. EXPLORING INDIAN TOURIST PLACES DATASET")
    print(f"Path: {zip_path}")
    print("=" * 70)
    
    if not os.path.exists(zip_path):
        print("ERROR: zip file not found!")
        return
        
    with zipfile.ZipFile(zip_path) as z:
        for fname in z.namelist():
            info = z.getinfo(fname)
            print(f"File in zip: {fname} ({info.file_size / (1024*1024):.2f} MB)")
            
            with z.open(fname) as raw_f:
                text_f = io.TextIOWrapper(raw_f, encoding="utf-8", errors="ignore")
                reader = csv.DictReader(text_f)
                headers = reader.fieldnames
                print(f"Total Columns ({len(headers)}):", headers)
                
                rows = list(reader)
                print(f"Total rows: {len(rows)}")
                
                # State distribution
                states = {}
                categories = {}
                for r in rows:
                    st = r.get("state", "Unknown")
                    states[st] = states.get(st, 0) + 1
                    cat = r.get("category", "Unknown")
                    categories[cat] = categories.get(cat, 0) + 1
                    
                print("\nState distribution:")
                for st, count in sorted(states.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {st}: {count}")
                    
                print("\nCategories:")
                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {cat}: {count}")
                    
                # Rajasthan records
                raj_rows = [r for r in rows if r.get("state") == "Rajasthan"]
                print(f"\nRajasthan rows: {len(raj_rows)}")
                raj_places = {}
                for r in raj_rows:
                    p = r.get("place_name", "")
                    if p not in raj_places:
                        raj_places[p] = {
                            "count": 0,
                            "city": r.get("city"),
                            "entry_fee_inr": r.get("entry_fee_inr"),
                            "entry_free": r.get("entry_free"),
                            "visit_duration": r.get("visit_duration"),
                            "crowd_levels": set(),
                            "ratings": [],
                            "coords": (r.get("latitude"), r.get("longitude"))
                        }
                    raj_places[p]["count"] += 1
                    raj_places[p]["crowd_levels"].add(r.get("crowd_level"))
                    try:
                        if r.get("user_rating"):
                            raj_places[p]["ratings"].append(float(r.get("user_rating")))
                    except ValueError:
                        pass
                        
                print("\nRajasthan attractions in dataset:")
                for p, d in raj_places.items():
                    avg_r = sum(d["ratings"]) / len(d["ratings"]) if d["ratings"] else 0
                    print(f"  - {p} ({d['city']}): {d['count']} visits recorded | Fee: INR {d['entry_fee_inr']} | Duration: {d['visit_duration']} | Avg Rating: {avg_r:.2f} | Crowds: {d['crowd_levels']} | Coords: {d['coords']}")

def explore_gpkg_railways():
    gpkg_path = os.path.join(BASE_DIR, "central-zone-261022-free.gpkg", "central-zone.gpkg")
    print("\n" + "=" * 70)
    print("2. EXPLORING CENTRAL ZONE GPKG (RAILWAYS & TRANSPORT)")
    print(f"Path: {gpkg_path}")
    print("=" * 70)
    
    if not os.path.exists(gpkg_path):
        print("ERROR: gpkg file not found!")
        return
        
    conn = sqlite3.connect(gpkg_path)
    cur = conn.cursor()
    
    # Check railway stations
    cur.execute("SELECT fclass, COUNT(*) FROM gis_osm_transport_free GROUP BY fclass")
    print("Transport facilities:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
        
    # Check railway lines
    cur.execute("SELECT fclass, COUNT(*) FROM gis_osm_railways_free GROUP BY fclass")
    print("\nRailway line classes:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
        
    # Check bounding box from gpkg_contents
    cur.execute("SELECT min_x, min_y, max_x, max_y FROM gpkg_contents WHERE table_name='gis_osm_places_free'")
    print("Bounding box (min_lon, min_lat, max_lon, max_lat):", cur.fetchone())

    # Check top cities
    cur.execute("SELECT name FROM gis_osm_places_free WHERE fclass='city' ORDER BY name LIMIT 15")
    print("Cities in GPKG:", [r[0] for r in cur.fetchall()])

if __name__ == "__main__":
    explore_tourism_dataset()
    explore_gpkg_railways()
