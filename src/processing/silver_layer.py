import os
import sys
from functools import reduce
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, split, size, lit
from src.common import config
from src.common.logger import get_logger
from src.storage.minio_client import MinIOClient

logger = get_logger(__name__)


def create_spark_session() -> SparkSession:
    """Initialize SparkSession with MinIO (S3A) configurations and required JARs."""
    logger.info("Initializing Spark Session for Silver Layer...")

    endpoint = f"http://{config.MINIO_ENDPOINT}" if not config.MINIO_SECURE else f"https://{config.MINIO_ENDPOINT}"
    spark = SparkSession.builder \
        .appName("BronzeToSilverProcessing") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .config("spark.hadoop.fs.s3a.endpoint", endpoint) \
        .config("spark.hadoop.fs.s3a.access.key", config.MINIO_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", config.MINIO_SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", str(config.MINIO_SECURE).lower()) \
        .getOrCreate()

    return spark


import json
import io
from pathlib import Path
from datetime import datetime, timezone

def get_last_processed_timestamp() -> datetime:
    """Retrieve the latest processed timestamp from the MinIO state tracker."""
    client = MinIOClient()
    client.ensure_bucket_exists("system-logs")
    try:
        response = client.client.get_object("system-logs", "silver_state.json")
        state = json.loads(response.read().decode('utf-8'))
        response.close()
        response.release_conn()
        ts_str = state.get("last_processed_timestamp", "1970-01-01T00:00:00+00:00")
        return datetime.fromisoformat(ts_str)
    except Exception as e:
        logger.info(f"No previous state found in MinIO or error reading state. Falling back to full load.")
        return datetime.fromisoformat("1970-01-01T00:00:00+00:00")

def update_last_processed_timestamp(timestamp: datetime):
    """Save the latest processed timestamp to the MinIO state tracker."""
    client = MinIOClient()
    client.ensure_bucket_exists("system-logs")
    try:
        data = json.dumps({"last_processed_timestamp": timestamp.isoformat()}, indent=2).encode('utf-8')
        client.upload_stream("system-logs", "silver_state.json", io.BytesIO(data), len(data))
        logger.info(f"Updated incremental state tracker in MinIO with timestamp: {timestamp.isoformat()}")
    except Exception as e:
        logger.error(f"Failed to save state file to MinIO: {e}")

def _get_new_bronze_files(sources: Optional[List[str]] = None) -> List[str]:
    """
    Use MinIO client to quickly list all files in the bronze bucket and return ONLY 
    the paths of files that have been added/modified since the last pipeline run.
    """
    last_processed = get_last_processed_timestamp()
    logger.info(f"Checking for new files modified after {last_processed.isoformat()}")
    
    minio_client = MinIOClient().client
    resolved = sources if sources is not None else config.get_silver_bronze_sources()
    
    new_paths = []
    latest_mod_time = last_processed

    try:
        # Check specific sources if provided, otherwise check all raw_news
        prefixes = [f"raw_news/source={s}/" for s in resolved] if resolved else ["raw_news/"]
        
        for prefix in prefixes:
            objects = minio_client.list_objects(config.MINIO_BRONZE_BUCKET, prefix=prefix, recursive=True)
            for obj in objects:
                # Ensure obj.last_modified is timezone aware
                mod_time = obj.last_modified
                if mod_time > last_processed:
                    new_paths.append(f"s3a://{config.MINIO_BRONZE_BUCKET}/{obj.object_name}")
                    if mod_time > latest_mod_time:
                        latest_mod_time = mod_time
                        
        return new_paths, latest_mod_time
    except Exception as e:
        logger.error(f"Error checking MinIO for new files: {e}")
        return [], last_processed

def _read_bronze_json(spark: SparkSession, paths: List[str]) -> DataFrame:
    # Read the explicit list of new file paths
    # We don't need recursiveFileLookup anymore since we pass the exact file paths!
    return spark.read.option("multiLine", "true").json(paths)


def process_silver_layer(sources: Optional[List[str]] = None):
    spark = create_spark_session()
    silver_path = f"s3a://{config.MINIO_SILVER_BUCKET}/cleaned_news"

    logger.info("Scanning MinIO storage for new files...")
    new_paths, latest_mod_time = _get_new_bronze_files(sources)
    
    if not new_paths:
        logger.info("No new files found in Bronze layer. Exiting early.")
        spark.stop()
        return
        
    logger.info(f"Found {len(new_paths)} new files to process.")
    
    df = _read_bronze_json(spark, new_paths)
    
    # CRITICAL FIX: Cache the raw dataframe!
    df.cache()

    initial_count = df.count()
    logger.info(f"Loaded {initial_count} raw records from new files.")

    logger.info("Dropping records with nulls in critical fields (title, content, source)...")
    cleaned_df = df.dropna(subset=["title", "content", "source"])

    logger.info("Filtering out articles with less than 10 words in content...")
    cleaned_df = cleaned_df.filter(size(split(col("content"), " ")) >= 10)

    logger.info("Deduplicating records based on article_id...")
    cleaned_df = cleaned_df.dropDuplicates(["article_id"])

    final_count = cleaned_df.count()
    logger.info(
        f"Data cleaning complete. {final_count} records remain "
        f"(removed {initial_count - final_count})."
    )

    logger.info("Ensuring silver bucket exists...")
    minio_client = MinIOClient()
    minio_client.ensure_bucket_exists(config.MINIO_SILVER_BUCKET)

    logger.info(f"Writing cleaned data to Silver layer: {silver_path} in Parquet format...")
    cleaned_df.write.mode("append").parquet(silver_path)

    # Update state tracker only after a successful write
    update_last_processed_timestamp(latest_mod_time)

    logger.info("Silver Layer processing completed successfully!")
    spark.stop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bronze to Silver processing job")
    parser.add_argument(
        "--sources",
        nargs="*",
        help="Bronze source= partition values (e.g. livemint moneycontrol). Defaults to SILVER_BRONZE_SOURCES env.",
    )
    args = parser.parse_args()
    process_silver_layer(sources=args.sources)
