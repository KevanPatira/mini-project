"""
Overpass API client for fetching tourist attractions from OpenStreetMap.

This module queries the Overpass API to extract Points of Interest (POIs)
tagged as tourism, historic, or leisure features within Rajasthan, India.

Data source: OpenStreetMap (ODbL licence)
"""

import requests
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional

from app.config import OVERPASS_API_URL, RAW_DATA_DIR

logger = logging.getLogger(__name__)


# Overpass QL query for Rajasthan tourism POIs
RAJASTHAN_TOURISM_QUERY = """
[out:json][timeout:120];

// Define Rajasthan as the search area
area["name"="Rajasthan"]["admin_level"="4"]->.searchArea;

// Gather tourism POIs
(
  // Tourism attractions
  node["tourism"~"attraction|museum|viewpoint|theme_park|zoo|gallery"](area.searchArea);
  way["tourism"~"attraction|museum|viewpoint|theme_park|zoo|gallery"](area.searchArea);

  // Historic sites (crucial for Rajasthan)
  node["historic"~"monument|castle|fort|palace|archaeological_site|ruins|memorial"](area.searchArea);
  way["historic"~"monument|castle|fort|palace|archaeological_site|ruins|memorial"](area.searchArea);

  // Places of worship (major temples, mosques)
  node["amenity"="place_of_worship"]["tourism"="attraction"](area.searchArea);
  way["amenity"="place_of_worship"]["tourism"="attraction"](area.searchArea);

  // Nature reserves and parks
  node["leisure"="nature_reserve"](area.searchArea);
  way["leisure"="nature_reserve"](area.searchArea);
  relation["leisure"="nature_reserve"](area.searchArea);

  // Protected areas (national parks, wildlife sanctuaries)
  way["boundary"="protected_area"](area.searchArea);
  relation["boundary"="protected_area"](area.searchArea);
);

out body;
>;
out skel qt;
"""


def fetch_rajasthan_pois(save_raw: bool = True) -> Optional[Dict]:
    """
    Fetch Rajasthan tourism POIs from the Overpass API.
    
    Args:
        save_raw: If True, save the raw JSON response to disk.
    
    Returns:
        Raw JSON response dict, or None on failure.
    """
    logger.info("Fetching Rajasthan tourism POIs from Overpass API...")
    
    try:
        response = requests.post(
            OVERPASS_API_URL,
            data={"data": RAJASTHAN_TOURISM_QUERY},
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()
        
        elements = data.get("elements", [])
        logger.info(f"Received {len(elements)} elements from Overpass API")
        
        if save_raw:
            output_path = RAW_DATA_DIR / "osm_rajasthan_pois.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved raw data to {output_path}")
        
        return data
        
    except requests.exceptions.Timeout:
        logger.error("Overpass API request timed out. Try reducing query scope.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Overpass API request failed: {e}")
        return None


def parse_osm_elements(data: Dict) -> List[Dict]:
    """
    Parse raw Overpass API response into structured attraction records.
    
    Extracts name, coordinates, categories, and available metadata from
    OSM elements. Only processes elements with valid names and coordinates.
    """
    if not data or "elements" not in data:
        return []
    
    attractions = []
    seen_names = set()
    
    for element in data["elements"]:
        tags = element.get("tags", {})
        name = tags.get("name") or tags.get("name:en")
        
        if not name:
            continue
        
        # Deduplicate by name (OSM may have node + way for same feature)
        name_lower = name.lower().strip()
        if name_lower in seen_names:
            continue
        seen_names.add(name_lower)
        
        # Get coordinates
        lat = element.get("lat")
        lon = element.get("lon")
        
        # For ways/relations, use center if available
        if lat is None and "center" in element:
            lat = element["center"].get("lat")
            lon = element["center"].get("lon")
        
        if lat is None or lon is None:
            continue
        
        # Extract categories from OSM tags
        categories = _extract_categories(tags)
        
        attraction = {
            "osm_id": f"{element['type']}_{element['id']}",
            "name": name,
            "name_en": tags.get("name:en", name),
            "latitude": lat,
            "longitude": lon,
            "categories": categories,
            "osm_tags": {
                k: v for k, v in tags.items()
                if k in ("tourism", "historic", "amenity", "leisure", "boundary",
                         "religion", "denomination", "heritage", "heritage:operator")
            },
            "opening_hours": tags.get("opening_hours"),
            "fee": tags.get("fee"),
            "website": tags.get("website") or tags.get("url"),
            "wikidata": tags.get("wikidata"),
            "wikipedia": tags.get("wikipedia"),
            "description": tags.get("description"),
        }
        
        attractions.append(attraction)
    
    logger.info(f"Parsed {len(attractions)} unique named attractions from OSM data")
    return attractions


def _extract_categories(tags: Dict[str, str]) -> List[str]:
    """Map OSM tags to our interest categories."""
    categories = set()
    
    tourism = tags.get("tourism", "")
    historic = tags.get("historic", "")
    amenity = tags.get("amenity", "")
    leisure = tags.get("leisure", "")
    boundary = tags.get("boundary", "")
    
    # History and architecture
    if historic in ("monument", "fort", "palace", "castle", "archaeological_site", "ruins", "memorial"):
        categories.add("history")
        if historic in ("fort", "palace", "castle", "monument"):
            categories.add("architecture")
    
    # Culture
    if tourism in ("museum", "gallery"):
        categories.add("culture")
    
    # Nature
    if leisure in ("nature_reserve", "park", "garden"):
        categories.add("nature")
    if boundary == "protected_area":
        categories.add("nature")
        categories.add("wildlife")
    if tourism == "viewpoint":
        categories.add("nature")
    
    # Religion
    if amenity == "place_of_worship":
        categories.add("religion")
        categories.add("culture")
    
    # Adventure / Theme parks
    if tourism in ("theme_park", "water_park"):
        categories.add("adventure")
    
    # Zoo / Wildlife
    if tourism == "zoo":
        categories.add("wildlife")
    
    # Default to culture if no specific match
    if not categories and tourism == "attraction":
        categories.add("culture")
    
    return sorted(categories)
