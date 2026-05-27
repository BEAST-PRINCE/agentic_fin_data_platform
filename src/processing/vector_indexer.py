import os
import sys
import uuid
from typing import List, Dict

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.common import config
from src.common.logger import get_logger
from src.storage.db_client import db
from src.processing.embeddings import EmbedderFactory
from src.storage.minio_client import MinIOClient
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

import json
from pathlib import Path

logger = get_logger(__name__)

import io

# Config
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "articles"
EMBEDDING_DIMENSIONS = config.VECTOR_EMBEDDING_DIMENSIONS
BATCH_SIZE = 64

def get_last_indexed_timestamp() -> str:
    """Retrieve the latest publish_timestamp from the MinIO state tracker."""
    client = MinIOClient()
    client.ensure_bucket_exists("system-logs")
    try:
        response = client.client.get_object("system-logs", "vector_indexer_state.json")
        state = json.loads(response.read().decode('utf-8'))
        response.close()
        response.release_conn()
        return state.get("last_indexed_timestamp", "1970-01-01T00:00:00")
    except Exception as e:
        logger.warning(f"No previous state found in MinIO or error reading state. Falling back to full indexing.")
        return "1970-01-01T00:00:00"

def update_last_indexed_timestamp(timestamp: str):
    """Save the latest publish_timestamp to the MinIO state tracker."""
    client = MinIOClient()
    client.ensure_bucket_exists("system-logs")
    try:
        data = json.dumps({"last_indexed_timestamp": timestamp}, indent=2).encode('utf-8')
        client.upload_stream("system-logs", "vector_indexer_state.json", io.BytesIO(data), len(data))
        logger.info(f"Updated incremental state tracker in MinIO with timestamp: {timestamp}")
    except Exception as e:
        logger.error(f"Failed to save state file to MinIO: {e}")

def run_indexing(engine: str = 'sentence-transformers'):
    logger.info(f"Starting Vector Indexing Job using {engine}...")
    
    # 1. Initialize Qdrant Client
    logger.info(f"Connecting to Qdrant at {QDRANT_URL}...")
    qdrant = QdrantClient(url=QDRANT_URL)
    
    # 2. Check and Create/Maintain Collection
    collection_exists = qdrant.collection_exists(COLLECTION_NAME)
    
    if not collection_exists:
        logger.info(f"Collection '{COLLECTION_NAME}' not found. Creating a fresh collection...")
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIMENSIONS, distance=Distance.COSINE),
        )
        # If the collection doesn't exist (e.g. wiped Qdrant), we force a full rebuild
        last_indexed = "1970-01-01T00:00:00"
    else:
        logger.info(f"Collection '{COLLECTION_NAME}' exists. Running in Incremental Mode...")
        last_indexed = get_last_indexed_timestamp()
    
    # 3. Fetch Gold Articles (Incremental)
    logger.info(f"Fetching articles from Gold layer published after {last_indexed}...")
    path = db.get_gold_path("articles_serving")
    
    # Fetch only newer records
    query = f"""
        SELECT article_id, publish_timestamp, source_domain, title, clean_content, source_tags, semantic_keywords 
        FROM read_parquet('{path}')
        WHERE CAST(publish_timestamp AS VARCHAR) > '{last_indexed}'
    """
    try:
        articles = db.query(query)
    except Exception as e:
        logger.error(f"Failed to query database: {e}")
        return
    
    total_articles = len(articles)
    logger.info(f"Found {total_articles} articles to index.")
    
    if total_articles == 0:
        logger.info("No new articles to process. Exiting.")
        return

    # 4. Load Embedder (Only if there are new articles to process!)
    logger.info("Loading Embedding Model...")
    embedder = EmbedderFactory.get_embedder(engine=engine, device='cuda')
    logger.info(f"Embedding model loaded on active device: {embedder.device}")

    # 5. Process and Upsert in Batches
    for i in range(0, total_articles, BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        
        # Prepare text for embedding (Title + Content)
        texts = [f"{row['title']} - {row['clean_content']}" for row in batch]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for batch {i // BATCH_SIZE + 1} ({len(batch)} articles)...")
        embeddings = embedder.embed(texts)
        
        # Prepare points for Qdrant
        points = []
        for j, row in enumerate(batch):
            points.append(
                PointStruct(
                    id=row['article_id'],  # UUID string is perfectly valid in Qdrant
                    vector=embeddings[j],
                    payload={
                        "title": row['title'],
                        "source_domain": row['source_domain'],
                        "publish_timestamp": str(row['publish_timestamp']),
                        "source_tags": row.get('source_tags', []),
                        "semantic_keywords": row.get('semantic_keywords', [])
                    }
                )
            )
            
        # Upsert batch
        logger.info(f"Upserting batch {i // BATCH_SIZE + 1} to Qdrant...")
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
    
    # 6. Save State (Update last_indexed_timestamp)
    # Find the maximum timestamp in the indexed articles to save as state
    max_timestamp = max(str(row['publish_timestamp']) for row in articles)
    update_last_indexed_timestamp(max_timestamp)
    
    logger.info("Vector Indexing Job Completed Successfully!")

if __name__ == "__main__":
    # The engine is now managed via src.common.config or .env
    # engine = sys.argv[1] if len(sys.argv) > 1 else 'sentence-transformers'
    run_indexing(engine=config.VECTOR_EMBEDDING_ENGINE)
