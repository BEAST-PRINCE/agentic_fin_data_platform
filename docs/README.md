# Documentation Index

Welcome to the official documentation for the **Agentic Datalake**. 

I built this project to bridge the gap between heavy-duty Data Engineering (Lakehouses, Spark, Kafka) and modern AI systems (Multi-Agent reasoning, Model Context Protocol, Vector Search). 

This documentation is designed to be read sequentially like a book. If you want to understand how it all fits together, start at the top and work your way down.

## 🏁 Getting Started
* [00 - Installation Guide](00_Installation_Guide.md) - How to get this entire beast running locally on your machine.
* [01 - Project Overview](01_Project_Overview.md) - Why I built this, the problem it solves, and the high-level workflow.
* [02 - Repository Tour](02_Repository_Tour.md) - A guided tour of the codebase.

## 🏗️ Architecture & Data
* [03 - System Architecture](03_System_Architecture.md) - The big picture diagram and how the pieces connect.
* [04 - Data Pipeline](04_Data_Pipeline.md) - How data flows through the Bronze, Silver, and Gold layers.
* [05 - Lakehouse](05_Lakehouse.md) - MinIO, DuckDB, Parquet files, and why I chose this over PostgreSQL.
* [12 - Data Model](12_Data_Model.md) - How the schema evolves from raw JSON to Qdrant embeddings.

## 🤖 AI & Search
* [06 - Semantic Search](06_Semantic_Search.md) - How I use KeyBERT and Qdrant to understand the meaning behind the data.
* [07 - MCP and Tools](07_MCP_and_Tools.md) - A directory of every tool the agents have access to via the Model Context Protocol.
* [08 - Multi-Agent System](08_Multi_Agent_System.md) - How the Planner, Researcher, and Analyst agents coordinate.

## 🖥️ UI & Operations
* [09 - Dashboard](09_Dashboard.md) - The React frontend and the Agent Workflow interactive UI.
* [10 - Observability](10_Observability.md) - How I use Prometheus and Grafana to spy on my own code.
* [11 - API Reference](11_API_Reference.md) - FastAPI endpoints and examples.
* [21 - Deployment Guide](21_Deployment_Guide.md) - Going beyond `localhost` (ports, proxies, Docker Compose).

## 🧠 Decisions, Lessons & Future
* [13 - Technology Stack](13_Technology_Stack.md) - An honest look at every technology I chose and why.
* [14 - Project Decisions](14_Project_Decisions.md) - The major architectural forks in the road.
* [15 - Developer Journey](15_Developer_Journey.md) - My raw, chronological engineering journal.
* [16 - Performance and Scaling](16_Performance_and_Scaling.md) - Speed, bottlenecks, and the dangers of tiny Parquet files.
* [17 - Troubleshooting](17_Troubleshooting.md) - Every(Okay maybe not every 🙃)  error I've encountered and how to fix it.
* [18 - Known Limitations](18_Known_Limitations.md) - What this project *can't* do.
* [19 - Glossary](19_Glossary.md) - Definitions of all the jargon used in this project.
* [20 - FAQ](20_FAQ.md) - Answers to questions you probably have.
* [22 - Future Roadmap](22_Future_Roadmap.md) - Where this project is heading next.
* [Security](Security.md) - Why you shouldn't put this on the public internet as-is.

---
**Next:** [00 - Installation Guide](00_Installation_Guide.md) ➡️
