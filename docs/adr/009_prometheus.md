# ADR 009: Using Prometheus and Grafana for Observability

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
An Agentic Datalake has too many moving parts to rely on simple terminal `print()` statements. 
When the dashboard hangs for 15 seconds, I need to know instantly:
1. Is DuckDB struggling with a massive query?
2. Is Qdrant taking too long to run the vector search?
3. Is the LLM provider experiencing high latency?
4. Is Kafka backed up with scraped articles?

I needed a robust, visual observability stack to monitor the health and performance of the infrastructure and the AI agents.

## 🤔 Considered Options
1. **Datadog / New Relic:** Industry standard, gorgeous dashboards, but very expensive and requires sending local telemetry data to the cloud.
2. **Logstash / Kibana (ELK):** Great for text logs, but heavy on RAM and less optimized for raw time-series metrics.
3. **Prometheus & Grafana:** The open-source standard for time-series monitoring. Lightweight, runs perfectly in Docker, and has native integration with FastAPI.

## ✅ Decision
I deployed **Prometheus** (for metric scraping and storage) and **Grafana** (for visualization) via the `docker-compose.yml` stack.

To expose metrics from the FastAPI backend, I utilized the `prometheus-fastapi-instrumentator` package. This automatically tracks HTTP request latency, error rates, and throughput. 

Furthermore, I instrumented custom metrics in the Multi-Agent orchestrator (`src/serving/core/metrics.py`) to explicitly track the execution time of individual agents (Planner vs. Researcher vs. Analyst) and tool calls.

## 📈 Consequences
* **Positive:** Local visibility into API, agent, vector-search, and maintained lakehouse metrics through Grafana on `localhost:3000`. The repository does not currently provide a benchmark-backed 3-minute/50-millisecond comparison.
* **Positive:** Local-first compliance. Telemetry data stays on the local machine.
* **Negative:** Writing custom Prometheus PromQL queries to build Grafana dashboards requires a steep learning curve compared to managed services that auto-generate dashboards.

---
⬅️ **Previous:** [ADR 008: Local First Architecture](008_local_first_architecture.md) | **Next:** [ADR 010: Multi-Agent System](010_multi_agent.md) ➡️

### 📚 Further Reading
* [10 - Observability](../10_Observability.md)
