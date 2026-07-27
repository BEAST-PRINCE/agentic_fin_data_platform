# 22 - Future Roadmap

The Agentic Datalake is fully functional, but it is far from finished. Here is the roadmap for where I intend to take this architecture next.

## 📈 Phase 1: Expanding the Data Universe
Currently, the agents rely heavily on unstructured financial news. To make the Analyst agent truly powerful, I need to feed it hard numbers.
* **SEC Filings Ingestion:** Build a new Python scraper pipeline specifically for pulling 10-K and 10-Q forms from the SEC EDGAR database.
* **Stock Price API Integration:** While I can scrape prices, integrating a reliable (and free/cheap) historical market data API into the Bronze layer will allow the agents to run complex quantitative correlations between news sentiment and price movement.

## 🤖 Phase 2: Agent Evolution
* **Parallel Task Execution:** Currently, the Researcher agent executes the Planner's task list sequentially. By implementing Python's `asyncio.gather`, the Researcher could hit DuckDB and Qdrant simultaneously, cutting latency in half.
* **Agent Memory:** The agents currently operate entirely within the context of a single query. Implementing a session-based memory store (likely using a dedicated Qdrant collection or Redis) would allow the agents to remember past conversations and build on previous analyses.

## ⚙️ Phase 3: Infrastructure Scaling
* **Airflow / Prefect Orchestration:** The PySpark jobs currently run via the FastAPI API integration. Introducing a proper DAG orchestrator like Apache Airflow will allow for robust, schedule-based dependency management and automatic retries.
* **Real-time Streaming:** The Lakehouse is currently updated in micro-batches. By leveraging Spark Structured Streaming directly against the Kafka topics, I could reduce the data latency from hours to seconds, allowing the agents to react to breaking news instantly.

## 📊 Phase 4: AI Observability
* **LLM Evaluation Metrics:** Grafana currently tracks system latency and data volume. The next step is to log the LLM token usage, cost-per-query, and "hallucination scores" (using an automated LLM-as-a-judge framework) to quantify the *quality* of the Multi-Agent pipeline over time.

## 🚀 Phase 5: The "Moonshot" Ambitions
Because we have to dream a little bit bigger:
* **Predictive Automated Execution:** Moving the agents from read-only "analysts" to active participants. If the Analyst agent detects a high-confidence sentiment shift that correlates with historical price drops, it could trigger a webhook to a paper-trading API, essentially turning the Datalake into an autonomous hedge fund.
* **Personalized Agent Personas:** Integrating a user-profile database so the agents dynamically alter their risk tolerance and analysis style based on who is logged in (e.g., explaining things to a conservative retiree vs. a high-frequency day trader).
* **Cross-Lakehouse Federation:** Why stop at one lakehouse? Scaling the MCP tools to allow the agents to query external, third-party data lakes directly (like Snowflake or Databricks delta-sharing) to supplement the local MinIO data on the fly.
* **Voice-Native Financial Interface:** Replacing the React chat box with a real-time WebRTC audio interface, allowing you to literally have a voice conversation with the Analyst agent while you drink your morning coffee.

---
⬅️ **Previous:** [21 - Deployment Guide](21_Deployment_Guide.md) | **Next:** [Security](Security.md) ➡️
