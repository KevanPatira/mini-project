"""
OpenRouteService (ORS) Routing & Directions Client.

Provides live driving routes, turn-by-turn road distances, and travel durations
using the OpenRouteService API (https://openrouteservice.org), with in-memory caching
and automatic, graceful fallback to calibrated 1.30x road circuity estimates.
"""

import logging
import requests
from typing import Dict, List, Tuple, Optional, Any

from app.config import ORS_API_KEY, ORS_BASE_URL
from app.sustainability.scoring import haversine_distance_km

logger = logging.getLogger(__name__)

# In-memory routing cache keyed by rounded (lat1, lon1, lat2, lon2)
_ROUTE_CACHE: Dict[Tuple[float, float, float, float], Dict[str, Any]] = {}


def get_driving_route(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    profile: str = "driving-car",
    timeout_sec: float = 6.0,
) -> Dict[str, Any]:
    """
    Get live driving distance and travel duration between two coordinates.
    
    Args:
        lat1, lon1: Origin coordinates (degrees)
        lat2, lon2: Destination coordinates (degrees)
        profile: ORS routing profile ('driving-car', 'driving-hgv', etc.)
        timeout_sec: Maximum request timeout before falling back to heuristic
        
    Returns:
        dict containing:
            distance_km (float): Road distance in kilometers
            duration_hours (float): Travel duration in hours
            source (str): 'openrouteservice' (live) or 'offline_heuristic' (fallback)
            geometry (list of [lat, lon]): Waypoints polyline if available
    """
    # Round coordinates to ~11 meters precision for robust cache hits
    cache_key = (round(lat1, 4), round(lon1, 4), round(lat2, 4), round(lon2, 4))
    if cache_key in _ROUTE_CACHE:
        return _ROUTE_CACHE[cache_key]

    # Offline fallback computation (calibrated 1.30x Rajasthan road circuity)
    straight_km = haversine_distance_km(lat1, lon1, lat2, lon2)
    heuristic_dist_km = round(straight_km * 1.30, 2)
    # Average driving speed: 30 km/h in urban areas (<30km), 60 km/h on highway
    avg_speed = 30.0 if heuristic_dist_km <= 30.0 else 60.0
    heuristic_hours = round(heuristic_dist_km / avg_speed, 2)

    fallback_result = {
        "distance_km": heuristic_dist_km,
        "duration_hours": heuristic_hours,
        "source": "offline_heuristic",
        "geometry": [[lat1, lon1], [lat2, lon2]],
    }

    # If no API key is provided, return offline estimate immediately
    if not ORS_API_KEY or ORS_API_KEY == "your_ors_api_key_here":
        _ROUTE_CACHE[cache_key] = fallback_result
        return fallback_result

    # If points are identical
    if straight_km < 0.05:
        zero_result = {
            "distance_km": 0.0,
            "duration_hours": 0.0,
            "source": "exact_zero",
            "geometry": [[lat1, lon1], [lat2, lon2]],
        }
        _ROUTE_CACHE[cache_key] = zero_result
        return zero_result

    url = f"{ORS_BASE_URL.rstrip('/')}/v2/directions/{profile}"
    headers = {
        "Authorization": ORS_API_KEY,
        "Accept": "application/json, application/geo+json",
        "Content-Type": "application/json; charset=utf-8",
    }
    # Note: OpenRouteService requires [longitude, latitude] ordering
    # radiuses: [-1, -1] allows snapping off-road / sanctuary coordinates to the nearest road
    body = {
        "coordinates": [
            [lon1, lat1],
            [lon2, lat2],
        ],
        "radiuses": [-1, -1],
    }

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=timeout_sec)
        if resp.status_code == 200:
            data = resp.json()
            routes = data.get("routes", [])
            if routes:
                summary = routes[0].get("summary", {})
                distance_m = summary.get("distance", 0.0)
                duration_s = summary.get("duration", 0.0)
                
                dist_km = round(distance_m / 1000.0, 2)
                dur_h = round(duration_s / 3600.0, 2)
                
                # Extract polyline geometry if present (encoded or coordinates)
                geometry = routes[0].get("geometry")
                # When coordinates are returned in geojson
                geo_coords = []
                if isinstance(geometry, dict) and "coordinates" in geometry:
                    geo_coords = [[pt[1], pt[0]] for pt in geometry["coordinates"]]
                elif not geo_coords:
                    geo_coords = [[lat1, lon1], [lat2, lon2]]

                result = {
                    "distance_km": dist_km,
                    "duration_hours": dur_h,
                    "source": "openrouteservice",
                    "geometry": geo_coords,
                }
                logger.info(
                    f"ORS route ({lat1:.4f},{lon1:.4f} -> {lat2:.4f},{lon2:.4f}): "
                    f"{dist_km} km, {dur_h} h"
                )
                _ROUTE_CACHE[cache_key] = result
                return result
            else:
                logger.warning("ORS returned 200 but no routes in payload; using fallback")
        else:
            logger.warning(
                f"ORS API request failed with status {resp.status_code}: {resp.text[:120]}; "
                f"using calibrated fallback"
            )
    except Exception as e:
        logger.warning(f"ORS connection error ({e}); using calibrated fallback")

    _ROUTE_CACHE[cache_key] = fallback_result
    return fallback_result


def check_ors_status() -> Dict[str, Any]:
    """
    Test connectivity to OpenRouteService API with the configured key.
    """
    has_key = bool(ORS_API_KEY and ORS_API_KEY != "your_ors_api_key_here")
    if not has_key:
        return {
            "status": "unconfigured",
            "provider": "OpenRouteService",
            "message": "ORS_API_KEY is not set or using placeholder.",
            "mode": "offline_heuristic",
        }

    # Perform lightweight probe between Jaipur and Amber Fort
    test_route = get_driving_route(26.9124, 75.7873, 26.9855, 75.8513, timeout_sec=5.0)
    is_live = test_route["source"] == "openrouteservice"
    
    return {
        "status": "connected" if is_live else "error_or_offline",
        "provider": "OpenRouteService",
        "live": is_live,
        "sample_route": {
            "origin": "Jaipur",
            "destination": "Amber Fort",
            "distance_km": test_route["distance_km"],
            "duration_hours": test_route["duration_hours"],
            "source": test_route["source"],
        },
    }

