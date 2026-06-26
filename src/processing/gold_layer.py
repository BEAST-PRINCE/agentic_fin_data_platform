import os
import sys
from collections import Counter
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, expr, explode, count, lit, size, pandas_udf
import pandas as pd
from pyspark.sql.types import ArrayType, StringType, StructType, StructField, DateType, IntegerType, TimestampType
from pyspark.ml.feature import Tokenizer, StopWordsRemover

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.common import config
from src.common.logger import get_logger
from src.storage.minio_client import MinIOClient
from src.storage.lakehouse_stats import add_gold_records

logger = get_logger(__name__)

def create_spark_session() -> SparkSession:
    logger.info("Initializing Spark Session for Gold Layer...")
    endpoint = f"http://{config.MINIO_ENDPOINT}" if not config.MINIO_SECURE else f"https://{config.MINIO_ENDPOINT}"
    spark = SparkSession.builder \
        .appName("SilverToGoldProcessing") \
        .master("local[1]") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
        .config("spark.sql.execution.arrow.maxRecordsPerBatch", "10") \
        .config("spark.hadoop.fs.s3a.endpoint", endpoint) \
        .config("spark.hadoop.fs.s3a.access.key", config.MINIO_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", config.MINIO_SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", str(config.MINIO_SECURE).lower()) \
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic") \
        .getOrCreate()
    return spark

# Semantic keyword extraction using KeyBERT
_kw_model = None

@pandas_udf(ArrayType(StringType()))
def extract_semantic_keywords(title_series: pd.Series, desc_series: pd.Series, content_series: pd.Series) -> pd.Series:
    global _kw_model
    if _kw_model is None:
        try:
            from keybert import KeyBERT
            import torch
            # Initialize safely on workers
            _kw_model = KeyBERT('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Failed to load KeyBERT: {e}")
            return pd.Series([[] for _ in range(len(title_series))])
            
    # Vectorized string concatenation using Pandas
    texts = (title_series.fillna("") + " " + desc_series.fillna("") + " " + content_series.fillna("")).str.strip()
    texts_list = texts.tolist()
    
    if not texts_list:
        return pd.Series([])
        
    try:
        # KeyBERT automatically batch-processes lists on the GPU! Massive speedup.
        if len(texts_list) == 1:
            kws = [_kw_model.extract_keywords(texts_list[0], keyphrase_ngram_range=(1, 2), stop_words='english', top_n=5)]
        else:
            kws = _kw_model.extract_keywords(texts_list, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=5)
            
        results = [[kw[0] for kw in item] if isinstance(item, list) else [] for item in kws]
    except Exception as e:
        logger.error(f"Error during batch extraction: {e}")
        results = [[] for _ in texts_list]
        
    return pd.Series(results)

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

    gold_base_path = f"s3a://{config.MINIO_GOLD_BUCKET}"

    # =========================================================================
    # Incremental Processing Logic
    # =========================================================================
    try:
        # Try to read existing Gold data to find the latest processed date
        existing_gold = spark.read.parquet(f"{gold_base_path}/articles_serving")
        max_date_row = existing_gold.agg({"publish_timestamp": "max"}).collect()[0]
        max_date = max_date_row[0] if max_date_row else None
    except Exception as e:
        logger.error(f"Failed to read existing Gold data: {e}")
        # Gold bucket or table might not exist yet
        max_date = None

    if max_date:
        logger.info(f"Incremental mode: Processing only records after {max_date}")
        df = df.filter(col("published_at") > lit(max_date))
    else:
        logger.info("Full load mode: Processing all records")

    if df.rdd.isEmpty():
        logger.info("No new records to process. Exiting.")
        spark.stop()
        return

    # =========================================================================
    # 1. gold_daily_trends
    # =========================================================================
    logger.info("Building gold_daily_trends table...")
    gold_daily_trends = df.groupBy("publish_date", "source_domain", "category").agg(
        count("*").alias("total_articles")
    )
    
    # DQ Gate & Schema Enforcement
    gold_daily_trends = gold_daily_trends.filter(col("total_articles") > 0).select(
        col("publish_date").cast(DateType()),
        col("source_domain").cast(StringType()),
        col("category").cast(StringType()),
        col("total_articles").cast(IntegerType())
    )

    # =========================================================================
    # Semantic Keyword Extraction
    # =========================================================================
    logger.info("Applying KeyBERT for semantic keyword extraction...")
    
    # Check if 'description' exists in source, otherwise pass null
    desc_col = col("description") if "description" in df.columns else lit(None).cast(StringType())
    
    enriched_df = df.withColumn("source_tags", col("tags")) \
                    .withColumn("semantic_keywords", extract_semantic_keywords(col("title"), desc_col, col("content")))
    
    # DQ Gate: Ensure we don't fail if semantic_keywords is empty (can happen on model load failure)
    # We allow articles with empty semantic_keywords to pass through if source_tags exist.
    enriched_df = enriched_df.filter((size(col("source_tags")) > 0) | (size(col("semantic_keywords")) > 0))

    # CRITICAL FIX: Cache the dataframe! 
    # Because we use this dataframe multiple times below (for articles_serving AND entity_mentions),
    # Spark will lazily re-run the entire KeyBERT extraction multiple times if we don't cache it!
    enriched_df.cache()

    # =========================================================================
    # 2. gold_articles_serving
    # =========================================================================
    logger.info("Building gold_articles_serving table...")
    
    # Schema Enforcement
    gold_articles_serving = enriched_df.select(
        col("article_id").cast(StringType()),
        col("published_at").cast(TimestampType()).alias("publish_timestamp"),
        col("source_domain").cast(StringType()),
        col("title").cast(StringType()),
        col("content").cast(StringType()).alias("clean_content"),
        col("word_count").cast(IntegerType()),
        col("source_tags").cast(ArrayType(StringType())),
        col("semantic_keywords").cast(ArrayType(StringType()))
    )

    # =========================================================================
    # 3. gold_entity_mentions
    # =========================================================================
    logger.info("Building gold_entity_mentions table...")
    # Explode both source tags and semantic keywords to count mentions
    exploded_tags = enriched_df.select(
        "publish_date", 
        "source_domain", 
        explode(col("source_tags")).alias("entity_name")
    ).withColumn("entity_type", lit("SOURCE_TAG"))
    
    exploded_keywords = enriched_df.select(
        "publish_date", 
        "source_domain", 
        explode(col("semantic_keywords")).alias("entity_name")
    ).withColumn("entity_type", lit("SEMANTIC_KEYWORD"))
    
    exploded_df = exploded_tags.union(exploded_keywords)
    

    gold_entity_mentions = exploded_df.groupBy("publish_date", "entity_name", "entity_type").agg(
        count("*").alias("mention_count")
    )
    
    # Schema Enforcement
    gold_entity_mentions = gold_entity_mentions.filter(col("mention_count") > 0).select(
        col("publish_date").cast(DateType()),
        col("entity_name").cast(StringType()),
        col("entity_type").cast(StringType()),
        col("mention_count").cast(IntegerType())
    )

    # =========================================================================
    # Write to Gold layer with Partitioning and Append Mode
    # =========================================================================
    logger.info("Ensuring gold bucket exists...")
    minio_client = MinIOClient()
    minio_client.ensure_bucket_exists(config.MINIO_GOLD_BUCKET)

    write_mode = "append"
    gold_serving_count = gold_articles_serving.count()

    logger.info("Writing gold_daily_trends...")
    gold_daily_trends.write.mode("overwrite").partitionBy("publish_date").parquet(f"{gold_base_path}/daily_trends")
    # gold_daily_trends.write.mode(write_mode).partitionBy("publish_date").parquet(f"{gold_base_path}/daily_trends")
    
    logger.info("Writing gold_articles_serving...")
    # Not partitioning articles by date to avoid small files and keep lookup fast by ID, but can partition if desired.
    gold_articles_serving.write.mode("append").parquet(f"{gold_base_path}/articles_serving")
    # gold_articles_serving.write.mode(write_mode).parquet(f"{gold_base_path}/articles_serving")
    
    logger.info("Writing gold_entity_mentions...")
    gold_entity_mentions.write.mode("overwrite").partitionBy("publish_date").parquet(f"{gold_base_path}/entity_mentions")
    # gold_entity_mentions.write.mode(write_mode).partitionBy("publish_date").parquet(f"{gold_base_path}/entity_mentions")

    add_gold_records(gold_serving_count)

    logger.info("Gold Layer processing completed successfully!")
    spark.stop()

# =========================================================================
# Deprecated MLlib Logic 
# =========================================================================
# # Lightweight UDF to extract top N keywords from an array of filtered words
# @udf(returnType=ArrayType(StringType()))
# def extract_top_keywords(words):
#     if not words:
#         return []
#     # Count word frequencies and return the top 5
#     counter = Counter([w for w in words if len(w) > 2]) # Ignore tiny words
#     return [word for word, count in counter.most_common(5)]
#
# # Tokenize the clean content
# tokenizer = Tokenizer(inputCol="content", outputCol="raw_words")
# wordsData = tokenizer.transform(df)
# 
# # Remove English stopwords
# remover = StopWordsRemover(inputCol="raw_words", outputCol="filtered_words")
# cleanWordsData = remover.transform(wordsData)
#
# # Extract keywords using our UDF
# enriched_df = cleanWordsData.withColumn("extracted_keywords", extract_top_keywords(col("filtered_words")))

if __name__ == "__main__":
    process_gold_layer()
