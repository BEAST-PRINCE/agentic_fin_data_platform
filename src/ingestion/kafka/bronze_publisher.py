import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from kafka import KafkaProducer

from src.common import config
from src.common.logger import get_logger
from src.ingestion.kafka.schema import build_bronze_kafka_payload

logger = get_logger(__name__)


class BronzePublisher:
    def __init__(self):
        self.producer = None
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
            )
            logger.info(
                f"Connected to Kafka at {config.KAFKA_BOOTSTRAP_SERVERS} "
                f"(topic={config.KAFKA_TOPIC})"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")

    def publish_article(self, article_data: dict) -> bool:
        if not self.producer:
            logger.warning("Kafka producer not initialized. Cannot publish.")
            return False

        payload = build_bronze_kafka_payload(article_data)

        try:
            future = self.producer.send(config.KAFKA_TOPIC, value=payload)
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Published article {payload['article_id']} to {record_metadata.topic} "
                f"partition {record_metadata.partition} offset {record_metadata.offset}"
            )
            return True
        except Exception as e:
            logger.error(f"Error publishing to Kafka: {e}")
            return False

    def close(self):
        if self.producer:
            self.producer.flush()
            self.producer.close()


if __name__ == "__main__":
    publisher = BronzePublisher()
    test_data = {
        "title": "Test Article",
        "url": "https://example.com/test",
        "content": "This is a test article content with enough words for validation.",
        "source": "TestSource",
        "published_at": "2024-05-12T10:00:00Z",
        "author": "Test Author",
    }
    publisher.publish_article(test_data)
    publisher.close()
