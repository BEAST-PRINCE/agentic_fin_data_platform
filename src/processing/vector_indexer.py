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
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

logger = get_logger(__name__)

# Config
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "articles"
EMBEDDING_DIMENSIONS = 384  # all-MiniLM-L6-v2 and bge-small-en-v1.5 both use 384 dims
BATCH_SIZE = 64

def run_indexing(engine: str = 'sentence-transformers'):
    logger.info(f"Starting Vector Indexing Job using {engine}...")
    
    # 1. Initialize Qdrant Client
    logger.info(f"Connecting to Qdrant at {QDRANT_URL}...")
    qdrant = QdrantClient(url=QDRANT_URL)
    
    # 2. Recreate Collection (Full Batch Processing)
    logger.info(f"Recreating collection '{COLLECTION_NAME}' (Full Batch Mode)...")
    if qdrant.collection_exists(COLLECTION_NAME):
        qdrant.delete_collection(COLLECTION_NAME)
        
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIMENSIONS, distance=Distance.COSINE),
    )
    
    # 3. Load Embedder
    logger.info("Loading Embedding Model...")
    embedder = EmbedderFactory.get_embedder(engine=engine, device='cuda')
    logger.info(f"Embedding model loaded on active device: {embedder.device}")
    
    # 4. Fetch Gold Articles
    logger.info("Fetching articles from Gold layer...")
    path = db.get_gold_path("articles_serving")
    # Fetch all records (Full Batch Mode)
    query = f"SELECT article_id, publish_timestamp, source_domain, title, clean_content, extracted_keywords FROM read_parquet('{path}')"
    articles = db.query(query)
    
    total_articles = len(articles)
    logger.info(f"Found {total_articles} articles to index.")
    
    if total_articles == 0:
        logger.info("No articles to process. Exiting.")
        return

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
                        "extracted_keywords": row.get('extracted_keywords', [])
                    }
                )
            )
            
        # Upsert batch
        logger.info(f"Upserting batch {i // BATCH_SIZE + 1} to Qdrant...")
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
    logger.info("Vector Indexing Job Completed Successfully!")

if __name__ == "__main__":
    # The engine is now managed via src.common.config or .env
    # engine = sys.argv[1] if len(sys.argv) > 1 else 'sentence-transformers'
    run_indexing(engine=config.VECTOR_EMBEDDING_ENGINE)
