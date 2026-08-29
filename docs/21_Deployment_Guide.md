# 21 - Deployment Guide

The Agentic Datalake is designed as a "Local-First" architecture. 

The primary deployment mechanism is Docker Compose. By running a single command, you bring up the entire data engineering and observability infrastructure. 

Here is exactly what happens when you deploy, and how you interact with the system.

## 🐳 The Docker Compose Stack

The root `docker-compose.yml` file is the heart of the deployment. When you run `docker compose up -d`, it provisions the following services:

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
   * Port: `9090` (Stores metrics scraped from the configured API target).
* **Grafana:** 
  * Port: `3000` (The visual dashboard for system health. Default login: `admin`/`admin`).

## 🚀 Running the Application Layers

You can orchestrate the full platform using our automation scripts or run individual application layers manually.

### Option A: Automated One-Command Startup (Recommended)

Run the startup script from the root of the repository:

* **Windows:** `.\scripts\start.ps1` (or `.\scripts\start.ps1 -NoBrowser` to skip opening browser)
* **Linux / macOS:** `./scripts/start.sh` (or `./scripts/start.sh --no-browser` to skip opening browser)

This script handles starting Docker Compose, verifying health checks, starting FastAPI and React in the background, logging to `logs/`, and opening `http://localhost:5173`.

---

### Option B: Manual Layer Startup (Legacy / Debugging Mode)

If you are actively developing and debugging application code, you can start each layer manually:

#### 1. Start Docker Infrastructure
```bash
docker compose up -d
```

#### 2. Start the FastAPI Backend
Serves API endpoints and orchestrates AI Agents.
```bash
uvicorn src.serving.api.main:app --reload --port 8000
```
* Swagger Docs: `http://localhost:8000/docs`

#### 3. Start the React Dashboard
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
3. Trigger the Spark Silver, Gold, and vector-indexing jobs directly from the UI.
4. Poll the latest pipeline and scraper log buffers from the UI.

The entire system is designed to be operated visually from that single pane of glass.

## ☁️ Migrating to the Cloud (Productionizing)

If you outgrow your local machine, the migration path is straightforward because of the architecture:

1. **MinIO ➔ AWS S3:** Because MinIO uses the S3 API, storage can be adapted for AWS, but endpoint, credentials, TLS, bucket, and Spark/DuckDB settings must be reviewed together.
2. **Local Qdrant ➔ Qdrant Cloud:** Update the Qdrant client configuration and add authentication; the current URL is hardcoded in retrieval/indexing code and should be centralized first.
3. **Local Spark ➔ AWS EMR / Databricks:** Package the `src/processing/` scripts and submit them to a managed cluster for horizontal scaling.
4. **FastAPI & React:** Containerize them using their respective Dockerfiles and deploy via AWS ECS or Kubernetes.

---
⬅️ **Previous:** [20 - FAQ](20_FAQ.md) | **Next:** [22 - Future Roadmap](22_Future_Roadmap.md) ➡️
