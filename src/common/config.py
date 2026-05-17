"""
Centralized configuration for the Agentic Datalake project.

Loads settings from .env file and exposes them as module-level constants.
All services (Kafka, MinIO) should import config from here
rather than reading environment variables directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).resolve().parents[2]
load_dotenv(_project_root / ".env")


# =============================================================================
# Kafka Configuration
# =============================================================================
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "raw_news")
RAW_DATA_PATH = os.getenv("RAW_DATA_PATH", "data/raw_data_source/News Dataset.csv")

# =============================================================================
# MinIO Configuration
# =============================================================================
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "password123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Bucket names for the lakehouse layers
MINIO_BRONZE_BUCKET = os.getenv("MINIO_BRONZE_BUCKET", "bronze")
MINIO_SILVER_BUCKET = os.getenv("MINIO_SILVER_BUCKET", "silver")
MINIO_GOLD_BUCKET = os.getenv("MINIO_GOLD_BUCKET", "gold")

# =============================================================================
# Vector & AI Configuration
# =============================================================================
# Options: 'sentence-transformers' (GPU priority) or 'fastembed' (Lightweight fallback)
VECTOR_EMBEDDING_ENGINE = os.getenv("VECTOR_EMBEDDING_ENGINE", "sentence-transformers")
VECTOR_EMBEDDING_MODEL = os.getenv("VECTOR_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
VECTOR_EMBEDDING_DIMENSIONS = int(os.getenv("VECTOR_EMBEDDING_DIMENSIONS", "384"))

# The model used by the AI Agent (e.g. 'ollama/gemma:2b', 'ollama/llama3.2:3b', etc.)
AGENT_MODEL = os.getenv("AGENT_MODEL", "ollama/gemma:2b")
