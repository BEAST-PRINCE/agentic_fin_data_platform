# 10 - Observability

When you build a system composed of scrapers, Kafka topics, Spark jobs, vector databases, and multi-agent AI, things will eventually break. And when they break, they break silently. 

A scraper might stop finding data. A Kafka topic might back up. An AI agent might start taking 45 seconds to answer a question instead of 10. 

I needed a way to see what my system was doing without constantly tailing terminal logs. I needed Observability.

## 👁️ The Stack: Prometheus & Grafana

I chose the industry-standard open-source observability stack. Both are orchestrated via `docker-compose.yml` in the `infra/` folder.

* **Prometheus:** The time-series database. It scrapes the configured FastAPI metrics endpoint. The repository does not currently export custom CPU, RAM, or Kafka-lag metrics.
* **Grafana:** The visualization layer. It connects to Prometheus and turns those raw numbers into beautiful, readable dashboards.

## 📊 What I Monitor

I don't just rely on logs. I built custom application metrics into the FastAPI backend and retrieval code.

The code currently exposes these application metrics:

### 1. Agent Latency (The Most Important Metric)
How long does a user wait for an answer? I track this at a granular level:
* Request counts and latency histograms for solo and multi-agent API requests.
* Vector-search request count and latency.
* Bronze, Silver, Gold, and Qdrant record gauges when retrieval code updates them.

### 2. Lakehouse Pipeline Health
* **Lakehouse counts:** Maintained Bronze, Silver, and Gold record counters, plus Qdrant vector count when available.

### 3. API Health
* **Error Rates:** Number of HTTP 500s or 422s.
* **Endpoint Traffic:** Which tools the agents are using the most.

## 📡 Health Endpoints

The FastAPI backend exposes `/metrics` through `prometheus-fastapi-instrumentator`. `/health` is a lightweight API liveness response; `/api/health` performs dependency checks for MinIO, Kafka, Qdrant, DuckDB, and Ollama according to configuration.

## 🔮 Future Metrics

While the current setup gives me great operational visibility, my next goal is to add **AI Evaluation Metrics**. I want Grafana to track:
* How many times the Researcher agent failed to find data.
* How many times the LLM failed to output valid JSON.
* The average token count used per query to estimate the cost of the system.

---
⬅️ **Previous:** [09 - Dashboard](09_Dashboard.md) | **Next:** [11 - API Reference](11_API_Reference.md) ➡️
