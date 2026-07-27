# 05 - Lakehouse Architecture

When I started this project, I could have just dumped everything into a PostgreSQL database and called it a day. That's what most tutorials do. 

But I knew that if the system scaled—if I started scraping tens of thousands of articles and market data points—a traditional row-based SQL database would start choking when my AI agents tried to run heavy analytical aggregations over years of historical data.

So, I built a Lakehouse. 

A Lakehouse combines the massive, cheap scalability of a Data Lake with the ACID transactions and SQL querying capabilities of a Data Warehouse. 

Here is how I implemented it entirely locally, for free.

## 🪣 The Storage: MinIO

Instead of saving files to a local hard drive folder, I use **MinIO**. 

MinIO is a high-performance object storage server that is API-compatible with Amazon S3. 
* **Why it matters:** By using MinIO, my code interacts with the storage exactly as if it were running on a massive AWS cluster. I use `s3a://` paths in my Spark code. If I ever decide to deploy this to the cloud, I don't have to rewrite a single line of storage logic. I just swap the endpoint URL.
* **Structure:** I have three main "buckets" in MinIO: `bronze`, `silver`, and `gold`.

## 📄 The Format: Parquet

I don't store data in CSVs or JSON (except initially in Bronze). I use **Apache Parquet**.

Parquet is a columnar storage format. 
* If you have a table with 100 columns and 1 million rows, and an AI agent runs a SQL query that only needs 2 columns (like `date` and `closing_price`), a CSV requires the engine to read the entire massive file into memory. 
* Parquet stores data by column, not by row. The query engine only reads the 2 columns it needs from disk, ignoring the other 98. It is orders of magnitude faster and heavily compressed.

## 🦆 The Query Engine: DuckDB

This is the secret weapon of the project.

I do not use a traditional database server to query the Gold layer. I use **DuckDB**.

DuckDB is an in-process SQL OLAP (Online Analytical Processing) database management system. 
* It doesn't run as a separate server container that you connect to via TCP/IP. 
* It runs *inside* the Python FastAPI process. 
* When the FastAPI backend receives a query, DuckDB reaches out over the network directly into MinIO, grabs the specific Parquet files it needs, runs the SQL query in-memory using vectorized execution, and returns the result to the AI agent.

### Why DuckDB over PostgreSQL?
1. **Analytical Speed:** PostgreSQL is an OLTP (transactional) database. It's great for finding one specific user by ID. DuckDB is an OLAP database. It is designed to aggregate millions of rows ("What is the average sentiment for AAPL over the last 30 days?") incredibly fast.
2. **Zero Management:** There are no users, roles, or vacuuming processes to manage. It's just a Python library that reads files.
3. **Native S3 & Parquet:** DuckDB can query an S3 bucket of Parquet files directly with standard SQL, utilizing pushdown optimizations (like only downloading the exact partitions needed).

## 🗂️ The Crucial Concept: Partitioning

If you dump a million Parquet files into a single Gold folder, DuckDB will still be slow. The key to Lakehouse performance is **partitioning**.

When my Spark jobs write to the Gold layer, they organize the files in a folder structure like this:
```
gold/market_data/
  year=2026/
    month=07/
      ticker=AAPL/
        data.parquet
      ticker=MSFT/
        data.parquet
```

If my AI agent executes:
```sql
SELECT avg(price) FROM gold_data WHERE year=2026 AND month=07 AND ticker='AAPL';
```
DuckDB looks at the query, looks at the folder structure, and realizes it can completely ignore 99.9% of the files in MinIO. It only downloads the one tiny `data.parquet` file inside the `ticker=AAPL` folder. 

This is how you achieve sub-second analytical queries on massive datasets without paying for Snowflake.

---
⬅️ **Previous:** [04 - Data Pipeline](04_Data_Pipeline.md) | **Next:** [06 - Semantic Search](06_Semantic_Search.md) ➡️
