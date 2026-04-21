import json
import time
from kafka import KafkaConsumer
from src.common import config
from src.common.logger import get_logger

logger = get_logger(__name__)

class NewsConsumer:
    def __init__(self):
        self.bootstrap_servers = config.KAFKA_BOOTSTRAP_SERVERS
        self.topic = config.KAFKA_TOPIC
        
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='news-ingestion-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info(f"Initialized Kafka Consumer at {self.bootstrap_servers} for topic '{self.topic}'")

    def consume_data(self):
        """Consume messages from Kafka in batches."""
        logger.info("Starting to consume messages...")
        batch_size = 100
        batch = []
        try:
            for message in self.consumer:
                data = message.value
                batch.append(data)
                
                # TODO: Phase 2 - Write this batch to MinIO
                if len(batch) >= batch_size:
                    logger.info(f"Collected a batch of {len(batch)} messages. (Ready for MinIO)")
                    batch.clear()
                

        except KeyboardInterrupt:
            logger.info("Consumer stopped by user.")
        except Exception as e:
            logger.error(f"Error while consuming messages: {e}")
        finally:
            self.consumer.close()
            logger.info("Kafka Consumer closed.")

if __name__ == "__main__":
    consumer = NewsConsumer()
    consumer.consume_data()
