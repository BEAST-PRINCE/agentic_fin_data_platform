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
from src.serving.core.pipeline_manager import pipeline_manager
from src.common.logger import get_logger

class ChatRequest(BaseModel):
    message: str

logger = get_logger(__name__)

app = FastAPI(
    title="Agentic Datalake API",
    description="External API Serving Layer for the Gold Data",
    version="1.0.0"
)

# Instrument the FastAPI app for Prometheus metrics (HTTP request totals, duration, etc.)
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
async def startup_event():
    """Initialize heavy models on the main thread to avoid PyTorch OpenMP deadlocks in background threads."""
    logger.info("Initializing semantic search embedding model on startup...")
    # This forces the lazy singleton to load in the main thread
    retrieval._get_embedder()
    logger.info("Embedding model initialized.")
    
    from src.common import config
    if config.START_AGENT_ON_BOOT:
        from src.serving.core.agent_manager import agent_manager
        logger.info("START_AGENT_ON_BOOT is true. Initializing Agent Session...")
        await agent_manager.initialize_session()
        logger.info("Agent Session initialized.")
    else:
        logger.info("START_AGENT_ON_BOOT is false. Agent will lazily initialize on first chat.")

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "agentic_datalake_api"}

@app.get("/api/system/statistics", response_model=Dict[str, Any])
def get_system_statistics():
    """
    Retrieve datalake statistics for the dashboard.
    Note: Removed 'async' so FastAPI runs this in a background threadpool, 
    preventing synchronous DuckDB/MinIO calls from blocking the event loop.
    """
    try:
        return retrieval.fetch_system_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/domain-throughput", response_model=Dict[str, Any])
def get_domain_throughput():
    """
    Retrieve real-time domain throughput stats.
    Executes synchronous DuckDB queries in a background threadpool.
    """
    try:
        return retrieval.fetch_domain_throughput()
    except Exception as e:
        logger.error(f"Error fetching domain throughput: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/health", response_model=Dict[str, Any])
def check_system_health():
    """
    Perform health checks on all dependent infrastructure components.
    Executes synchronous socket/HTTP checks in a background threadpool.
    """
    try:
        return health.get_system_health()
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/scrapers", response_model=List[Dict[str, Any]])
def list_scrapers():
    """List all available scrapers and their status in a threadpool."""
    return scraper_manager.list_scrapers()

@app.post("/api/scrapers/{name}/start")
def start_scraper(name: str):
    """Start a scrapy spider."""
    res = scraper_manager.start_scraper(name)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@app.post("/api/scrapers/{name}/stop")
def stop_scraper(name: str):
    """Stop a running scrapy spider."""
    res = scraper_manager.stop_scraper(name)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@app.get("/api/scrapers/{name}/logs")
def get_scraper_logs(name: str):
    """Get the real-time tail of the scraper logs."""
    return {"logs": scraper_manager.get_logs(name)}

# --- Data Pipeline Endpoints ---

@app.get("/api/pipeline/status")
def get_pipeline_status():
    """Get the active status of the data pipeline."""
    return pipeline_manager.get_status()

@app.post("/api/pipeline/run/{stage}")
def run_pipeline_stage(stage: str):
    """Run a specific pipeline stage (silver, gold, indexer)."""
    res = pipeline_manager.run_stage(stage)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@app.post("/api/pipeline/stop")
def stop_pipeline():
    """Stop the currently running pipeline stage."""
    res = pipeline_manager.stop_pipeline()
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@app.get("/api/pipeline/logs")
def get_pipeline_logs(stage: str = Query(None, description="The specific stage to get logs for (silver, gold, indexer)")):
    """Get the live logs of the running pipeline stage."""
    if not stage:
        return {"logs": []}
    return {"logs": pipeline_manager.get_logs(stage)}

@app.get("/articles", response_model=List[Dict[str, Any]])
def get_recent_articles(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Retrieve a list of recently published articles in a threadpool."""
    try:
        return retrieval.fetch_recent_articles(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/articles/{article_id}", response_model=Dict[str, Any])
def get_article_by_id(article_id: str):
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
def semantic_search_articles(
    query: str = Query(..., min_length=3),
    limit: int = Query(10, ge=1, le=50)
):
    """Perform semantic search over the articles using Qdrant Vector DB."""
    try:
        return retrieval.semantic_search(query_text=query, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trending", response_model=List[Dict[str, Any]])
def get_daily_trends(start_date: str, end_date: str):
    """Retrieve aggregate daily trends across sources and categories."""
    try:
        return retrieval.fetch_daily_trends(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/entities", response_model=List[Dict[str, Any]])
def get_top_entities(
    publish_date: str,
    limit: int = Query(10, ge=1, le=100)
):
    """Retrieve top entity mentions (keywords) for a specific date."""
    try:
        return retrieval.fetch_top_entities(publish_date, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trends/dates", response_model=List[str])
def get_available_dates():
    """Get all available dates with trending data."""
    return retrieval.fetch_available_dates()

@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    """Interact with the Datalake Intelligence Agent (solo agent)."""
    try:
        from src.serving.core.agent_manager import agent_manager
        reply = await agent_manager.chat(request.message)
        return {"reply": reply, "agent": "solo"}
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/multi")
async def chat_with_multi_agent(request: ChatRequest):
    """Interact with the multi-agent Financial Intelligence pipeline (independent from solo agent)."""
    try:
        from src.serving.core.multi_agent_manager import multi_agent_manager
        reply = await multi_agent_manager.chat(request.message)
        return {"reply": reply, "agent": "multi"}
    except Exception as e:
        logger.error(f"Multi-agent chat API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
