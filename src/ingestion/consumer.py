import json
import time
import io
from datetime import datetime
from kafka import KafkaConsumer
from src.common import config
from src.common.logger import get_logger
from src.storage.minio_client import MinIOClient
from src.storage.lakehouse_stats import increment_bronze

logger = get_logger(__name__)

class NewsConsumer:
    def __init__(self):
        self.bootstrap_servers = config.KAFKA_BOOTSTRAP_SERVERS
        self.topic = config.KAFKA_TOPIC
        
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            group_id='news-ingestion-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info(f"Initialized Kafka Consumer at {self.bootstrap_servers} for topic '{self.topic}'")
        
        self.minio_client = MinIOClient()
        self.minio_bucket = config.MINIO_BRONZE_BUCKET
        self.minio_client.ensure_bucket_exists(self.minio_bucket)

    def consume_data(self):
        """Consume messages from Kafka in batches and upload to MinIO."""
        logger.info("Starting to consume messages...")
        batch_size = 100
        batch = []
        try:
            for message in self.consumer:
                data = message.value
                batch.append(data)
                
                if len(batch) >= batch_size:
                    self._process_batch(batch)
                    batch.clear()

        except KeyboardInterrupt:
            logger.info("Consumer stopped by user.")
        except Exception as e:
            logger.error(f"Error while consuming messages: {e}")
        finally:
            if batch:
                logger.info(f"Uploading final partial batch of {len(batch)} messages...")
                try:
                    self._process_batch(batch)
                except Exception as e:
                    logger.error(f"Failed to upload final batch: {e}")
            self.consumer.close()
            logger.info("Kafka Consumer closed.")

    def _process_batch(self, batch):
        """Serializes batch to JSONL and uploads to MinIO as a partitioned object."""
        if not batch:
            return
            
        # Use the ingestion timestamp of the first message for partitioning
        first_msg_ts = batch[0].get("ingested_at", datetime.utcnow().isoformat())
        try:
            dt = datetime.fromisoformat(first_msg_ts.replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.utcnow()
            
        timestamp = int(time.time() * 1000)
        object_path = f"raw_news/year={dt.year}/month={dt.month:02d}/day={dt.day:02d}/batch_{timestamp}.jsonl"
        
        # Serialize to JSONL in memory
        buffer = io.BytesIO()
        for item in batch:
            buffer.write((json.dumps(item) + "\n").encode('utf-8'))
            
        length = buffer.tell()
        
        # Upload
        self.minio_client.upload_stream(self.minio_bucket, object_path, buffer, length)
        increment_bronze(len(batch))

        # Manually commit Kafka offsets to ensure at-least-once delivery
        self.consumer.commit()
        logger.info(f"Committed Kafka offsets after successful batch upload.")

if __name__ == "__main__":
    consumer = NewsConsumer()
    consumer.consume_data()
