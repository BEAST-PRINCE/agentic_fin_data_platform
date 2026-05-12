import os
import json
import uuid
import logging
import hashlib
from datetime import datetime, timezone
from kafka import KafkaProducer

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_NAME = os.getenv("KAFKA_RAW_TOPIC", "raw_financial_news")

class BronzePublisher:
    def __init__(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info(f"Connected to Kafka broker at {KAFKA_BROKER}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.producer = None

    def publish_article(self, article_data: dict):
        if not self.producer:
            logger.warning("Kafka producer not initialized. Cannot publish.")
            return False

        # Ensure schema fields
        article_id = article_data.get('article_id')
        if not article_id:
            url = article_data.get('url')
            title = article_data.get('title')
            source = article_data.get('source')
            content = article_data.get('content')
            
            if url:
                id_input = url
            elif title or source:
                id_input = f"{title or ''}{source or ''}"
            else:
                id_input = content or str(uuid.uuid4())
                
            article_id = hashlib.md5(id_input.encode('utf-8')).hexdigest()
        
        payload = {
            "article_id": article_id,
            "title": article_data.get('title', ''),
            "content": article_data.get('content', ''),
            "description": article_data.get('description', ''),
            "source": article_data.get('source', 'Unknown'),
            "url": article_data.get('url', ''),
            "published_at": article_data.get('published_at', ''),
            "author": article_data.get('author', ''),
            "category": article_data.get('category', ''),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "tags": article_data.get('tags', [])
        }

        try:
            future = self.producer.send(TOPIC_NAME, value=payload)
            record_metadata = future.get(timeout=10)
            logger.info(f"Published article {article_id} to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
            return True
        except Exception as e:
            logger.error(f"Error publishing to Kafka: {e}")
            return False

    def close(self):
        if self.producer:
            self.producer.flush()
            self.producer.close()

if __name__ == "__main__":
    # Test publishing
    publisher = BronzePublisher()
    test_data = {
        "title": "Test Article",
        "url": "https://example.com/test",
        "content": "This is a test article content."
    }
    publisher.publish_article(test_data)
    publisher.close()
