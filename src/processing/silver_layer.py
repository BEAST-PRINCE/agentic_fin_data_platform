import os
import sys

# Ensure the project root is in the path when running inside the spark container
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, split, size
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

def process_silver_layer():
    spark = create_spark_session()
    
    bronze_path = f"s3a://{config.MINIO_BRONZE_BUCKET}/raw_news"
    silver_path = f"s3a://{config.MINIO_SILVER_BUCKET}/cleaned_news"
    
    logger.info(f"Reading raw data from Bronze layer: {bronze_path}")
    # Read all JSONL files in the bronze bucket under raw_news/
    df = spark.read.option("recursiveFileLookup", "true").json(bronze_path)

    initial_count = df.count()
    logger.info(f"Loaded {initial_count} raw records.")

    # 1. Drop records where critical fields are null
    logger.info("Dropping records with nulls in critical fields (title, content, source)...")
    cleaned_df = df.dropna(subset=["title", "content", "source"])

    # 2. Filter content with less than 10 words
    logger.info("Filtering out articles with less than 10 words in content...")
    cleaned_df = cleaned_df.filter(size(split(col("content"), " ")) >= 10)

    # 3. Deduplicate based on article_id
    logger.info("Deduplicating records based on article_id...")
    cleaned_df = cleaned_df.dropDuplicates(["article_id"])

    final_count = cleaned_df.count()
    logger.info(f"Data cleaning complete. {final_count} records remain (removed {initial_count - final_count}).")

    # 4. Write to Silver layer
    logger.info("Ensuring silver bucket exists...")
    minio_client = MinIOClient()
    minio_client.ensure_bucket_exists(config.MINIO_SILVER_BUCKET)

    logger.info(f"Writing cleaned data to Silver layer: {silver_path} in Parquet format...")
    cleaned_df.write \
        .mode("overwrite") \
        .parquet(silver_path)

    logger.info("Silver Layer processing completed successfully!")
    spark.stop()

if __name__ == "__main__":
    process_silver_layer()
