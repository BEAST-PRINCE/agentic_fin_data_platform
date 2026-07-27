# 13 - Technology Stack

I am very deliberate about the technologies I choose. I try to avoid "hype-driven development," but I also don't want to use legacy tools when better alternatives exist. 

Here is the honest breakdown of every major piece of technology in the Agentic Datalake, and exactly why I chose it.

## 🧠 The AI Layer
* **Model Context Protocol (MCP):** The open standard for connecting AI models to data sources. I used this instead of custom LangChain tool wrappers because it is universally supported and keeps my API logic completely separated from my LLM logic.
* **Sentence Transformers (MiniLM) & KeyBERT:** Used for generating vector embeddings and extracting semantic keywords. I chose these because they are small, incredibly fast, and run perfectly on local CPU/GPU without needing an external API key.

## 🗄️ The Data Engineering Layer
* **Apache Spark (PySpark):** The industry standard for big data processing. I use it to power the Medallion Architecture (Bronze -> Silver -> Gold). I chose it over Pandas because it natively handles distributed Parquet files and partitioning, which is critical for scaling.
* **Apache Kafka:** The ingestion buffer. Scrapers push to Kafka; Spark reads from Kafka. This decouples my brittle web scrapers from my heavy database writes.
* **MinIO:** The object storage engine. It acts identically to AWS S3. I chose this because it allows me to build a true Lakehouse architecture locally. 

## 🦆 The Retrieval Layer
* **DuckDB:** The analytical engine. Instead of spinning up a heavy PostgreSQL container, DuckDB runs in-process within my FastAPI backend. It queries the Gold Parquet files in MinIO directly using vectorized execution. It is ridiculously fast for aggregations.
* **Qdrant:** The vector database. Written in Rust. I chose it over Milvus or Pinecone because it has a fantastic local Docker container and excellent support for JSON Payload Filtering, which is essential for accurate agent retrieval.

## 🌐 The Application Layer
* **FastAPI:** The backend framework. Chosen for its automatic Pydantic validation (which is a lifesaver when dealing with unpredictable LLM JSON outputs) and native async support.
* **React & Vite:** The frontend dashboard. I used Vite for sub-second hot module reloading during development. 

## 👁️ The Observability Layer
* **Prometheus & Grafana:** The classic observability stack. I use it to track agent latency, DuckDB query times, and Kafka lag. I chose it because it is open-source, runs locally, and integrates easily with FastAPI via the `prometheus-fastapi-instrumentator` package.

---
⬅️ **Previous:** [12 - Data Model](12_Data_Model.md) | **Next:** [14 - Project Decisions](14_Project_Decisions.md) ➡️
