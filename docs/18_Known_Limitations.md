# 18 - Known Limitations

This project is powerful, but it is not magic. I built this under specific constraints (primarily: running locally on consumer hardware without enterprise budgets). 

It is important to be honest about what this system *cannot* do.

## 1. Scraper Brittleness
The pipeline starts with Scrapy spiders under `src/ingestion/scrapers/scrapy_project/`.
* **Limitation:** If a target financial news website changes its HTML structure, CSS classes, or implements aggressive anti-bot protection (like Cloudflare Turnstile), the scraper will silently fail and return empty data to Kafka.
* **Reality:** Maintaining web scrapers is a full-time job. In a true enterprise environment, this ingestion layer would be replaced by a paid, structured API feed (like Bloomberg or Reuters).

## 2. LLM Context Windows & Long Documents
The Multi-Agent system works by passing JSON packages of evidence from the Researcher to the Summarizer to the Analyst.
* **Limitation:** If the Researcher pulls 50 massive articles from Qdrant, the resulting JSON Evidence Package might easily exceed the token context limit of the LLM. 
* **Reality:** Furthermore, the current semantic search approach struggles with extremely long, dense documents (like 150-page 10-K SEC filings). KeyBERT extracts keywords fine, but the agents cannot read a full 10-K in one pass without sophisticated RAG chunking techniques that are currently outside the scope of this project.

## 3. Not Horizontally Scalable (Yet)
* **Limitation:** The Spark jobs (`silver_layer.py`, `gold_layer.py`) are currently configured with `.master("local[1]")`. They run on one local Spark worker and do not distribute across a cluster of separate worker nodes.
* **Reality:** If the data volume grows from gigabytes to terabytes, the local Spark setup will eventually hit a wall. Migrating to an AWS EMR or Databricks cluster would be required.

## 4. Analytical Latency
* **Limitation:** While DuckDB is incredibly fast, LLMs are slow. When a user asks a complex question on the dashboard, the Multi-Agent pipeline has to make multiple sequential network calls to the LLM provider. This means an answer can take 15-30 seconds to generate.
* **Reality:** This system is designed for deep research, not real-time instant chat. The interactive Workflow Accordion on the dashboard helps manage user expectations by showing progress, but it cannot speed up the actual token generation. 

## 5. Lack of Real-Time Streaming Analytics
* **Limitation:** The data pipeline operates on micro-batches. You have to trigger the `silver` and `gold` pipelines to process the Kafka backlog.
* **Reality:** If an event happens *right now*, the AI agent will not know about it until the pipeline finishes running. True real-time streaming (using Spark Structured Streaming writing to Delta tables) is not yet implemented.

## 6. Zero User Personalization
* **Limitation:** The agents do not know who you are. There are no user profiles, risk tolerances, or personalized portfolios. 
* **Reality:** If a conservative retiree and a day-trader ask the system "What should I do about Nvidia?", they will get the exact same heavily-analytical response. 

## 7. Security
* **Limitation:** There is zero authentication or authorization on the FastAPI backend or the React dashboard. Anyone who can reach the port can trigger Spark jobs or query the database.
* **Reality:** See [Security.md](Security.md) for details. Do not deploy this to the public internet as-is.

---
⬅️ **Previous:** [17 - Troubleshooting](17_Troubleshooting.md) | **Next:** [19 - Glossary](19_Glossary.md) ➡️
