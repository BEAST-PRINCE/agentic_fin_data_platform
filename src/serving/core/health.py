import time
import requests
from typing import Dict, Any
from src.common import config
from src.common.logger import get_logger
from src.storage.db_client import db

logger = get_logger(__name__)

def check_minio() -> Dict[str, Any]:
    start = time.time()
    try:
        from src.storage.minio_client import MinIOClient
        client = MinIOClient().client
        client.bucket_exists(config.MINIO_GOLD_BUCKET)
        latency = round((time.time() - start) * 1000, 2)
        return {"status": "online", "latency_ms": latency}
    except Exception as e:
        logger.warning(f"MinIO health check failed: {e}")
        return {"status": "offline", "latency_ms": None, "error": str(e)}

def check_kafka() -> Dict[str, Any]:
    start = time.time()
    try:
        from kafka import KafkaConsumer
        consumer = KafkaConsumer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            request_timeout_ms=1000,
            session_timeout_ms=2000,
            connections_max_idle_ms=3000
        )
        consumer.topics()
        consumer.close()
        latency = round((time.time() - start) * 1000, 2)
        return {"status": "online", "latency_ms": latency}
    except Exception as e:
        logger.warning(f"Kafka health check failed: {e}")
        return {"status": "offline", "latency_ms": None, "error": str(e)}

def check_qdrant() -> Dict[str, Any]:
    start = time.time()
    try:
        res = requests.get("http://localhost:6333/collections", timeout=2)
        res.raise_for_status()
        latency = round((time.time() - start) * 1000, 2)
        return {"status": "online", "latency_ms": latency}
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}")
        return {"status": "offline", "latency_ms": None, "error": str(e)}

def check_duckdb() -> Dict[str, Any]:
    start = time.time()
    try:
        db.query("SELECT 1")
        latency = round((time.time() - start) * 1000, 2)
        return {"status": "online", "latency_ms": latency}
    except Exception as e:
        logger.warning(f"DuckDB health check failed: {e}")
        return {"status": "offline", "latency_ms": None, "error": str(e)}

def check_ollama() -> Dict[str, Any]:
    start = time.time()
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=2)
        res.raise_for_status()
        latency = round((time.time() - start) * 1000, 2)
        return {"status": "online", "latency_ms": latency}
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        return {"status": "offline", "latency_ms": None, "error": str(e)}

def get_system_health() -> Dict[str, Any]:
    """Gather health status of all dependent services, skipping disabled ones."""
    health_status = {}
    if config.HEALTH_CHECK_ENABLE_MINIO:
        health_status["minio"] = check_minio()
    if config.HEALTH_CHECK_ENABLE_KAFKA:
        health_status["kafka"] = check_kafka()
    if config.HEALTH_CHECK_ENABLE_QDRANT:
        health_status["qdrant"] = check_qdrant()
    if config.HEALTH_CHECK_ENABLE_DUCKDB:
        health_status["duckdb"] = check_duckdb()
    if config.HEALTH_CHECK_ENABLE_OLLAMA:
        health_status["ollama"] = check_ollama()
    return health_status
