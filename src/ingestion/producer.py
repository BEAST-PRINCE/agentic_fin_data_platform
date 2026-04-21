import csv
import json
import time
import random
import logging
import hashlib
import ast
from datetime import datetime
from kafka import KafkaProducer
from src.common import config
from src.common.logger import get_logger

logger = get_logger(__name__)


class NewsProducer:
    def __init__(self):
        self.bootstrap_servers = config.KAFKA_BOOTSTRAP_SERVERS
        self.topic = config.KAFKA_TOPIC
        self.file_path = config.RAW_DATA_PATH
        
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all'
        )
        logger.info(f"Initialized Kafka Producer at {self.bootstrap_servers}")

    def generate_article_id(self, row):
        """Generate a deterministic MD5 hash for article_id based on priority."""
        url = row.get('url')
        title = row.get('title')
        source = row.get('source')
        content = row.get('content')
        
        if url:
            id_input = url
        elif title or source:
            id_input = f"{title or ''}{source or ''}"
        else:
            id_input = content or str(random.random())
            
        return hashlib.md5(id_input.encode('utf-8')).hexdigest()

    def transform_row(self, row):
        """Map dataset row to the target schema with normalization and defaults."""
        # Handle source parsing
        source_str = row.get('source', '')
        try:
            source_parsed = ast.literal_eval(source_str) if source_str else "unknown"
        except (ValueError, SyntaxError):
            source_parsed = source_str
            
        transformed = {
            "article_id": self.generate_article_id(row),
            "title": row.get('title', ''),
            "content": row.get('content', ''),
            "description": row.get('description', ''),
            "author": row.get('author') or "unknown",
            "source": source_parsed,
            "url": row.get('url', ''),
            "image_url": row.get('urlToImage', ''),  # Rename
            "published_at": row.get('publishedAt', ''),  # Rename
            "category": row.get('category') or "general",
            "ingested_at": datetime.utcnow().isoformat() + "Z"
        }
        return transformed

    def stream_data(self):
        """Read CSV and stream to Kafka with random delays and schema transformation."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                logger.info(f"Opened file: {self.file_path}")
                
                count = 0
                for row in reader:
                    # Apply schema transformation
                    transformed_row = self.transform_row(row)
                    
                    self.producer.send(self.topic, value=transformed_row)
                    count += 1
                    
                    if count % 10 == 0:
                        logger.info(f"Sent {count} transformed messages to topic '{self.topic}'")
                    
                    # Random delay between 0.1s and 1.0s
                    delay = random.uniform(0.1, 1.0)
                    time.sleep(delay)
                
                # Ensure all messages are sent
                self.producer.flush()
                logger.info(f"Successfully sent total {count} messages.")

        except FileNotFoundError:
            logger.error(f"Dataset file not found at {self.file_path}")
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
        finally:
            self.producer.close()
            logger.info("Kafka Producer closed.")

if __name__ == "__main__":
    producer = NewsProducer()
    producer.stream_data()
