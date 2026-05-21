# pyrefly: ignore [missing-import]
import os
import sys

# Ensure project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from src.serving.core import retrieval, health
from src.serving.core.scraper_manager import scraper_manager
from src.common.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Agentic Datalake API",
    description="External API Serving Layer for the Gold Data",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "agentic_datalake_api"}

@app.get("/api/system/statistics", response_model=Dict[str, Any])
async def get_system_statistics():
    """Retrieve datalake statistics for the dashboard."""
    try:
        return retrieval.fetch_system_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/domain-throughput", response_model=Dict[str, Any])
async def get_domain_throughput():
    """Retrieve real-time domain throughput stats."""
    try:
        return retrieval.fetch_domain_throughput()
    except Exception as e:
        logger.error(f"Error fetching domain throughput: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/health", response_model=Dict[str, Any])
async def check_system_health():
    """Perform health checks on all dependent infrastructure components."""
    try:
        return health.get_system_health()
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/scrapers", response_model=List[Dict[str, Any]])
async def list_scrapers():
    """List all available scrapers and their status."""
    return scraper_manager.list_scrapers()

@app.post("/api/scrapers/{name}/start")
async def start_scraper(name: str):
    """Start a scrapy spider."""
    res = scraper_manager.start_scraper(name)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@app.post("/api/scrapers/{name}/stop")
async def stop_scraper(name: str):
    """Stop a running scrapy spider."""
    res = scraper_manager.stop_scraper(name)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@app.get("/api/scrapers/{name}/logs")
async def get_scraper_logs(name: str):
    """Get the real-time tail of the scraper logs."""
    return {"logs": scraper_manager.get_logs(name)}

@app.get("/articles", response_model=List[Dict[str, Any]])
async def get_recent_articles(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Retrieve a list of recently published articles."""
    try:
        return retrieval.fetch_recent_articles(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/articles/{article_id}", response_model=Dict[str, Any])
async def get_article_by_id(article_id: str):
    """Retrieve a single article by its unique ID."""
    try:
        article = retrieval.fetch_article_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return article
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search", response_model=List[Dict[str, Any]])
async def semantic_search_articles(
    query: str = Query(..., min_length=3),
    limit: int = Query(10, ge=1, le=50)
):
    """Perform semantic search over the articles using Qdrant Vector DB."""
    try:
        return retrieval.semantic_search(query_text=query, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trending", response_model=List[Dict[str, Any]])
async def get_daily_trends(start_date: str, end_date: str):
    """Retrieve aggregate daily trends across sources and categories."""
    try:
        return retrieval.fetch_daily_trends(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/entities", response_model=List[Dict[str, Any]])
async def get_top_entities(
    publish_date: str,
    limit: int = Query(10, ge=1, le=100)
):
    """Retrieve top entity mentions (keywords) for a specific date."""
    try:
        return retrieval.fetch_top_entities(publish_date, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
