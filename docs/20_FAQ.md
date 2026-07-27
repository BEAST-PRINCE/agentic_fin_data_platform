# 20 - FAQ

> *Disclaimer: If you have a highly specific question that isn't answered here, you should probably just ask your AI Coding Agent to analyze the project and get the answer for you. That's literally what it is there for!* 😉

Here are answers to some of the most common questions about the architecture and decisions made in the Agentic Datalake.

### Why not just use PostgreSQL for everything?
PostgreSQL is incredible, but it is an OLTP (Online Transaction Processing) database. It is designed for fast, single-row lookups (e.g., "Get user profile #1234"). The Datalake requires OLAP (Online Analytical Processing) capabilities to aggregate millions of rows of text and market data instantly. DuckDB querying columnar Parquet files is orders of magnitude faster for this specific use case than Postgres.

### Why use 5 separate Agents instead of just one smart Agent?
LLMs suffer from "attention fatigue" when context windows get too large, and they struggle to follow complex, multi-step instructions without deviating. By splitting the work into a Planner, Researcher, Summarizer, Analyst, and Synthesizer, I force the LLM to focus on one tiny, highly constrained task at a time. It dramatically reduces hallucinations and format errors.

### Do I need a massive GPU to run this?
No! That is the beauty of this architecture. 
1. **The Infrastructure** (MinIO, Kafka, Qdrant, DuckDB, Spark) runs entirely on CPU and is relatively lightweight.
2. **The Embeddings** (KeyBERT/MiniLM) are very small models that can run on a standard CPU, though a basic laptop GPU will speed up the Gold layer processing.
3. **The LLM** can be offloaded to an external provider (like Anthropic or OpenAI) via API keys in the `.env` file, meaning your local machine doesn't have to do the heavy lifting of text generation.

### Why do you use JSON for agent-to-agent communication?
If the Researcher Agent passes its findings to the Analyst Agent as conversational Markdown (e.g., "Here is what I found..."), the Analyst has to waste tokens figuring out where the data actually is. By enforcing strict JSON structures, the orchestrator guarantees that the next agent in the pipeline receives clean, parsable data.

### Can I add my own data sources?
Yes! The ingestion pipeline is completely decoupled. If you want to add Reddit scraping or SEC filings, simply write a Python script that pushes a JSON payload to the Kafka topic. The Bronze and Silver Spark jobs will pick it up automatically.

---
⬅️ **Previous:** [19 - Glossary](19_Glossary.md) | **Next:** [21 - Deployment Guide](21_Deployment_Guide.md) ➡️
