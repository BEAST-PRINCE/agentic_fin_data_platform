# 11 - API Reference

I built the backend using **FastAPI** because it offers automatic Pydantic validation and interactive Swagger documentation right out of the box. 

While the AI agents interact with the backend via MCP tools, the React dashboard needs traditional REST endpoints to render the UI. Here are the primary endpoints I exposed for the frontend based directly on `src/serving/api/main.py`.

## 🤖 Agent Endpoints

### `POST /api/chat` (Solo Agent)
Interacts with the single-agent intelligence.
**Request Body:** `{"message": "string"}`
**Response:** `{"reply": "string", "agent": "solo", "execution_time_ms": int}`

### `POST /api/chat/multi` (Multi-Agent Pipeline)
Interacts with the multi-agent pipeline (Planner, Researcher, Analyst, etc).
**Request Body:** `{"message": "string"}`
**Response (JSON):**
Returns the final answer and the workflow steps taken.
```json
{
  "reply": "# Market Analysis...",
  "workflow_steps": [
    {"agent": "Planner", "action": "Created plan", "details": "..."}
  ],
  "agent": "multi"
}
```

## 📊 Data Retrieval Endpoints

### `GET /articles`
Retrieve a list of recently published articles.
**Query Params:** `limit` (int, default 10), `offset` (int, default 0)

### `GET /articles/{article_id}`
Retrieve a single article by its unique ID.

### `GET /search`
Perform semantic search over the articles using Qdrant Vector DB.
**Query Params:** `query` (str), `limit` (int)

### `GET /trending`
Retrieve aggregate daily trends across sources and categories.
**Query Params:** `start_date` (str), `end_date` (str)

### `GET /entities`
Retrieve top entity mentions (keywords) for a specific date.
**Query Params:** `publish_date` (str), `limit` (int)

### `GET /api/trends/dates`
Get all available dates with trending data.

## ⚙️ System & Pipeline Endpoints

### `GET /api/system/statistics`
Retrieve datalake statistics for the dashboard (runs synchronous DuckDB in a background threadpool).

### `GET /api/domain-throughput`
Retrieve real-time domain throughput stats.

### `GET /api/health`
Perform health checks on all dependent infrastructure components.

### `GET /api/pipeline/status`
Get the active status of the data pipeline.

### `POST /api/pipeline/run/{stage}`
Run a specific pipeline stage (e.g., `silver`, `gold`, `indexer`).

### `POST /api/pipeline/stop`
Stop the currently running pipeline stage.

### `GET /api/pipeline/logs`
Get the live logs of the running pipeline stage (Query param `stage`).

## 🕷️ Scraper Endpoints

* `GET /api/scrapers` - List all available scrapers and status.
* `POST /api/scrapers/{name}/start` - Start a scrapy spider.
* `POST /api/scrapers/{name}/stop` - Stop a running scrapy spider.
* `GET /api/scrapers/{name}/logs` - Get real-time tail of scraper logs.

---
⬅️ **Previous:** [10 - Observability](10_Observability.md) | **Next:** [12 - Data Model](12_Data_Model.md) ➡️
