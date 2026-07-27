# 04 - Data Pipeline

If you want to build an AI that can answer questions about data, the AI is only going to be as good as the data you feed it. 

I didn't want my agents guessing or hallucinating based on messy, unstructured web scrapes. I needed a rigorous, industrial-grade data pipeline to clean and organize the data *before* the agents ever saw it. 

To do this, I implemented the **Medallion Architecture**, a data design pattern popularized by Databricks, using Apache Spark. 

Here is how data travels from chaos to clarity.

## 🥉 The Bronze Layer (Raw & Unfiltered)

**Purpose:** To land data as quickly and safely as possible without losing any historical context.

**The Process:**
When the scrapers run, they publish JSON messages to Kafka. The Bronze PySpark job acts as a Kafka consumer. It reads these messages in micro-batches and writes them directly into the MinIO object store (`bronze` bucket).

**Rules of Bronze:**
1. **No schema enforcement:** If a scraper accidentally sends a string instead of an integer for a timestamp, Bronze doesn't care. It accepts everything.
2. **Append-only:** We never update or delete records in Bronze. It is a pure, immutable historical log.
3. **Format:** Usually stored as raw JSON or basic unoptimized Parquet.

**Why it exists:** If a bug in my downstream cleaning logic accidentally deletes half my data, I can always return to the Bronze layer and replay the history to rebuild the database perfectly.

## 🥈 The Silver Layer (Cleaned & Validated)

**Purpose:** To turn raw data into something you can actually query.

**The Process:**
The Silver PySpark job reads the messy data from the Bronze bucket and goes to work. 

**Rules of Silver:**
1. **Schema Enforcement:** Here, we demand structure. Dates must be actual Timestamp objects. Prices must be Floats. If a record doesn't match the schema, it is quarantined or dropped.
2. **Deduplication:** Scrapers often pull the same news article twice. Silver identifies duplicates based on URL or article ID and keeps only the latest version.
3. **Data Cleaning:** Standardizing company tickers (e.g., changing "Apple Inc." to "AAPL"), stripping out HTML tags from article text, and handling null values.
4. **Format:** Stored as highly compressed, columnar Parquet files.

**Why it exists:** Data scientists and analysts (or in our case, AI Analyst Agents) shouldn't have to write `IF NULL THEN...` logic in every single query. Silver ensures the data is trustworthy.

## 🥇 The Gold Layer (Business-Ready & Optimized)

**Purpose:** To structure the data specifically for the exact questions the AI agents will ask, and to optimize it for blazing-fast retrieval.

**The Process:**
The Gold PySpark job reads from Silver and performs business-level aggregations. 

**Rules of Gold:**
1. **Aggregations:** Instead of just having a table of individual stock trades, Gold might create a table of "Daily Volatility by Ticker." 
2. **Join Denormalization:** If an agent needs to know a company's sector and its recent news, we don't want DuckDB doing massive joins on the fly. Gold joins the `companies` table with the `news` table to create wide, ready-to-read datasets.
3. **Partitioning:** The Parquet files are heavily partitioned (usually by `date` and `ticker`). This is critical. When DuckDB asks for Apple news from yesterday, partitioning allows it to skip reading 99% of the files in the Lakehouse, returning the answer in milliseconds.
4. **Vector Prep:** This is also where the text data is prepared for the semantic pipeline (extracting keywords with KeyBERT) before being sent to Qdrant.

**Why it exists:** AI agents have a limited context window and a limited attention span. Gold ensures they get exactly the data they need, formatted perfectly, instantly.

---
⬅️ **Previous:** [03 - System Architecture](03_System_Architecture.md) | **Next:** [05 - Lakehouse](05_Lakehouse.md) ➡️
