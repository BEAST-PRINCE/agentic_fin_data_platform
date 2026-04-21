import csv
import json
import time
import random
import logging
from kafka import KafkaProducer
from src.common import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

    def stream_data(self):
        """Read CSV and stream to Kafka with random delays."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                logger.info(f"Opened file: {self.file_path}")
                
                count = 0
                for row in reader:
                    # Clean the data slightly if needed (e.g., source field is a string representation of dict)
                    # For now just passing as is
                    self.producer.send(self.topic, value=row)
                    count += 1
                    
                    if count % 10 == 0:
                        logger.info(f"Sent {count} messages to topic '{self.topic}'")
                    
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
