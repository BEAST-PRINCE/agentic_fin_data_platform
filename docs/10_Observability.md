# 10 - Observability

When you build a system composed of scrapers, Kafka topics, Spark jobs, vector databases, and multi-agent AI, things will eventually break. And when they break, they break silently. 

A scraper might stop finding data. A Kafka topic might back up. An AI agent might start taking 45 seconds to answer a question instead of 10. 

I needed a way to see what my system was doing without constantly tailing terminal logs. I needed Observability.

## 👁️ The Stack: Prometheus & Grafana

I chose the industry-standard open-source observability stack. Both are orchestrated via `docker-compose.yml` in the `infra/` folder.

* **Prometheus:** The time-series database. It acts like a vacuum cleaner, constantly reaching out to all my services every 5 seconds and scraping their current metrics (e.g., CPU usage, number of API requests, Kafka queue size).
* **Grafana:** The visualization layer. It connects to Prometheus and turns those raw numbers into beautiful, readable dashboards.

## 📊 What I Monitor

I don't just monitor CPU and RAM. I built custom metrics into the FastAPI backend (`src/serving/`) and the Agent Orchestrator. 

Here is what I am watching on my Grafana dashboards:

### 1. Agent Latency (The Most Important Metric)
How long does a user wait for an answer? I track this at a granular level:
* Time spent by Planner.
* Time spent by Researcher waiting on DuckDB.
* Time spent by Synthesizer generating text.
If latency spikes, I can instantly see which agent is the bottleneck.

### 2. Lakehouse Pipeline Health
* **Kafka Lag:** How many messages have the scrapers pushed that Spark hasn't processed yet? If this number grows, the Bronze layer job has crashed.
* **Data Volume:** Total MBs of Parquet files in the Gold layer.

### 3. API Health
* **Error Rates:** Number of HTTP 500s or 422s.
* **Endpoint Traffic:** Which tools the agents are using the most.

## 📡 Health Endpoints

Every custom service I wrote (especially the FastAPI backend) has a `/metrics` endpoint specifically designed for Prometheus to scrape. I also added a `/health` endpoint that returns a simple `{"status": "ok"}` if the service can successfully ping DuckDB and Qdrant. 

## 🔮 Future Metrics

While the current setup gives me great operational visibility, my next goal is to add **AI Evaluation Metrics**. I want Grafana to track:
* How many times the Researcher agent failed to find data.
* How many times the LLM failed to output valid JSON.
* The average token count used per query to estimate the cost of the system.

---
⬅️ **Previous:** [09 - Dashboard](09_Dashboard.md) | **Next:** [11 - API Reference](11_API_Reference.md) ➡️
