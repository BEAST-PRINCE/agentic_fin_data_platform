# Storage Integration (`src/storage/`)

## 🗄️ Why does this folder exist?

This folder is the data retrieval engine of the project. While `src/processing/` writes the data to the Lakehouse, `src/storage/` is responsible for reading it back out in a way that is incredibly fast and useful for my AI agents. I abstracted the database logic into this folder so the rest of the application doesn't have to care whether data lives in DuckDB, Qdrant, or a text file.

## 💾 Responsibilities & Internal Structure

I have two primary datastores, and this folder contains the client wrappers for both:

* **DuckDB Client:** The analytical engine. DuckDB doesn't act as a traditional database server here. Instead, this client spins up an in-memory DuckDB instance that reaches directly into the MinIO object storage to run complex SQL queries against my Gold-layer Parquet files.
* **Qdrant Client:** The semantic engine. This client handles interactions with the Qdrant vector database. It takes vectorized queries (e.g., "What are the latest AI hardware trends?"), converts them into embeddings using `sentence-transformers`, and performs cosine similarity searches to find relevant historical context.

## 🔄 Data Flow

When the API or an Agent asks for data:

`MCP Tool` ➔ `Storage Wrapper (DuckDB or Qdrant)` ➔ `Raw Storage (MinIO or Qdrant Container)` ➔ `Dataframes/JSON` ➔ `MCP Tool`

## 🔌 Dependencies & Extension Points

* **Dependencies:** `duckdb`, `qdrant-client`, `sentence-transformers`. It also relies on the MinIO credentials configured in `src/common/`.
* **Extension Points:** If I ever outgrow DuckDB and decide to use a dedicated analytical warehouse like ClickHouse, I only need to rewrite the interface in this folder. The agents and the API wouldn't even notice the change.

## 🐛 Debugging Tips

* **DuckDB Memory Leaks:** Because DuckDB runs in-process within the FastAPI app, complex queries can eat up RAM quickly. If the API container crashes with OOM, check the complexity of the DuckDB SQL queries in this folder.
* **Qdrant Empty Results:** If the semantic search returns nothing, verify two things: 
  1. Did the `sentence-transformer` model load correctly? (It usually takes a few seconds on startup).
  2. Does the Qdrant collection actually have data, or did the embedding pipeline fail during the Gold layer processing?
* **MinIO Connection Refused:** DuckDB needs to know *how* to talk to MinIO (S3 credentials). If DuckDB throws an IO error about an S3 endpoint, check that the AWS-compatible S3 variables are correctly passed into the DuckDB connection string here.
