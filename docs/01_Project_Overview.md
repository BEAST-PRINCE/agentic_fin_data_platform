# 01 - Project Overview

## 💡 The "Why"

Data engineering and Generative AI usually exist in two entirely different universes. 

Data engineers spend their time wrestling with Spark, partitions, Parquet files, and Airflow DAGs. AI engineers spend their time messing with prompts, LangChain, vector databases, and RAG pipelines. 

I built the **Agentic Datalake** because I wanted to see what happens when you smash these two universes together.

I wanted to know: *Can an autonomous AI agent understand and query a raw, partitioned data lakehouse?*

Usually, if you want an LLM to answer questions about your data, you have to build a highly curated, polished dashboard, or write a very specific SQL wrapper. I wanted something more dynamic. I wanted a system where I could scrape raw financial news, dump it into a Lakehouse, and have a team of AI agents figure out how to parse, analyze, and summarize it on the fly.

## 🎯 The Problem This Solves

If you are a financial analyst, a researcher, or just someone interested in the market, information overload is your biggest enemy. 

1. **Volume:** There are thousands of news articles, SEC filings, and price movements every single day.
2. **Context:** A raw piece of news means nothing without historical context.
3. **Tooling:** You usually have to search a news aggregator, then open a database, then open Excel to do math.

This project solves this by creating a **single interface** where you can ask high-level questions. The system orchestrates the data retrieval, the math, and the summarization for you.

## 🌊 The High-Level Workflow

At 10,000 feet, the project has two operational phases: **The Data Pipeline** and **The Active Query**. The pipeline is started manually or from the dashboard; it is not a built-in scheduler.

### Phase 1: The Background Sweep (Data Engineering)
When the ingestion and processing jobs are running:
1. **Scrapers** fetch financial news from configured sites.
2. They push raw text into **Kafka** topics.
3. The Python Bronze consumer reads Kafka and dumps raw JSON objects into the **Bronze** layer of MinIO.
4. Another Spark job cleans it, deduplicates it, and moves it to **Silver**.
5. Finally, the **Gold** job creates serving and aggregate Parquet tables and extracts KeyBERT keywords. The separate vector indexer generates embeddings and pushes them into **Qdrant**.

### Phase 2: The Active Query (Multi-Agent AI)
When you wake up and type a question into the dashboard:
1. The **Planner** receives the question and creates a JSON execution plan.
2. The **Researcher** uses MCP tools to search Qdrant and DuckDB to gather raw data evidence.
3. The **Summarizer** compresses that raw data into themes and clusters.
4. The **Analyst** takes the summary and reasons about risks and insights.
5. The **Synthesizer** drafts the final human-readable report.

It is a data pipeline that feeds an AI pipeline.

---
⬅️ **Previous:** [00 - Installation Guide](00_Installation_Guide.md) | **Next:** [02 - Repository Tour](02_Repository_Tour.md) ➡️
