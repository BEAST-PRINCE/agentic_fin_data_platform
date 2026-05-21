import os
import sys
import subprocess
import threading
import time
import queue
from datetime import datetime
from typing import Dict, Any, List

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.common.logger import get_logger
from src.storage.minio_client import MinIOClient

logger = get_logger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SYSTEM_LOGS_BUCKET = "system-logs"

class PipelineManager:
    def __init__(self):
        self.active_process: subprocess.Popen = None
        self.active_stage: str = "idle"
        
        self.log_buffer: List[str] = []
        self.log_queue: queue.Queue = queue.Queue()
        
        self.flush_thread: threading.Thread = None
        self.running_flag: bool = False
        
        self.minio_client = MinIOClient()

    def get_status(self) -> Dict[str, Any]:
        if self.active_process:
            if self.active_process.poll() is not None:
                self.active_stage = "idle"
                self.active_process = None
        
        return {
            "active_stage": self.active_stage,
            "status": "Running" if self.active_stage != "idle" else "Idle"
        }

    def run_stage(self, stage: str) -> Dict[str, Any]:
        self.get_status() # Refresh status
        if self.active_stage != "idle":
            return {"status": "error", "message": f"Cannot start {stage}: Pipeline is currently running {self.active_stage}."}

        logger.info(f"Starting pipeline stage: {stage}")
        
        cmd = []
        if stage == "silver":
            cmd = [
                "docker", "exec", "-e", "MINIO_ENDPOINT=minio:9000", "spark-master",
                "/opt/spark/bin/spark-submit", "--master", "local[*]",
                "--packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
                "/app/src/processing/silver_layer.py"
            ]
        elif stage == "gold":
            cmd = [
                "docker", "exec", "-e", "MINIO_ENDPOINT=minio:9000", "spark-master",
                "/opt/spark/bin/spark-submit", "--master", "local[*]",
                "--packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
                "/app/src/processing/gold_layer.py"
            ]
        elif stage == "indexer":
            cmd = [sys.executable, "src/processing/vector_indexer.py"]
        else:
            return {"status": "error", "message": f"Unknown stage: {stage}"}

        try:
            p = subprocess.Popen(
                cmd,
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.active_process = p
            self.active_stage = stage
            self.log_buffer = []
            
            # Clear old queue
            while not self.log_queue.empty():
                self.log_queue.get()
                
            self.running_flag = True
            
            threading.Thread(target=self._read_output, args=(p.stdout,), daemon=True).start()
            
            self.flush_thread = threading.Thread(target=self._flush_logs_to_minio, args=(stage,), daemon=True)
            self.flush_thread.start()
            
            return {"status": "success", "message": f"Started {stage}"}
        except Exception as e:
            logger.error(f"Failed to start {stage}: {e}")
            self.active_stage = "idle"
            return {"status": "error", "message": str(e)}

    def stop_pipeline(self) -> Dict[str, Any]:
        if not self.active_process or self.active_process.poll() is not None:
            return {"status": "error", "message": "Pipeline is not currently running."}
            
        logger.info(f"Force stopping pipeline stage: {self.active_stage}")
        self.active_process.terminate()
        self.running_flag = False
        self.active_stage = "idle"
        
        return {"status": "success", "message": "Pipeline stopped."}

    def _read_output(self, stdout):
        import re
        # Match pattern: YYYY-MM-DD HH:MM:SS,mmm - 
        log_pattern = re.compile(r"^202\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d - ")
        keep_multiline = False
        
        for line in iter(stdout.readline, ''):
            clean_line = line.strip()
            if clean_line:
                is_our_log = bool(log_pattern.match(clean_line))
                is_traceback = clean_line.startswith("Traceback (") or clean_line.startswith("File ") or clean_line.startswith("ValueError") or clean_line.startswith("Exception") or clean_line.startswith("TypeError") or clean_line.startswith("KeyError")
                
                if is_our_log or is_traceback:
                    keep_multiline = True
                    self.log_queue.put(clean_line)
                    self.log_buffer.append(clean_line)
                    if len(self.log_buffer) > 200:
                        self.log_buffer.pop(0)
                elif keep_multiline and (line.startswith(" ") or line.startswith("\t")):
                    # It's a continuation of a traceback or multiline log
                    self.log_queue.put(clean_line)
                    self.log_buffer.append(clean_line)
                    if len(self.log_buffer) > 200:
                        self.log_buffer.pop(0)
                else:
                    # It's an internal Spark/JVM log, ignore it!
                    keep_multiline = False
                    
        stdout.close()
        self.running_flag = False
        
        # Check process status to reset stage cleanly
        if self.active_process and self.active_process.poll() is not None:
            self.active_stage = "idle"

    def _flush_logs_to_minio(self, stage: str):
        client = self.minio_client.client
        buffer = []
        
        while self.running_flag or not self.log_queue.empty():
            time.sleep(15)
            
            while not self.log_queue.empty():
                buffer.append(self.log_queue.get())
                
            if buffer:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                object_name = f"{stage}_pipeline/{timestamp}.log"
                log_data = "\\n".join(buffer).encode('utf-8')
                
                from io import BytesIO
                try:
                    client.put_object(
                        bucket_name=SYSTEM_LOGS_BUCKET,
                        object_name=object_name,
                        data=BytesIO(log_data),
                        length=len(log_data),
                        content_type="text/plain"
                    )
                    buffer.clear()
                except Exception as e:
                    logger.error(f"Failed to upload pipeline logs to MinIO for {stage}: {e}")

    def get_logs(self) -> List[str]:
        return self.log_buffer

pipeline_manager = PipelineManager()
