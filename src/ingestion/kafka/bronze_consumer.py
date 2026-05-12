import os
import json
import logging
import boto3
import time
from datetime import datetime
from kafka import KafkaConsumer
from botocore.exceptions import NoCredentialsError

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.common import config

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_NAME = os.getenv("KAFKA_RAW_TOPIC", "raw_financial_news")

MINIO_ENDPOINT = f"http://{config.MINIO_ENDPOINT}" if not config.MINIO_SECURE else f"https://{config.MINIO_ENDPOINT}"
MINIO_ACCESS_KEY = config.MINIO_ACCESS_KEY
MINIO_SECRET_KEY = config.MINIO_SECRET_KEY
BRONZE_BUCKET = config.MINIO_BRONZE_BUCKET

class BronzeConsumer:
    def __init__(self):
        try:
            self.consumer = KafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='bronze-ingestion-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info(f"Connected to Kafka broker at {KAFKA_BROKER}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.consumer = None

        self.s3_client = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            region_name='us-east-1' # Default for MinIO
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.s3_client.head_bucket(Bucket=BRONZE_BUCKET)
        except Exception as e:
            logger.info(f"Bucket {BRONZE_BUCKET} not found. Creating it...")
            try:
                self.s3_client.create_bucket(Bucket=BRONZE_BUCKET)
                logger.info(f"Bucket {BRONZE_BUCKET} created.")
            except Exception as e2:
                logger.error(f"Could not create bucket {BRONZE_BUCKET}: {e2}")

    def generate_s3_key(self, source, article_id):
        # Format: raw_news/source/year=YYYY/month=MM/day=DD/article_id.json
        now = datetime.utcnow()
        safe_source = source.replace(" ", "_").lower() if source else "unknown"
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        
        key = f"raw_news/{safe_source}/year={year}/month={month}/day={day}/{article_id}.json"
        return key

    def start_consuming(self):
        if not self.consumer:
            logger.error("No Kafka consumer configured.")
            return

        logger.info(f"Starting to consume from topic: {TOPIC_NAME}")
        for message in self.consumer:
            article_data = message.value
            article_id = article_data.get('article_id')
            source = article_data.get('source', 'unknown')
            
            if not article_id:
                logger.warning(f"Received message without article_id: {article_data}")
                continue
                
            s3_key = self.generate_s3_key(source, article_id)
            
            try:
                json_bytes = json.dumps(article_data, indent=2).encode('utf-8')
                self.s3_client.put_object(
                    Bucket=BRONZE_BUCKET,
                    Key=s3_key,
                    Body=json_bytes,
                    ContentType='application/json'
                )
                logger.info(f"Successfully saved {article_id} to s3://{BRONZE_BUCKET}/{s3_key}")
            except Exception as e:
                logger.error(f"Failed to upload {article_id} to MinIO: {e}")

if __name__ == "__main__":
    consumer = BronzeConsumer()
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Stopping consumer.")
