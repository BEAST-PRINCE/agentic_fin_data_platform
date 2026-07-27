# Source Code (`src/`)

## 🎯 Why does this folder exist?

This is the brain and the engine of my entire Agentic Datalake project. Everything from the moment data is ingested, to the Spark pipelines that clean it, to the multi-agent AI system that reasons over it, lives right here in the `src/` directory.

I structured this directory to clearly separate concerns. Instead of a messy monolith where AI code gets tangled with database logic, I broke it down into logical domains.

## 🧱 Internal Structure & Responsibilities

Here is how I organized the code:

* **`agents/`** - The multi-agent AI system. This is where my Planner, Researcher, Summarizer, and Analyst live and coordinate.
* **`common/`** - Shared utilities, configurations, and logging setup that every other module relies on.
* **`ingestion/`** - The entry point for data. Contains Kafka producers that push raw scraped data into the pipeline.
* **`processing/`** - The Lakehouse engine. Here you'll find my PySpark jobs that transform data through the Bronze, Silver, and Gold layers.
* **`scrapers/`** - The data gatherers. Scripts that pull raw financial news and information from the web.
* **`serving/`** - The FastAPI backend. This serves my React dashboard and exposes the MCP (Model Context Protocol) tools my agents use.
* **`storage/`** - The database interaction layer. Contains my DuckDB and Qdrant integration logic for structured and semantic querying.

## 🔄 Data Flow

When looking at the `src/` directory, the general flow of data looks like this:

`scrapers/` ➔ `ingestion/` (Kafka) ➔ `processing/` (Spark/Lakehouse) ➔ `storage/` (DuckDB/Qdrant) ➔ `serving/` (FastAPI/MCP) ➔ `agents/` (AI Reasoning)

## 🐛 Debugging Tips

If you (or future me) are debugging an issue in this directory, always trace the data backward:
1. **Agent saying something weird?** Check `agents/`.
2. **Agent missing a tool?** Check `serving/` (where MCP tools are defined).
3. **Data missing from the tool?** Check `storage/` (DuckDB/Qdrant queries).
4. **Data corrupted in the database?** Check `processing/` (Spark jobs).
5. **No data at all?** Check `scrapers/` and `ingestion/`.
