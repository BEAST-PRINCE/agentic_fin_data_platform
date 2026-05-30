import logging
import sys
import os
import threading
import time
import queue
from datetime import datetime
from io import BytesIO

# Global variables for the MinIO logger background thread
_minio_log_queue = queue.Queue()
_minio_flush_thread = None
_minio_client = None
_bucket_initialized = False

SYSTEM_LOGS_BUCKET = "system-logs"

def _init_minio_bucket():
    global _bucket_initialized, _minio_client
    if _bucket_initialized:
        return
    try:
        from minio import Minio
        from src.common import config
        
        _minio_client = Minio(
            config.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=False
        )
        
        found = _minio_client.bucket_exists(SYSTEM_LOGS_BUCKET)
        if not found:
            _minio_client.make_bucket(SYSTEM_LOGS_BUCKET)
        
        # Set 15-day TTL
        from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration, Filter
        lifecycle_config = LifecycleConfig([
            Rule(
                status="Enabled",
                rule_filter=Filter(prefix=""),
                rule_id="expire-system-logs-15-days",
                expiration=Expiration(days=15)
            )
        ])
        _minio_client.set_bucket_lifecycle(SYSTEM_LOGS_BUCKET, lifecycle_config)
        _bucket_initialized = True
    except Exception as e:
        print(f"Failed to initialize system-logs bucket: {e}", file=sys.stderr)

def _minio_flush_worker():
    global _minio_client
    buffer = []
    
    # Process Name identifying the script running
    script_name = os.path.basename(sys.argv[0]) if sys.argv else "unknown_script"
    if script_name.endswith('.py'):
        script_name = script_name[:-3]

    while True:
        time.sleep(30) # Flush every 30 seconds
        
        while not _minio_log_queue.empty():
            buffer.append(_minio_log_queue.get())
            
        if buffer and _minio_client:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            object_name = f"{script_name}/{timestamp}.log"
            log_data = "\\n".join(buffer).encode('utf-8')
            
            try:
                _minio_client.put_object(
                    bucket_name=SYSTEM_LOGS_BUCKET,
                    object_name=object_name,
                    data=BytesIO(log_data),
                    length=len(log_data),
                    content_type="text/plain"
                )
                buffer.clear()
            except Exception as e:
                print(f"Failed to upload system logs to MinIO: {e}", file=sys.stderr)

class MinIOLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        global _minio_flush_thread
        
        _init_minio_bucket()
        
        # Start the background thread once
        if _minio_flush_thread is None:
            _minio_flush_thread = threading.Thread(target=_minio_flush_worker, daemon=True)
            _minio_flush_thread.start()

    def emit(self, record):
        try:
            msg = self.format(record)
            _minio_log_queue.put(msg)
        except Exception:
            self.handleError(record)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a centrally configured logger instance that also logs to MinIO.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Standard stderr handler
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # MinIO handler
        try:
            minio_handler = MinIOLogHandler()
            minio_handler.setLevel(logging.INFO)
            minio_handler.setFormatter(formatter)
            logger.addHandler(minio_handler)
        except Exception as e:
            print(f"Failed to attach MinIOLogHandler: {e}", file=sys.stderr)
            
        logger.propagate = False
        
    return logger
