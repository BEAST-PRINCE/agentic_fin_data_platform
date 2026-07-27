# 14 - Project Decisions (ADR Summary)

Throughout the development of the Agentic Datalake, I had to make several architectural forks in the road. 

I document these as Architecture Decision Records (ADRs). You can find the full, detailed ADRs in the `docs/adr/` directory, but here is a summary of the most critical decisions that shaped this repository.

## 1. Local-First Architecture
**The Decision:** I chose to build this entire project to run locally using Docker Compose, rather than deploying it to AWS or GCP immediately.
**The Why:** Cloud costs can spiral out of control when experimenting with big data and AI. By using MinIO (S3 compatible) and local LLMs (or local API proxies), I can process millions of rows and run hundreds of agent queries for exactly $0.00. The code is written in a way (`s3a://` paths, modular endpoints) that allows a seamless migration to the cloud later if needed.

## 2. DuckDB over PostgreSQL
**The Decision:** I chose an in-process OLAP engine (DuckDB) over a traditional client-server OLTP database (PostgreSQL).
**The Why:** My AI agents don't need to look up a single user profile; they need to run massive aggregations ("What is the total trend of tech articles this week?"). DuckDB queries Parquet files directly. It skips the ETL step of loading data *into* a database server, saving massive amounts of compute and time.

## 3. Strict JSON Handoffs in the Multi-Agent Pipeline
**The Decision:** I forced all intermediate agents (Planner, Researcher, Summarizer, Analyst) to communicate exclusively via structured JSON, forbidding Markdown or conversational text until the final step.
**The Why:** LLMs suffer from "format drift." If Agent A writes a conversational summary, Agent B might get confused parsing it. By enforcing strict JSON schemas via Pydantic/instructions, the orchestrator can validate the data programmatically before passing it to the next agent, preventing catastrophic pipeline failures.

## 4. MCP Over Custom Tool Calling
**The Decision:** I used the Model Context Protocol (MCP) to define tools for the Researcher agent, rather than writing custom LangChain tool wrappers.
**The Why:** MCP standardizes how AI connects to data. By defining my DuckDB and Qdrant queries as MCP tools, I decouple the prompt engineering from the database logic. The FastAPI backend simply exposes a standardized tool interface, and the Agent Orchestrator consumes it.

## 5. Background Sweep vs. Active Query
**The Decision:** I completely separated the data ingestion/processing pipeline (Kafka + Spark) from the retrieval pipeline (FastAPI + Agents).
**The Why:** If the scraper breaks, the dashboard should still work. If the LLM goes down, the scrapers should keep building historical data. This absolute decoupling ensures system resilience.

---
⬅️ **Previous:** [13 - Technology Stack](13_Technology_Stack.md) | **Next:** [15 - Developer Journey](15_Developer_Journey.md) ➡️
