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
    """
    Perform a lightweight TCP socket ping to the Kafka broker.
    This replaces the heavy KafkaConsumer initialization, dropping latency 
    from hundreds of milliseconds down to ~1-5ms.
    """
    import socket
    start = time.time()
    try:
        host, port = config.KAFKA_BOOTSTRAP_SERVERS.split(":")
        
        # Create a native TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        
        # Attempt to connect
        result = sock.connect_ex((host, int(port)))
        sock.close()
        
        if result == 0:
            latency = round((time.time() - start) * 1000, 2)
            return {"status": "online", "latency_ms": latency}
        else:
            return {"status": "offline", "latency_ms": None, "error": f"Socket error code: {result}"}
            
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
