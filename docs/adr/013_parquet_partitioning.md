# ADR 013: Strategic Parquet Partitioning

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
When Apache Spark processes data in the Gold layer, it writes the output as Parquet files to MinIO. 

If I dump 100,000 articles into a single folder, DuckDB has to scan the metadata of every single file whenever a user queries the dashboard for "What were the trends on Tuesday?" This full-table scan would eventually degrade performance as the Datalake grew.

I needed to implement Hive-style partitioning (e.g., `publish_date=2026-07-27/`), but I had to be careful not to trigger the "Small File Problem"—where Spark writes thousands of 2KB files, which causes a massive IO bottleneck when DuckDB tries to read them.

## 🤔 Considered Options
1. **No Partitioning:** Easy, but results in full-table scans for every query.
2. **Partition Everything by Date:** Good for time-series, but terrible for point-lookups (e.g., fetching a specific article by its ID).
3. **Strategic Partitioning:** Partition the aggregate tables by date, but leave the core serving table unpartitioned.

## ✅ Decision
I implemented **Strategic Partitioning** in `src/processing/gold_layer.py`.

1. **`gold_daily_trends` and `gold_entity_mentions`:** These tables are explicitly partitioned by `publish_date`. 
   * *Why?* Because the dashboard and the agents almost always query these tables using a date range. This allows DuckDB to perform *Partition Pruning* (ignoring folders outside the date range), ensuring queries take 50ms regardless of how large the total dataset grows.
2. **`gold_articles_serving`:** This table is **NOT** partitioned by date; it is simply appended to the root folder.
   * *Why?* When the AI Agent finds a relevant vector in Qdrant, it often wants to fetch the full text of that specific `article_id`. If the table was partitioned by date, DuckDB wouldn't know which folder to look in without scanning all of them. Furthermore, not partitioning keeps the Parquet file sizes large, which is optimal for read performance.

## 📈 Consequences
* **Positive:** Aggregation queries on the dashboard remain lightning fast regardless of dataset size.
* **Positive:** Avoids the Small File Problem in the massive `articles_serving` table.
* **Negative:** If I ever need to run a full text search across all articles in DuckDB (which I shouldn't, because that is what Qdrant is for), it will require a full table scan.

---
⬅️ **Previous:** [ADR 012: DuckDB Query Service](012_duckdb_query_service.md) | **Next:** [ADR 014: Markdown Export Design](014_pdf_export_design.md) ➡️

### 📚 Further Reading
* [16 - Performance and Scaling](../16_Performance_and_Scaling.md)
