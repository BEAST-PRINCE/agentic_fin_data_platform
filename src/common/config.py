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
# Unified topic for scraping ingestion (KAFKA_RAW_TOPIC kept as backward-compatible alias)
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC") or os.getenv("KAFKA_RAW_TOPIC", "raw_financial_news")
KAFKA_DLQ_TOPIC = os.getenv("KAFKA_DLQ_TOPIC", f"{KAFKA_TOPIC}_dlq")
KAFKA_DLQ_ENABLED = os.getenv("KAFKA_DLQ_ENABLED", "true").lower() == "true"
KAFKA_BRONZE_CONSUMER_GROUP = os.getenv("KAFKA_BRONZE_CONSUMER_GROUP", "bronze-ingestion-group")

# Comma-separated bronze source= partition values for incremental silver (empty = all sources)
SILVER_BRONZE_SOURCES = os.getenv("SILVER_BRONZE_SOURCES", "")


def get_silver_bronze_sources() -> list[str]:
    """Parse SILVER_BRONZE_SOURCES into partition-safe source names."""
    if not SILVER_BRONZE_SOURCES.strip():
        return []
    return [s.strip().lower().replace(" ", "_") for s in SILVER_BRONZE_SOURCES.split(",") if s.strip()]

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
LLM_MODE = os.getenv("LLM_MODE", "local")

# HuggingFace Auth Token
HF_TOKEN = os.getenv("HF_TOKEN", "")

# =============================================================================
# Health Check Configuration
# =============================================================================
HEALTH_CHECK_ENABLE_MINIO = os.getenv("HEALTH_CHECK_ENABLE_MINIO", "true").lower() == "true"
HEALTH_CHECK_ENABLE_KAFKA = os.getenv("HEALTH_CHECK_ENABLE_KAFKA", "true").lower() == "true"
HEALTH_CHECK_ENABLE_QDRANT = os.getenv("HEALTH_CHECK_ENABLE_QDRANT", "true").lower() == "true"
HEALTH_CHECK_ENABLE_DUCKDB = os.getenv("HEALTH_CHECK_ENABLE_DUCKDB", "true").lower() == "true"
HEALTH_CHECK_ENABLE_OLLAMA = os.getenv("HEALTH_CHECK_ENABLE_OLLAMA", "true").lower() == "true"
