# 03 - System Architecture

To understand the Agentic Datalake, you have to look at it from two different angles. 

On the left side, we have the **Data Engineering Pipeline**—a rigorous, structured flow of information from the wild internet into a highly optimized storage format. On the right side, we have the **AI Application**—a dynamic, multi-agent system that queries that optimized storage to answer complex questions.

Here is the 10,000-foot view of how everything connects.

## 🗺️ The Big Picture

```mermaid
flowchart TD
    subgraph Data Gathering
        S[Web Scrapers]
        API[External APIs]
    end

    subgraph Streaming
        K[Apache Kafka]
    end

    subgraph The Lakehouse (MinIO & Spark)
        B[(Bronze Layer\nRaw JSON)]
        Si[(Silver Layer\nCleaned Parquet)]
        G[(Gold Layer\nAggregated Parquet)]
    end

    subgraph Storage & Retrieval
        D[(DuckDB\nAnalytical Engine)]
        Q[(Qdrant\nVector Database)]
    end

    subgraph The AI Brain
        F[FastAPI & MCP Tools]
        M[Multi-Agent System\nPlanner, Researcher, etc.]
    end

    subgraph User Experience
        UI[React Dashboard]
    end

    %% Connections
    S --> K
    API --> K
    
    K -->|PySpark| B
    B -->|PySpark| Si
    Si -->|PySpark| G
    
    G -.->|SQL| D
    G -->|KeyBERT Embeddings| Q
    
    D <-->|MCP| F
    Q <-->|MCP| F
    
    F <--> M
    UI <-->|HTTP/REST| F

    %% Styling
    classDef storage fill:#f9f,stroke:#333,stroke-width:2px;
    classDef processing fill:#bbf,stroke:#333,stroke-width:2px;
    classDef ai fill:#bfb,stroke:#333,stroke-width:2px;
    
    class B,Si,G,D,Q storage;
    class K processing;
    class M,F ai;
```

## 🧩 Component Breakdown

Let's walk through the major architectural blocks.

### 1. Data Gathering & Streaming
* **Scrapers:** Python scripts running on a schedule to fetch financial news, stock prices, and market sentiment.
* **Apache Kafka:** I use Kafka as a buffer. Scrapers don't write directly to the database. They dump payloads onto a Kafka topic. This decouples the fast scraping process from the slower, heavier data processing jobs. If the database goes down, Kafka holds the messages safely until it comes back up.

### 2. The Medallion Lakehouse
I use **MinIO** (an S3-compatible object store) to hold the actual files, and **Apache Spark** to process them.
* **Bronze:** Raw data lands here exactly as the scraper found it. If a scraper breaks formatting, we don't lose the data; it just sits in Bronze until we fix the parser.
* **Silver:** Spark cleans the data, enforces strict schemas, drops duplicates, and writes it back to MinIO in Parquet format.
* **Gold:** The data is aggregated and optimized for read performance. 

### 3. The Retrieval Engines
Once data is in the Gold layer, it splits into two paths so our AI agents can query it effectively.
* **DuckDB:** The analytical powerhouse. It allows our API to run blazing-fast SQL queries directly against the Gold Parquet files in MinIO without needing to load them into a traditional database server like PostgreSQL.
* **Qdrant:** The semantic engine. Text data (like news articles) is run through an embedding model (Sentence Transformers/KeyBERT) and stored here. This allows agents to search by *concept* rather than just keyword.

### 4. The AI Application
* **FastAPI:** Exposes the API for the dashboard, but more importantly, it defines the **Model Context Protocol (MCP)** tools. These tools are Python functions that know how to query DuckDB and Qdrant.
* **Multi-Agent System:** A team of LLM-powered agents. The Planner decides what needs to be done, the Researcher uses the MCP tools to fetch data from DuckDB/Qdrant, and the Analyst/Summarizer package the final answer.

### 5. The Dashboard
* **React UI:** The front door for the user. It streams the agent's thought process in real-time, displaying both the final markdown report and the interactive steps the agents took to get there.

---
⬅️ **Previous:** [02 - Repository Tour](02_Repository_Tour.md) | **Next:** [04 - Data Pipeline](04_Data_Pipeline.md) ➡️
