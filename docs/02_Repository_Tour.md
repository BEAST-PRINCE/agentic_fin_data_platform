# 02 - Repository Tour

If you just cloned the repository, your file explorer probably looks a bit overwhelming. There are a lot of folders. 

I designed this project to be highly modular. I hate monoliths where a single `app.py` file contains database connections, API routes, and HTML templates. 

Let's take a guided tour of the codebase so you know exactly what lives where, and more importantly, *why* it lives there.

## 🗂️ The Top-Level Folders

### `docs/`
You are here. This contains the comprehensive documentation for the project. I treat docs as code.

### `docker-compose.yml`, `Dockerfile.spark`, `prometheus/`, and `grafana/`
These are the infrastructure files. The Compose file and Spark image definition live at the repository root; `prometheus/` and `grafana/` contain observability configuration. The `infra/` directory currently contains supporting documentation rather than the Compose file itself.

### `scripts/`
Contains the automated orchestration scripts (`start.ps1`, `stop.ps1`, `restart.ps1`, `start.sh`, `stop.sh`, `restart.sh`, and `healthcheck.py`) for one-command startup, shutdown, health monitoring, and logging.

### `dashboard/`
This is the frontend. It is a React application that provides the chat interface and data visualizations. If you want to change the color of a button or tweak how the agent's reasoning is displayed, this is where you go.

### `tests/`
The test directory contains focused Python tests for schema helpers, lakehouse statistics, MCP behavior, and multi-agent module structure. `pytest` is not currently pinned in `requirements.txt`, and the tests are not yet organized into a complete unit/integration/agent taxonomy.

### `data/` and `notebooks/`
These are mostly for local exploration. 
* `data/` is often used as a local mount point for Docker volumes so that MinIO data persists between restarts. 
* `notebooks/` contains Jupyter notebooks I used for prototyping Spark jobs and embedding models before moving them into production code.

### `src/` - The Core Engine
This is where the actual Python backend lives. It is so important that I broke it down further.

## 🔬 Inside the `src/` Directory

If `src/` is the engine, here are its cylinders:

* **`src/ingestion/scrapers/`**: The Scrapy project and spiders that pull financial news from the web.
* **`src/ingestion/`**: Kafka producers and consumers. Scrapers publish normalized payloads; the Bronze consumer writes them to MinIO.
* **`src/processing/`**: The Apache Spark Silver/Gold transformation and vector-indexing jobs. Bronze landing is implemented under `src/ingestion/kafka/`.
* **`src/storage/`**: The database clients. Contains the logic for querying DuckDB (for structured Parquet files) and Qdrant (for vector embeddings).
* **`src/serving/`**: The FastAPI backend. This exposes the API endpoints for the dashboard and defines the MCP tools that the agents are allowed to use.
* **`src/serving/agent/`**: The Solo Agent and Multi-Agent prompts, runners, memory, and orchestration logic.
* **`src/common/`**: Shared utilities like logging setup and `.env` configuration parsing.

## 🔗 How It All Connects

If you want to trace a piece of data through the entire repository, follow this path:

1. A spider in `src/ingestion/scrapers/scrapy_project/scrapy_project/spiders/` finds a news article.
2. It passes it to `src/ingestion/` which sends it to Kafka.
3. The Python consumer in `src/ingestion/kafka/bronze_consumer.py` reads it from Kafka and saves it to MinIO (`docker-compose.yml` runs MinIO locally).
4. Eventually, a user types a query into the `dashboard/`.
5. The dashboard sends an HTTP request to `src/serving/`.
6. `src/serving/` wakes up the `src/agents/`.
7. The agent uses a tool from `src/serving/`, which calls `src/storage/` to query the data from MinIO using DuckDB.
8. The result flows all the way back up to the `dashboard/`.

Everything has a specific place. If you keep this mental map, you'll never get lost.

---
⬅️ **Previous:** [01 - Project Overview](01_Project_Overview.md) | **Next:** [03 - System Architecture](03_System_Architecture.md) ➡️
