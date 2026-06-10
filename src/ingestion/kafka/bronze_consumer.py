import json
import sys
import os
import time
from urllib.parse import urlparse
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import boto3
from kafka import KafkaConsumer, KafkaProducer

from src.common import config
from src.common.logger import get_logger
from src.ingestion.kafka.schema import build_bronze_s3_key, sanitize_source_partition
from src.storage.lakehouse_stats import increment_bronze

logger = get_logger(__name__)

MINIO_ENDPOINT = (
    f"http://{config.MINIO_ENDPOINT}"
    if not config.MINIO_SECURE
    else f"https://{config.MINIO_ENDPOINT}"
)


def _safe_deserialize(raw: bytes):
    """Deserialize JSON; return a sentinel dict on failure for DLQ routing."""
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return {
            "__invalid_message__": True,
            "__error__": str(e),
            "__raw_preview__": raw[:2000].decode("utf-8", errors="replace"),
        }


class BronzeConsumer:
    def __init__(self):
        self.consumer = None
        self.dlq_producer = None

        try:
            self.consumer = KafkaConsumer(
                config.KAFKA_TOPIC,
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                group_id=config.KAFKA_BRONZE_CONSUMER_GROUP,
                value_deserializer=_safe_deserialize,
            )
            logger.info(
                f"Kafka consumer connected: topic={config.KAFKA_TOPIC}, "
                f"group={config.KAFKA_BRONZE_CONSUMER_GROUP}"
            )
        except Exception as e:
            logger.error(f"Failed to connect Kafka consumer: {e}")

        if config.KAFKA_DLQ_ENABLED:
            try:
                self.dlq_producer = KafkaProducer(
                    bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                )
                logger.info(f"Kafka DLQ producer enabled for topic: {config.KAFKA_DLQ_TOPIC}")
            except Exception as e:
                logger.error(f"Failed to connect Kafka DLQ producer: {e}")

        # Initialize domain stats and pending bronze counter batch
        self.domain_counts = {}
        self.pending_bronze_count = 0
        self.last_flush_time = time.time()
        
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=config.MINIO_ACCESS_KEY,
            aws_secret_access_key=config.MINIO_SECRET_KEY,
            region_name="us-east-1",
        )
        
        try:
            res = self.s3_client.get_object(Bucket=config.MINIO_BRONZE_BUCKET, Key="domain_throughput.json")
            self.domain_counts = json.loads(res["Body"].read().decode("utf-8"))
            logger.info("Loaded initial domain throughput stats from MinIO.")
        except Exception as e:
            logger.info("No existing domain throughput stats found or could not load.")
            
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.s3_client.head_bucket(Bucket=config.MINIO_BRONZE_BUCKET)
        except Exception:
            logger.info(f"Bucket {config.MINIO_BRONZE_BUCKET} not found. Creating it...")
            try:
                self.s3_client.create_bucket(Bucket=config.MINIO_BRONZE_BUCKET)
                logger.info(f"Bucket {config.MINIO_BRONZE_BUCKET} created.")
            except Exception as e:
                logger.error(f"Could not create bucket {config.MINIO_BRONZE_BUCKET}: {e}")

    def _send_to_dlq(self, reason: str, payload: dict, original_message=None):
        if not config.KAFKA_DLQ_ENABLED or not self.dlq_producer:
            logger.warning(f"DLQ disabled or unavailable; dropping message: {reason}")
            return

        envelope = {
            "dlq_reason": reason,
            "dlq_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "original_topic": config.KAFKA_TOPIC,
            "payload": payload,
        }
        if original_message is not None:
            envelope["kafka_partition"] = original_message.partition
            envelope["kafka_offset"] = original_message.offset

        try:
            future = self.dlq_producer.send(config.KAFKA_DLQ_TOPIC, value=envelope)
            future.get(timeout=10)
            logger.info(f"Sent message to DLQ ({config.KAFKA_DLQ_TOPIC}): {reason}")
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
            raise

    def _upload_article(self, article_data: dict) -> str:
        article_id = article_data.get("article_id")
        source = article_data.get("source", "unknown")
        s3_key = build_bronze_s3_key(
            source=source,
            article_id=article_id,
            ingested_at=article_data.get("ingested_at"),
        )
        json_bytes = json.dumps(article_data, indent=2).encode("utf-8")
        self.s3_client.put_object(
            Bucket=config.MINIO_BRONZE_BUCKET,
            Key=s3_key,
            Body=json_bytes,
            ContentType="application/json",
        )
        return s3_key

    def _handle_bad_message(self, reason: str, payload: dict, message) -> bool:
        """
        Route bad messages to DLQ and commit offset when DLQ succeeds.
        Returns True if the offset can be committed.
        """
        try:
            self._send_to_dlq(reason, payload, message)
            return True
        except Exception:
            return False

    def _flush_domain_stats(self):
        try:
            json_bytes = json.dumps(self.domain_counts, indent=2).encode("utf-8")
            self.s3_client.put_object(
                Bucket=config.MINIO_BRONZE_BUCKET,
                Key="domain_throughput.json",
                Body=json_bytes,
                ContentType="application/json",
            )
            if self.pending_bronze_count > 0:
                increment_bronze(self.pending_bronze_count)
                logger.info(
                    f"Flushed {self.pending_bronze_count} bronze records to lakehouse stats."
                )
                self.pending_bronze_count = 0
            logger.info("Flushed domain throughput stats to MinIO.")
        except Exception as e:
            logger.error(f"Failed to flush domain stats: {e}")

    def start_consuming(self):
        if not self.consumer:
            logger.error("No Kafka consumer configured.")
            return

        logger.info(f"Consuming from topic: {config.KAFKA_TOPIC}")
        for message in self.consumer:
            article_data = message.value

            if article_data.get("__invalid_message__"):
                if self._handle_bad_message(
                    "json_deserialize_error",
                    article_data,
                    message,
                ):
                    self.consumer.commit()
                continue

            article_id = article_data.get("article_id")
            if not article_id:
                if self._handle_bad_message("missing_article_id", article_data, message):
                    self.consumer.commit()
                continue

            required = ("title", "content", "source")
            missing = [f for f in required if not article_data.get(f)]
            if missing:
                if self._handle_bad_message(
                    f"missing_required_fields:{','.join(missing)}",
                    article_data,
                    message,
                ):
                    self.consumer.commit()
                continue

            try:
                s3_key = self._upload_article(article_data)
                self.consumer.commit()
                logger.info(
                    f"Saved {article_id} (source={sanitize_source_partition(article_data.get('source'))}) "
                    f"to s3://{config.MINIO_BRONZE_BUCKET}/{s3_key}"
                )
                
                self.pending_bronze_count += 1

                # Update domain throughput stats
                url = article_data.get("url")
                if url:
                    domain = urlparse(url).netloc
                    if domain:
                        self.domain_counts[domain] = self.domain_counts.get(domain, 0) + 1

                # Flush every 5 seconds
                if time.time() - self.last_flush_time >= 5:
                    self._flush_domain_stats()
                    self.last_flush_time = time.time()
                    
            except Exception as e:
                logger.error(
                    f"Failed to upload {article_id} to MinIO (offset not committed, will retry): {e}"
                )


if __name__ == "__main__":
    consumer = BronzeConsumer()
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Stopping consumer.")
    finally:
        consumer._flush_domain_stats()
        if consumer.consumer:
            consumer.consumer.close()
