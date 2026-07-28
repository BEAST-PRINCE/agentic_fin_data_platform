# ADR 001: Using DuckDB for Analytical Queries

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
As the Bronze and Silver layers of the data pipeline began to process tens of thousands of financial news articles, the AI agents needed a way to query the resulting structured data (the Gold layer) quickly. The standard industry approach is to load the transformed data from the Lakehouse into a traditional relational database (OLTP) like PostgreSQL or MySQL. 

However, spinning up a PostgreSQL container requires defining strict relational schemas, managing connections, and performing an additional heavy ETL step to copy data out of Parquet files and into Postgres tables. Furthermore, PostgreSQL struggles with fast analytical aggregations (OLAP) over millions of rows without heavy indexing and partitioning.

## 🤔 Considered Options
1. **PostgreSQL:** Industry standard, highly reliable. Poor OLAP performance out of the box. Requires data duplication (Lakehouse -> DB).
2. **ClickHouse:** Phenomenal OLAP speed. Requires a separate, heavy Docker container. Complex setup.
3. **DuckDB:** In-process OLAP engine. Reads Parquet files directly from S3/MinIO. No external server required.

## ✅ Decision
I chose **DuckDB** as the primary analytical query engine for the Gold layer.

Instead of running a database server, DuckDB runs directly inside the FastAPI backend process (`src/storage/db_client.py`). When the AI Agent Orchestrator requests data via MCP, DuckDB reaches directly into MinIO, queries the partitioned Parquet files using SQL, and returns the result in milliseconds. 

To handle FastAPI's asynchronous concurrency, I implemented a `threading.local()` connection pool, giving each API thread its own isolated, in-memory DuckDB connection.

## 📈 Consequences
* **Positive:** Absolute zero data duplication. The Spark jobs write Parquet files to MinIO, and DuckDB reads them natively. 
* **Positive:** Massive cost and resource savings. I don't have to run a dedicated 4GB RAM Postgres container.
* **Positive:** Vectorized execution makes aggregation queries (e.g., "average sentiment over 30 days") incredibly fast.
* **Negative:** DuckDB is primarily designed for single-node read workloads. It is not designed for high-concurrency *writes*. To mitigate this, DuckDB is used strictly in a read-only capacity in this project; Apache Spark handles all the heavy writes.

---
**Next:** [ADR 002: MinIO](002_minio.md) ➡️

### 📚 Further Reading
* [05 - Lakehouse](../05_Lakehouse.md)
* [16 - Performance and Scaling](../16_Performance_and_Scaling.md)
