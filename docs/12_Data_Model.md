# 12 - Data Model

Because this project is built on a Lakehouse rather than a traditional relational database, the data model isn't just a set of static SQL tables. It is an *evolution*. 

Data enters the system as messy, unstructured text and slowly transforms into clean tabular data and multi-dimensional vectors. Here is the exact schema evolution based on the `src/processing/` layer jobs.

## 🥉 Bronze Layer: The Raw Scrape

When the scraper hits a news site, it pulls whatever it can find. We dump this into MinIO (`raw_news/`) as JSON. There is no strict schema enforcement here, but the JSON payloads generally contain these keys:

* `article_id`
* `title`
* `content`
* `source`
* `url`
* `description` (optional)
* `tags` (optional array)
* `published_at` (raw string format)

## 🥈 Silver Layer: The Cleanup (`silver_layer.py`)

The Spark job picks up the Bronze JSON, ensures critical fields aren't null, drops short articles, deduplicates, and writes it out as columnar Parquet files (`cleaned_news`).

**Cleaning Logic applied:**
* Drop records with nulls in `title`, `content`, or `source`.
* Filter out articles with less than 60 words in `content`.
* Drop duplicates based on `article_id`.

*The output schema matches the incoming Bronze structure but guarantees cleanliness.*

## 🥇 Gold Layer: Business & AI Ready (`gold_layer.py`)

The Gold layer is where we prepare the data for the retrieval engines: DuckDB (tabular) and Qdrant (vectors). It outputs three highly structured Parquet tables.

### 1. `gold_articles_serving`
This is the core table used when retrieving article details.
* `article_id` (String)
* `publish_timestamp` (Timestamp)
* `source_domain` (String) - Extracted from the URL host.
* `title` (String)
* `clean_content` (String)
* `word_count` (Integer)
* `source_tags` (Array of Strings) - The original tags from the scraper.
* `semantic_keywords` (Array of Strings) - Keywords extracted via the KeyBERT ML model.

### 2. `gold_daily_trends`
Aggregated table partitioned by `publish_date`. Used for dashboard charts.
* `publish_date` (Date)
* `source_domain` (String)
* `category` (String)
* `total_articles` (Integer)

### 3. `gold_entity_mentions`
A flattened, exploded table used to quickly see which entities (companies, themes) were talked about on a specific day. Partitioned by `publish_date`.
* `publish_date` (Date)
* `entity_name` (String) - Can be from `source_tags` or `semantic_keywords`.
* `entity_type` (String) - E.g., `"SOURCE_TAG"` or `"SEMANTIC_KEYWORD"`.
* `mention_count` (Integer)

## 🎯 The Vector Payload (`vector_indexer.py`)

The `vector_indexer.py` job queries `gold_articles_serving` via DuckDB, generates 384-dimensional embeddings using `sentence-transformers`, and stores them in Qdrant. 

Alongside the raw vector, it stores this exact JSON Payload in Qdrant so the Agent receives immediate context on a similarity match:

```json
{
  "title": "...",
  "source_domain": "...",
  "publish_timestamp": "...",
  "source_tags": ["...", "..."],
  "semantic_keywords": ["...", "..."]
}
```
*(Note: `article_id` is passed as the native Qdrant Point ID)*

By attaching this payload directly to the vector, the AI agent instantly receives the `publish_timestamp`, `source_domain`, and critical keywords without having to perform a secondary, slower lookup against the DuckDB tables.

---
⬅️ **Previous:** [11 - API Reference](11_API_Reference.md) | **Next:** [13 - Technology Stack](13_Technology_Stack.md) ➡️
