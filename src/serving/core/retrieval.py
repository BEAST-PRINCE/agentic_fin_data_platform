import os
import sys
from typing import List, Optional, Dict, Any

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.storage.db_client import db
from src.common import config
from src.common.logger import get_logger

logger = get_logger(__name__)

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
    path = db.get_gold_path("articles_serving")
    query = f"""
        SELECT article_id, title, source_domain, publish_timestamp, extracted_keywords 
        FROM read_parquet('{path}')
        ORDER BY publish_timestamp DESC
        LIMIT {limit} OFFSET {offset}
    """
    return db.query(query)


def semantic_search(query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for articles semantically using Qdrant."""
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
                "extracted_keywords": hit.payload.get("extracted_keywords", [])
            })
            
        return formatted_results
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise


def fetch_daily_trends(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Get the aggregate daily trends."""
    path = db.get_gold_path("daily_trends")
    query = f"""
        SELECT publish_date, source_domain, category, SUM(total_articles) as total_articles
        FROM read_parquet('{path}')
        WHERE publish_date >= '{start_date}' AND publish_date <= '{end_date}'
        GROUP BY publish_date, source_domain, category
        ORDER BY publish_date DESC, total_articles DESC
    """
    return db.query(query)


def fetch_top_entities(publish_date: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve the most frequently mentioned entities for a specific date."""
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


def fetch_system_statistics() -> Dict[str, Any]:
    """Retrieve dynamic file and record counts across the Bronze, Silver, and Gold layers."""
    stats = {
        "bronze": {"raw_messages": 0},
        "silver": {"cleaned_articles": 0},
        "gold": {"serving_articles": 0}
    }
    
    try:
        # Bronze JSON Count
        query = "SELECT count(*) as total FROM read_json_auto('s3://bronze/raw_news/**/*.json')"
        res = db.query(query)
        stats["bronze"]["raw_messages"] = res[0]["total"] if res else 0
    except Exception as e:
        logger.warning(f"Failed to fetch bronze stats: {e}")

    try:
        # Silver Parquet Count
        query = "SELECT count(*) as total FROM read_parquet('s3://silver/cleaned_news/**/*.parquet')"
        res = db.query(query)
        stats["silver"]["cleaned_articles"] = res[0]["total"] if res else 0
    except Exception as e:
        logger.warning(f"Failed to fetch silver stats: {e}")
        
    try:
        # Gold Parquet Count
        gold_path = db.get_gold_path("articles_serving")
        query = f"SELECT count(*) as total FROM read_parquet('{gold_path}')"
        res = db.query(query)
        stats["gold"]["serving_articles"] = res[0]["total"] if res else 0
    except Exception as e:
        logger.warning(f"Failed to fetch gold stats: {e}")
        
    return stats


def fetch_domain_throughput() -> Dict[str, Any]:
    """Retrieve the real-time domain throughput counts directly from the JSON tracker in MinIO."""
    try:
        query = "SELECT * FROM read_json_auto('s3://bronze/domain_throughput.json')"
        res = db.query(query)
        if res:
            return res[0]
        return {}
    except Exception as e:
        logger.warning(f"Failed to fetch domain throughput: {e}")
        return {}

