"""
Destinations & POI Catalog Endpoints
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from app.api.deps import engine
from app.data_ingestion.loader import get_attraction_by_id

router = APIRouter(tags=["Destinations"])


@router.get("/api/destinations")
def list_destinations(
    city: Optional[str] = None,
    category: Optional[str] = None,
):
    """List available destinations with optional filters."""
    filters = {}
    if city:
        filters["city"] = city
    if category:
        filters["category"] = category
    
    destinations = engine.get_all_destinations(filters)
    return {
        "destinations": destinations,
        "total": len(destinations),
        "filters_applied": filters,
    }


@router.get("/api/destinations/{attraction_id}")
def get_destination(attraction_id: str):
    """Get detailed information about a specific destination."""
    attraction = get_attraction_by_id(attraction_id)
    if not attraction:
        raise HTTPException(status_code=404, detail=f"Attraction not found: {attraction_id}")
    return attraction
