import os
import sys
import time
from typing import List, Optional, Dict, Any

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.storage.db_client import db
from src.storage.lakehouse_stats import get_stats
from src.common import config
from src.common.logger import get_logger

logger = get_logger(__name__)

# Simple in-memory caching for expensive datalake aggregations
_stats_cache = {"timestamp": 0, "data": {}}
_throughput_cache = {"timestamp": 0, "data": {}}
CACHE_TTL_SECONDS = 15

# Lazy initialization singletons for Vector DB
_embedder = None
_qdrant = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        from src.processing.embeddings import EmbedderFactory
        _embedder = EmbedderFactory.get_embedder(engine=config.VECTOR_EMBEDDING_ENGINE, device='cuda')
    return _embedder

def _get_qdrant():
    global _qdrant
    if _qdrant is None:
        from qdrant_client import QdrantClient
        _qdrant = QdrantClient(url="http://localhost:6333")
    return _qdrant


def fetch_article_by_id(article_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a specific article's full content and metadata by ID from the Silver layer."""
    db_id = article_id.replace('-', '')
    query = f"""
        SELECT 
            *, 
            published_at as publish_timestamp, 
            regexp_extract(url, 'https?://([^/]+)', 1) as source_domain 
        FROM read_parquet('s3://silver/cleaned_news/**/*.parquet') 
        WHERE article_id = '{db_id}'
    """
    results = db.query(query)
    return results[0] if results else None


def fetch_recent_articles(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """Fetch recent articles."""
    try:
        path = db.get_gold_path("articles_serving")
        query = f"""
            SELECT article_id, title, source_domain, publish_timestamp, source_tags, semantic_keywords 
            FROM read_parquet('{path}')
            ORDER BY publish_timestamp DESC
            LIMIT {limit} OFFSET {offset}
        """
        return db.query(query)
    except Exception as e:
        error_msg = str(e)
        if "No files found" in error_msg or "Timeout was reached" in error_msg:
            return []
        logger.error(f"Failed to fetch recent articles: {e}")
        return []


def semantic_search(query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for articles semantically using Qdrant."""
    start_time = time.time()
    try:
        embedder = _get_embedder()
        qdrant = _get_qdrant()
        
        query_vector = embedder.embed([query_text])[0]
        
        search_results = qdrant.query_points(
            collection_name="articles",
            query=query_vector,
            limit=limit
        ).points
        
        formatted_results = []
        for hit in search_results:
            formatted_results.append({
                "article_id": str(hit.id),
                "score": hit.score,
                "title": hit.payload.get("title"),
                "source_domain": hit.payload.get("source_domain"),
                "publish_timestamp": hit.payload.get("publish_timestamp"),
                "source_tags": hit.payload.get("source_tags", []),
                "semantic_keywords": hit.payload.get("semantic_keywords", [])
            })
            
        # Record Prometheus Metrics
        try:
            from src.serving.core.metrics import VECTOR_SEARCH_REQUESTS, VECTOR_SEARCH_LATENCY
            VECTOR_SEARCH_REQUESTS.inc()
            VECTOR_SEARCH_LATENCY.observe(time.time() - start_time)
        except ImportError:
            pass
            
        return formatted_results
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise


def fetch_daily_trends(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Get the aggregate daily trends."""
    try:
        path = db.get_gold_path("daily_trends")
        query = f"""
            SELECT publish_date, source_domain, category, SUM(total_articles) as total_articles
            FROM read_parquet('{path}')
            WHERE publish_date >= '{start_date}' AND publish_date <= '{end_date}'
            GROUP BY publish_date, source_domain, category
            ORDER BY publish_date DESC, total_articles DESC
        """
        return db.query(query)
    except Exception as e:
        error_msg = str(e)
        if "No files found" in error_msg or "Timeout was reached" in error_msg:
            return []
        logger.error(f"Failed to fetch daily trends: {e}")
        return []


def fetch_top_entities(publish_date: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve the most frequently mentioned entities for a specific date."""
    try:
        path = db.get_gold_path("entity_mentions")
        query = f"""
            SELECT entity_name, entity_type, SUM(mention_count) as total_mentions
            FROM read_parquet('{path}')
            WHERE publish_date = '{publish_date}'
            GROUP BY entity_name, entity_type
            ORDER BY total_mentions DESC
            LIMIT {limit}
        """
        return db.query(query)
    except Exception as e:
        error_msg = str(e)
        if "No files found" in error_msg or "Timeout was reached" in error_msg:
            return []
        logger.error(f"Failed to fetch top entities: {e}")
        return []


def fetch_available_dates() -> List[str]:
    """Get a list of all distinct dates available in the daily trends."""
    try:
        path = db.get_gold_path("daily_trends")
        query = f"SELECT DISTINCT publish_date FROM read_parquet('{path}') ORDER BY publish_date DESC"
        res = db.query(query)
        return [str(row["publish_date"]) for row in res if row.get("publish_date")]
    except Exception as e:
        error_msg = str(e)
        if "No files found" in error_msg or "Timeout was reached" in error_msg:
            return []
        logger.error(f"Failed to fetch available dates: {e}")
        return []

def fetch_system_statistics() -> Dict[str, Any]:
    """
    Retrieve lakehouse record counts from maintained counters in MinIO.
    Results are cached briefly to avoid redundant object reads on dashboard reloads.
    """
    global _stats_cache
    if time.time() - _stats_cache["timestamp"] < CACHE_TTL_SECONDS:
        return _stats_cache["data"]

    try:
        maintained = get_stats()
        stats = {
            "bronze": {"raw_messages": maintained["bronze"]["raw_messages"]},
            "silver": {"cleaned_articles": maintained["silver"]["cleaned_articles"]},
            "gold": {"serving_articles": maintained["gold"]["serving_articles"]},
        }
    except Exception as e:
        logger.warning(f"Failed to read maintained lakehouse stats: {e}")
        stats = {
            "bronze": {"raw_messages": 0},
            "silver": {"cleaned_articles": 0},
            "gold": {"serving_articles": 0},
        }

    _stats_cache["data"] = stats
    _stats_cache["timestamp"] = time.time()
    
    # Update Prometheus Gauges
    try:
        from src.serving.core.metrics import BRONZE_RECORDS, SILVER_RECORDS, GOLD_RECORDS, QDRANT_VECTORS_TOTAL
        BRONZE_RECORDS.set(stats["bronze"]["raw_messages"])
        SILVER_RECORDS.set(stats["silver"]["cleaned_articles"])
        GOLD_RECORDS.set(stats["gold"]["serving_articles"])
        
        # Try fetching Qdrant total vectors
        try:
            qdrant = _get_qdrant()
            info = qdrant.get_collection("articles")
            QDRANT_VECTORS_TOTAL.set(info.points_count)
        except Exception:
            pass
    except ImportError:
        pass
    
    return stats


def fetch_domain_throughput() -> Dict[str, Any]:
    """
    Retrieve the real-time domain throughput counts directly from the JSON tracker in MinIO.
    Results are cached for CACHE_TTL_SECONDS to reduce S3 overhead.
    """
    global _throughput_cache
    if time.time() - _throughput_cache["timestamp"] < CACHE_TTL_SECONDS:
        return _throughput_cache["data"]
        
    try:
        query = "SELECT * FROM read_json_auto('s3://bronze/domain_throughput.json')"
        res = db.query(query)
        if res:
            _throughput_cache["data"] = res[0]
            _throughput_cache["timestamp"] = time.time()
            return res[0]
        return {}
    except Exception as e:
        logger.warning(f"Failed to fetch domain throughput: {e}")
        return {}

