# 16 - Performance and Scaling

Building a toy AI that queries a 10-row CSV is easy. Building a system that handles thousands of articles, semantic indexing, and multi-agent orchestration locally requires aggressive performance tuning.

Here is how I squeezed every drop of performance out of this architecture.

## 🦆 DuckDB: Thread-Local Connections

FastAPI is highly concurrent. If ten users (or ten agents) hit the API simultaneously, they shouldn't block each other.

However, DuckDB is an in-memory OLAP engine. If you create a single global DuckDB connection and share it across all FastAPI async workers, they will queue up and execute sequentially. 

**The Fix:** I implemented a `threading.local()` connection pool in `src/storage/db_client.py`. Every time a FastAPI background thread needs to query the Gold Lakehouse, it gets its own dedicated, isolated DuckDB connection. This allows massive concurrent read throughput without locks.

## 🚀 KeyBERT: GPU Batch Processing

During the Gold layer processing (`src/processing/gold_layer.py`), I use KeyBERT to extract semantic keywords from every article. Running NLP models row-by-row in Python is painfully slow.

**The Fix:** Instead of passing strings one at a time, I built a PySpark `pandas_udf`. This passes batches of the DataFrame to KeyBERT as Pandas Series. The embedder falls back to CPU when CUDA is unavailable; the repository does not include a benchmark proving a fixed speedup.

## 🗂️ Spark Parquet Partitioning

If DuckDB has to scan 10GB of Parquet files to find articles from yesterday, it will be slow, even with vectorization.

**The Fix:** The Gold layer explicitly partitions the `gold_daily_trends` and `gold_entity_mentions` tables by `publish_date` when writing to MinIO. 
```python
gold_daily_trends.write.partitionBy("publish_date").parquet(...)
```
When DuckDB executes a query filtered by `publish_date`, the Hive-style layout can enable *Partition Pruning*. The actual improvement depends on object count, data volume, MinIO latency, and query shape; this repository does not include a benchmark supporting a fixed latency.

*(Note: I intentionally chose NOT to partition `gold_articles_serving` by date, because the agents usually query it by `article_id` from the Qdrant payload, and over-partitioning would lead to the "Small File Problem".)*

## 🤖 Multi-Agent Latency

The biggest bottleneck in this entire system is the Large Language Model. Generating tokens takes time. The Multi-Agent pipeline (Planner -> Researcher -> Summarizer -> Analyst -> Synthesizer) can easily take 15-30 seconds.

**The Fix:** 
1. **Parallel Execution (Future):** The Planner currently outputs a list of tasks. While they are currently executed sequentially by the Researcher, the architecture supports executing them concurrently in the future.
2. **Dashboard UX:** To mask the latency, the React dashboard doesn't just show a spinner. It exposes the live JSON state changes in the Workflow Accordion, giving the user immediate visual feedback that work is being done.

---
⬅️ **Previous:** [15 - Developer Journey](15_Developer_Journey.md) | **Next:** [17 - Troubleshooting](17_Troubleshooting.md) ➡️
