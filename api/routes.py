from fastapi import APIRouter, HTTPException, Query
from models.embedding_model import SearchQuery
from api.search_service import process_search
import json, os

router = APIRouter()

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw_events.json')


@router.post("/search")
def search_events(query: SearchQuery):
    """
    Semantic search endpoint.
    Returns vector-matched hackathons.
    """
    try:
        results = process_search(query.text, query.limit)

        return {
            "status": "success",
            "query": query.text,
            "results": results,
            "llm_summary": None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
def browse_events(
    limit: int = Query(default=20, le=100),
    skip: int = Query(default=0, ge=0),
):
    """
    Browse all raw hackathon events (no search).
    Supports pagination via limit/skip.
    """
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            events = json.load(f)
        paginated = events[skip: skip + limit]
        return {
            "status": "success",
            "total": len(events),
            "skip": skip,
            "limit": limit,
            "results": paginated,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Event database not found. Run the uploader first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explore")
def explore_events(
    limit: int = Query(default=9, le=50),
    page: int = Query(default=1, ge=1),
):
    """
    Returns a stable, paginated list of all hackathons.
    """
    try:
        from database.qdrant_db import get_all_points
        
        # 1. Fetch points (capped at 500 for performance, enough for "max no" currently)
        all_hits = get_all_points(limit=500)
        
        # 2. Extract payload and score
        results = []
        for hit in all_hits:
            payload = hit.payload
            results.append({
                "title": payload.get("title"),
                "date": payload.get("date"),
                "location": payload.get("location"),
                "fee": payload.get("fee"),
                "prize": payload.get("prize"),
                "registration_url": payload.get("registration_url"),
                "visit_url": payload.get("visit_url"),
                "domains": payload.get("domains", []),
                "description": payload.get("clean_description"),
                "score": 1.0
            })

        # 3. Paginate (Stable order without shuffle)
        total = len(results)
        start = (page - 1) * limit
        end = start + limit
        paginated_results = results[start:end]
        
        return {
            "status": "success",
            "total": total,
            "page": page,
            "limit": limit,
            "results": paginated_results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health_check():
    """Quick health check — confirms API status."""
    return {
        "api": "online",
    }