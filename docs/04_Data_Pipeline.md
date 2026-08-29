# 04 - Data Pipeline

If you want to build an AI that can answer questions about data, the AI is only going to be as good as the data you feed it. 

I didn't want my agents guessing or hallucinating based on messy, unstructured web scrapes. I needed a rigorous, industrial-grade data pipeline to clean and organize the data *before* the agents ever saw it. 

To do this, I implemented a **Medallion Architecture** using MinIO and Apache Spark for Silver/Gold processing. Kafka-to-Bronze landing is handled by a Python consumer.

Here is how data travels from chaos to clarity.

## 🥉 The Bronze Layer (Raw & Unfiltered)

**Purpose:** To land data as quickly and safely as possible without losing any historical context.

**The Process:**
When the scrapers run, they publish normalized JSON messages to Kafka. `src/ingestion/kafka/bronze_consumer.py` consumes them and writes one JSON object per article into the MinIO `bronze` bucket using Hive-style source/date partitions.

**Rules of Bronze:**
1. **No schema enforcement:** If a scraper accidentally sends a string instead of an integer for a timestamp, Bronze doesn't care. It accepts everything.
2. **Append-only:** We never update or delete records in Bronze. It is a pure, immutable historical log.
3. **Format:** Raw JSON objects under `raw_news/source=.../year=.../month=.../day=.../`.

**Why it exists:** If a bug in my downstream cleaning logic accidentally deletes half my data, I can always return to the Bronze layer and replay the history to rebuild the database perfectly.

## 🥈 The Silver Layer (Cleaned & Validated)

**Purpose:** To turn raw data into something you can actually query.

**The Process:**
The Silver PySpark job reads the messy data from the Bronze bucket and goes to work. 

**Rules of Silver:**
1. **Required-field filtering:** Records missing `title`, `content`, or `source` are dropped.
2. **Content filtering:** Articles with fewer than 60 space-separated words are dropped.
3. **Deduplication:** Duplicate records are removed using `article_id`.
4. **Format:** Stored as highly compressed, columnar Parquet files.

**Why it exists:** Data scientists and analysts (or in our case, AI Analyst Agents) shouldn't have to write `IF NULL THEN...` logic in every single query. Silver ensures the data is trustworthy.

## 🥇 The Gold Layer (Business-Ready & Optimized)

**Purpose:** To structure the data specifically for the exact questions the AI agents will ask, and to optimize it for blazing-fast retrieval.

**The Process:**
The Gold PySpark job reads from Silver and performs business-level aggregations. 

**Rules of Gold:**
1. **Serving table:** `articles_serving` contains article-level fields used by the API and vector indexer.
2. **Aggregations:** `daily_trends` groups article counts by date, source domain, and category; `entity_mentions` counts source tags and semantic keywords.
3. **Partitioning:** The two aggregate tables are partitioned by `publish_date`. `articles_serving` is not date-partitioned.
4. **Vector prep:** Gold extracts KeyBERT keywords. `vector_indexer.py` separately embeds Gold articles and upserts them into Qdrant.

> **Important operational note:** The current Gold job filters to new records but overwrites the aggregate output paths. Treat this as a known correctness limitation until aggregate partitions are merged or recomputed safely.

**Why it exists:** AI agents have a limited context window and a limited attention span. Gold ensures they get exactly the data they need, formatted perfectly, instantly.

---
⬅️ **Previous:** [03 - System Architecture](03_System_Architecture.md) | **Next:** [05 - Lakehouse](05_Lakehouse.md) ➡️
