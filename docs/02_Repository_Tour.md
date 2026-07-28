# 02 - Repository Tour

If you just cloned the repository, your file explorer probably looks a bit overwhelming. There are a lot of folders. 

I designed this project to be highly modular. I hate monoliths where a single `app.py` file contains database connections, API routes, and HTML templates. 

Let's take a guided tour of the codebase so you know exactly what lives where, and more importantly, *why* it lives there.

## 🗂️ The Top-Level Folders

### `docs/`
You are here. This contains the comprehensive documentation for the project. I treat docs as code.

### `infra/`
This is the infrastructure-as-code folder. The most important file here is `docker-compose.yml`. This folder is responsible for spinning up the local services (MinIO, Kafka, Qdrant, Prometheus). It doesn't contain application logic; it contains the environment.

### `scripts/`
Contains the automated orchestration scripts (`start.ps1`, `stop.ps1`, `restart.ps1`, `start.sh`, `stop.sh`, `restart.sh`, and `healthcheck.py`) for one-command startup, shutdown, health monitoring, and logging.

### `dashboard/`
This is the frontend. It is a React application that provides the chat interface and data visualizations. If you want to change the color of a button or tweak how the agent's reasoning is displayed, this is where you go.

### `tests/`
The automated testing suite. I use Pytest to ensure that adding a new agent doesn't accidentally break the DuckDB querying engine. It is separated into unit, integration, and agent testing.

### `data/` and `notebooks/`
These are mostly for local exploration. 
* `data/` is often used as a local mount point for Docker volumes so that MinIO data persists between restarts. 
* `notebooks/` contains Jupyter notebooks I used for prototyping Spark jobs and embedding models before moving them into production code.

### `src/` - The Core Engine
This is where the actual Python backend lives. It is so important that I broke it down further.

## 🔬 Inside the `src/` Directory

If `src/` is the engine, here are its cylinders:

* **`src/scrapers/`**: The very beginning of the pipeline. Scripts that pull data from the web.
* **`src/ingestion/`**: The Kafka producers. They take the scraped data and push it into the message queue.
* **`src/processing/`**: The Apache Spark Lakehouse jobs. This is where data gets moved through the Bronze, Silver, and Gold layers.
* **`src/storage/`**: The database clients. Contains the logic for querying DuckDB (for structured Parquet files) and Qdrant (for vector embeddings).
* **`src/serving/`**: The FastAPI backend. This exposes the API endpoints for the dashboard and defines the MCP tools that the agents are allowed to use.
* **`src/agents/`**: The Multi-Agent AI system. This holds the prompts, logic, and orchestrator for the Planner, Researcher, Analyst, and Summarizer.
* **`src/common/`**: Shared utilities like logging setup and `.env` configuration parsing.

## 🔗 How It All Connects

If you want to trace a piece of data through the entire repository, follow this path:

1. A script in `src/scrapers/` finds a news article.
2. It passes it to `src/ingestion/` which sends it to Kafka.
3. A PySpark job in `src/processing/` reads it from Kafka and saves it to MinIO (`infra/` manages MinIO).
4. Eventually, a user types a query into the `dashboard/`.
5. The dashboard sends an HTTP request to `src/serving/`.
6. `src/serving/` wakes up the `src/agents/`.
7. The agent uses a tool from `src/serving/`, which calls `src/storage/` to query the data from MinIO using DuckDB.
8. The result flows all the way back up to the `dashboard/`.

Everything has a specific place. If you keep this mental map, you'll never get lost.

---
⬅️ **Previous:** [01 - Project Overview](01_Project_Overview.md) | **Next:** [03 - System Architecture](03_System_Architecture.md) ➡️
