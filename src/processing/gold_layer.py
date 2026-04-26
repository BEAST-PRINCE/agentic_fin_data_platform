import os
import sys
from collections import Counter
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, expr, udf, explode, count, lit
from pyspark.sql.types import ArrayType, StringType
from pyspark.ml.feature import Tokenizer, StopWordsRemover

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.common import config
from src.common.logger import get_logger
from src.storage.minio_client import MinIOClient

logger = get_logger(__name__)

def create_spark_session() -> SparkSession:
    logger.info("Initializing Spark Session for Gold Layer...")
    endpoint = f"http://{config.MINIO_ENDPOINT}" if not config.MINIO_SECURE else f"https://{config.MINIO_ENDPOINT}"
    spark = SparkSession.builder \
        .appName("SilverToGoldProcessing") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .config("spark.hadoop.fs.s3a.endpoint", endpoint) \
        .config("spark.hadoop.fs.s3a.access.key", config.MINIO_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", config.MINIO_SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", str(config.MINIO_SECURE).lower()) \
        .getOrCreate()
    return spark

# Lightweight UDF to extract top N keywords from an array of filtered words
@udf(returnType=ArrayType(StringType()))
def extract_top_keywords(words):
    if not words:
        return []
    # Count word frequencies and return the top 5
    counter = Counter([w for w in words if len(w) > 2]) # Ignore tiny words
    return [word for word, count in counter.most_common(5)]

def process_gold_layer():
    spark = create_spark_session()
    
    silver_path = f"s3a://{config.MINIO_SILVER_BUCKET}/cleaned_news"
    
    logger.info(f"Reading cleaned data from Silver layer: {silver_path}")
    try:
        df = spark.read.parquet(silver_path)
    except Exception as e:
        logger.error(f"Failed to read from Silver layer. Ensure the job ran previously. Error: {e}")
        spark.stop()
        return

    # Base Transformations: Extract Domain and Publish Date
    df = df.withColumn("publish_date", to_date(col("published_at")))
    df = df.withColumn("source_domain", expr("parse_url(url, 'HOST')"))
    df = df.withColumn("word_count", expr("size(split(content, ' '))"))

    # =========================================================================
    # 1. gold_daily_trends
    # =========================================================================
    logger.info("Building gold_daily_trends table...")
    gold_daily_trends = df.groupBy("publish_date", "source_domain", "category").agg(
        count("*").alias("total_articles")
    )

    # =========================================================================
    # MLlib Text Processing (Tokenization -> StopWordsRemover)
    # =========================================================================
    logger.info("Applying PySpark MLlib for text processing...")
    # Tokenize the clean content
    tokenizer = Tokenizer(inputCol="content", outputCol="raw_words")
    wordsData = tokenizer.transform(df)
    
    # Remove English stopwords
    remover = StopWordsRemover(inputCol="raw_words", outputCol="filtered_words")
    cleanWordsData = remover.transform(wordsData)

    # Extract keywords using our UDF
    enriched_df = cleanWordsData.withColumn("extracted_keywords", extract_top_keywords(col("filtered_words")))

    # =========================================================================
    # 2. gold_articles_serving
    # =========================================================================
    logger.info("Building gold_articles_serving table...")
    gold_articles_serving = enriched_df.select(
        col("article_id"),
        col("published_at").cast("timestamp").alias("publish_timestamp"),
        col("source_domain"),
        col("title"),
        col("content").alias("clean_content"),
        col("word_count"),
        col("extracted_keywords")
    )

    # =========================================================================
    # 3. gold_entity_mentions
    # =========================================================================
    logger.info("Building gold_entity_mentions table...")
    # Explode the extracted keywords so each keyword gets its own row
    exploded_df = enriched_df.select(
        "publish_date", 
        "source_domain", 
        explode(col("extracted_keywords")).alias("entity_name")
    )
    
    # We assign 'KEYWORD' as the entity_type since we are using MLlib instead of full NER
    exploded_df = exploded_df.withColumn("entity_type", lit("KEYWORD"))

    gold_entity_mentions = exploded_df.groupBy("publish_date", "entity_name", "entity_type").agg(
        count("*").alias("mention_count")
    )

    # =========================================================================
    # Write to Gold layer
    # =========================================================================
    logger.info("Ensuring gold bucket exists...")
    minio_client = MinIOClient()
    minio_client.ensure_bucket_exists(config.MINIO_GOLD_BUCKET)

    gold_base_path = f"s3a://{config.MINIO_GOLD_BUCKET}"
    
    logger.info("Writing gold_daily_trends...")
    gold_daily_trends.write.mode("overwrite").parquet(f"{gold_base_path}/daily_trends")
    
    logger.info("Writing gold_articles_serving...")
    gold_articles_serving.write.mode("overwrite").parquet(f"{gold_base_path}/articles_serving")
    
    logger.info("Writing gold_entity_mentions...")
    gold_entity_mentions.write.mode("overwrite").parquet(f"{gold_base_path}/entity_mentions")

    logger.info("Gold Layer processing completed successfully!")
    spark.stop()

if __name__ == "__main__":
    process_gold_layer()
