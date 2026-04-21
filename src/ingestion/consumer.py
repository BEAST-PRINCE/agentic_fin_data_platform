import json
import logging
from kafka import KafkaConsumer
from src.common import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        """Consume messages from Kafka and print them."""
        logger.info("Starting to consume messages...")
        try:
            for message in self.consumer:
                data = message.value
                # Printing a summary of the received news article
                logger.info(f"Received Story: {data.get('title', 'No Title')} | Category: {data.get('category', 'N/A')}")
                # You can uncomment the line below to see the full JSON
                # print(json.dumps(data, indent=2))
                
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
