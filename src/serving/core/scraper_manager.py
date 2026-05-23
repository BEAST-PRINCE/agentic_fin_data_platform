import os
import sys
import subprocess
import threading
import time
import queue
import json
from datetime import datetime
from typing import Dict, Any, List

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.common import config
from src.common.logger import get_logger
from src.storage.minio_client import MinIOClient

logger = get_logger(__name__)

# Scrapy project path
SCRAPY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "ingestion", "scrapers", "scrapy_project"
)

SCRAPER_LOGS_BUCKET = "scraper-logs"

class ScraperManager:
    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.log_buffers: Dict[str, List[str]] = {}
        self.log_queues: Dict[str, queue.Queue] = {}
        self.flush_threads: Dict[str, threading.Thread] = {}
        self.running_flags: Dict[str, bool] = {}
        
        self.bronze_consumer_process: subprocess.Popen = None
        
        self.minio_client = MinIOClient()
        self._ensure_bucket_and_ttl()
        
        # Dynamically discover scrapers once on startup
        self.available_scrapers = self._discover_scrapers()

    def _discover_scrapers(self) -> List[str]:
        """Dynamically find all available Scrapy spiders."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "scrapy", "list"],
                cwd=SCRAPY_DIR,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                scrapers = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                logger.info(f"Dynamically discovered scrapers: {scrapers}")
                return scrapers
            else:
                logger.warning(f"Failed to list scrapers, scrapy list returned non-zero: {result.stderr}")
        except Exception as e:
            logger.error(f"Error discovering scrapers: {e}")
        return []

    def _ensure_bucket_and_ttl(self):
        """Ensure the log bucket exists and configure 15-day TTL."""
        try:
            self.minio_client.ensure_bucket_exists(SCRAPER_LOGS_BUCKET)
            
            # Use Minio python client directly to set lifecycle
            client = self.minio_client.client
            from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration, Filter
            
            config = LifecycleConfig([
                Rule(
                    status="Enabled",
                    rule_filter=Filter(prefix=""),  # Applies to all objects
                    rule_id="expire-logs-15-days",
                    expiration=Expiration(days=15)
                )
            ])
            client.set_bucket_lifecycle(SCRAPER_LOGS_BUCKET, config)
            logger.info(f"Configured 15-day TTL lifecycle for bucket: {SCRAPER_LOGS_BUCKET}")
        except Exception as e:
            logger.warning(f"Could not configure bucket TTL: {e}")

    def list_scrapers(self) -> List[Dict[str, Any]]:
        status_list = []
        for name in self.available_scrapers:
            process = self.active_processes.get(name)
            is_running = process is not None and process.poll() is None
            status_list.append({
                "name": name,
                "status": "Running" if is_running else "Idle",
                "pid": process.pid if is_running else None
            })
        return status_list

    def start_scraper(self, name: str) -> Dict[str, Any]:
        process = self.active_processes.get(name)
        if process and process.poll() is None:
            return {"status": "error", "message": f"Scraper {name} is already running."}
            
        logger.info(f"Starting scraper: {name} in {SCRAPY_DIR}")
        
        # Ensure bronze consumer is running
        if self.bronze_consumer_process is None or self.bronze_consumer_process.poll() is not None:
            logger.info("Starting bronze consumer for data ingestion...")
            bronze_consumer_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "ingestion", "kafka", "bronze_consumer.py"
            )
            self.bronze_consumer_process = subprocess.Popen([sys.executable, bronze_consumer_path])
        
        # Run process and pipe output using the current python executable (venv)
        try:
            p = subprocess.Popen(
                [sys.executable, "-m", "scrapy", "crawl", name],
                cwd=SCRAPY_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.active_processes[name] = p
            self.log_buffers[name] = ["Scraper is running..."]
            self.log_queues[name] = queue.Queue()
            self.running_flags[name] = True
            
            # Start background threads for reading and flushing logs
            threading.Thread(target=self._read_output, args=(name, p.stdout), daemon=True).start()
            
            flush_thread = threading.Thread(target=self._flush_logs_to_minio, args=(name,), daemon=True)
            self.flush_threads[name] = flush_thread
            flush_thread.start()
            
            return {"status": "success", "message": f"Started {name}", "pid": p.pid}
        except Exception as e:
            logger.error(f"Failed to start scraper {name}: {e}")
            return {"status": "error", "message": str(e)}

    def stop_scraper(self, name: str) -> Dict[str, Any]:
        process = self.active_processes.get(name)
        if not process or process.poll() is not None:
            return {"status": "error", "message": f"Scraper {name} is not running."}
            
        logger.info(f"Stopping scraper: {name}")
        process.terminate()
        
        # Stop background thread gracefully
        self.running_flags[name] = False
        
        # If no other scrapers are running, stop the bronze consumer
        running_count = sum(1 for p in self.active_processes.values() if p and p.poll() is None)
        if running_count == 0 and self.bronze_consumer_process:
            logger.info("No active scrapers remaining. Stopping bronze consumer...")
            self.bronze_consumer_process.terminate()
            self.bronze_consumer_process = None
            
        return {"status": "success", "message": f"Stopped {name}"}

    def _read_output(self, name: str, stdout):
        """Read lines from stdout and push to queue (MinIO) and selectively to buffer (Frontend)."""
        capturing_stats = False
        stats_buffer = []
        
        for line in iter(stdout.readline, ''):
            clean_line = line.strip()
            if clean_line:
                # Always send to MinIO queue
                self.log_queues[name].put(clean_line)
                
                # Smart filtering for Frontend
                if "Dumping Scrapy stats:" in clean_line:
                    capturing_stats = True
                    stats_buffer.append("--- Scrapy Execution Stats ---")
                elif capturing_stats:
                    if clean_line.startswith("20") and "[scrapy" in clean_line:
                        # Reached the end of the stats dictionary (which is usually followed by another log line like "Spider closed")
                        capturing_stats = False
                        # Update frontend buffer to show ONLY stats
                        self.log_buffers[name] = stats_buffer.copy()
                    else:
                        stats_buffer.append(clean_line)
                        # Show live stats buildup
                        self.log_buffers[name] = stats_buffer.copy()
                        
        stdout.close()
        self.running_flags[name] = False
        
        # Check if the process exited with an error or without stats
        p = self.active_processes.get(name)
        if p and p.poll() != 0 and len(stats_buffer) == 0:
            self.log_buffers[name].append("--- Scraper Error ---")
            self.log_buffers[name].append("The scraper crashed or exited unexpectedly.")
            self.log_buffers[name].append("Please check the 'scraper-logs' in MinIO or your backend terminal for the full stacktrace.")

    def _flush_logs_to_minio(self, name: str):
        """Flush logs to MinIO every 25 seconds."""
        client = self.minio_client.client
        buffer = []
        
        while self.running_flags.get(name, False):
            # Wait 25 seconds or until queue has items
            time.sleep(25)
            
            while not self.log_queues[name].empty():
                buffer.append(self.log_queues[name].get())
                
            if buffer:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                object_name = f"{name}/{timestamp}.log"
                log_data = "\\n".join(buffer).encode('utf-8')
                
                from io import BytesIO
                try:
                    client.put_object(
                        bucket_name=SCRAPER_LOGS_BUCKET,
                        object_name=object_name,
                        data=BytesIO(log_data),
                        length=len(log_data),
                        content_type="text/plain"
                    )
                    buffer.clear()
                except Exception as e:
                    logger.error(f"Failed to upload logs to MinIO for {name}: {e}")

    def get_logs(self, name: str) -> List[str]:
        """Return the latest log buffer."""
        return self.log_buffers.get(name, [])

# Singleton instance
scraper_manager = ScraperManager()
