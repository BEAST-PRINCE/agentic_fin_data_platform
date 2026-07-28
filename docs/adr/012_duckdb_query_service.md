# ADR 012: DuckDB as a Direct API Service

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
DuckDB was originally introduced purely for the AI Agents. The Researcher agent needed a way to query the Gold Lakehouse via MCP. 

However, as I built the React Dashboard, I needed to display system statistics, daily trending topics, and throughput metrics on the homepage *before* the user even asked a question. 

I had two choices: I could either build a separate database (like Postgres) just for the UI, or I could figure out how to safely expose DuckDB directly to the FastAPI REST endpoints (`/api/system/statistics`, `/trending`) so the React dashboard could query it.

## 🤔 Considered Options
1. **Dual Databases:** Keep DuckDB for the AI, spin up Postgres for the dashboard. (Rejected: Violates the Single Source of Truth principle).
2. **Global DuckDB Connection:** Open one DuckDB connection in FastAPI and let all endpoints use it. (Rejected: Causes thread locks and crashes when multiple users hit the dashboard simultaneously).
3. **Thread-Local DuckDB Connections:** Give every FastAPI worker thread its own isolated DuckDB connection pointing at the same MinIO bucket.

## ✅ Decision
I implemented **Thread-Local DuckDB connections** inside `src/storage/db_client.py`. 

By using `threading.local()`, every time an API endpoint is hit, it checks if the current thread has a DuckDB connection. If not, it creates an in-memory connection and configures the `httpfs` extension to read from MinIO. 

This allows the FastAPI application to act as a highly concurrent analytical query service. The React dashboard hits `/trending`, FastAPI executes a fast DuckDB SQL query against MinIO, and returns the JSON directly to the frontend.

## 📈 Consequences
* **Positive:** The dashboard is incredibly fast. DuckDB aggregates thousands of rows in milliseconds, allowing the React charts to render instantly on page load.
* **Positive:** Architecture remains simple. No extra databases were added just to support the UI.
* **Negative:** Slight memory overhead. If FastAPI scales to 10 workers, there are 10 separate DuckDB in-memory instances running simultaneously in the backend process. Given the read-only nature of the queries, this is currently an acceptable trade-off.

---
⬅️ **Previous:** [ADR 011: Dashboard Redesign](011_dashboard_redesign.md) | **Next:** [ADR 013: Parquet Partitioning](013_parquet_partitioning.md) ➡️

### 📚 Further Reading
* [16 - Performance and Scaling](../16_Performance_and_Scaling.md)
