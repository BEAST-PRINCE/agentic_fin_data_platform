# 21 - Deployment Guide

The Agentic Datalake is designed as a "Local-First" architecture. 

The primary deployment mechanism is Docker Compose. By running a single command, you bring up the entire data engineering and observability infrastructure. 

Here is exactly what happens when you deploy, and how you interact with the system.

## 🐳 The Docker Compose Stack

The `infra/docker-compose.yml` file is the heart of the deployment. When you run `docker-compose up -d`, it provisions the following isolated network of containers:

### Storage & Ingestion
* **MinIO (Lakehouse):** 
  * API Port: `9000` (Used by Spark and DuckDB to read/write files).
  * Web Console: `9001` (Open this in your browser to visually inspect your Bronze/Silver/Gold buckets).
* **Zookeeper:** 
  * Port: `2181` (Required for Kafka orchestration).
* **Kafka:** 
  * Broker Port: `9092` (Where your scrapers send their data).
* **Qdrant (Vector DB):** 
  * API Port: `6333`
  * Web Dashboard: `http://localhost:6333/dashboard`

### Observability
* **Prometheus:** 
  * Port: `9090` (Scrapes metrics from the API and infrastructure).
* **Grafana:** 
  * Port: `3000` (The visual dashboard for system health. Default login: `admin`/`admin`).

## 🚀 Running the Application Layers

While the databases run in Docker, the application code is typically run directly on your host machine during development for easier debugging.

### 1. Start the FastAPI Backend
This serves the API endpoints and orchestrates the AI Agents.
```bash
cd src/serving/api
uvicorn main:app --reload --port 8000
```
* Swagger Docs: `http://localhost:8000/docs`

### 2. Start the React Dashboard
The frontend user interface is your absolute command center.
```bash
cd dashboard
npm install
npm run dev
```
* Dashboard URL: `http://localhost:5173`

### 3. Use the Dashboard for Everything!
Once the UI is running on port 5173, **you do not need to manually run scripts in the terminal.** 
The React Dashboard has full control over the infrastructure. 

From the Dashboard, you can:
1. Navigate to the **Data Pipeline** tab.
2. Start or stop any specific web scraper with a click.
3. Trigger the PySpark Medallion jobs (Bronze to Silver to Gold) directly from the UI.
4. Watch the pipeline logs stream live directly into your browser.

The entire system is designed to be operated visually from that single pane of glass.

## ☁️ Migrating to the Cloud (Productionizing)

If you outgrow your local machine, the migration path is straightforward because of the architecture:

1. **MinIO ➔ AWS S3:** Because MinIO uses the S3 API, you simply change the `.env` endpoint from `localhost:9000` to `s3.amazonaws.com` and provide real AWS IAM credentials. DuckDB and Spark won't know the difference.
2. **Local Qdrant ➔ Qdrant Cloud:** Update the `QDRANT_URL` to point to a managed cluster.
3. **Local Spark ➔ AWS EMR / Databricks:** Package the `src/processing/` scripts and submit them to a managed cluster for horizontal scaling.
4. **FastAPI & React:** Containerize them using their respective Dockerfiles and deploy via AWS ECS or Kubernetes.

---
⬅️ **Previous:** [20 - FAQ](20_FAQ.md) | **Next:** [22 - Future Roadmap](22_Future_Roadmap.md) ➡️
