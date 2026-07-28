# Agentic Datalake 🌊🤖

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![DuckDB](https://img.shields.io/badge/DuckDB-Fast-yellow.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

> **"What if your data lake could talk back, understand context, and do its own research?"**

Welcome to the **Agentic Datalake**—a fully local, multi-agent financial intelligence platform. It's not just a place where data goes to sleep in Parquet files; it's a living ecosystem where data is ingested, refined, embedded, and actively analyzed by a team of AI agents.

Think of it as a data engineering project that accidentally became sentient.

## 🌟 Why Does This Exist?

Most data platforms are passive. You query them, they give you rows. 
I wanted a system that could proactively synthesize information. I built a complete **Lakehouse Architecture** (Bronze, Silver, Gold layers) and then strapped a **Multi-Agent AI** system on top of it using the Model Context Protocol (MCP).

If you want to understand how to bridge the gap between heavy-duty Data Engineering (Spark, Kafka, Lakehouse) and modern Generative AI (Multi-Agent, Semantic Search), you're in the right place.

## ✨ Feature Highlights

* **Lakehouse Architecture:** A robust Bronze ➔ Silver ➔ Gold pipeline built on top of MinIO and queried blazingly fast by DuckDB.
* **Semantic Search:** I don't just use `LIKE '%keyword%'`. I use KeyBERT and MiniLM to extract semantic meaning, embedding everything into Qdrant for lightning-fast similarity search.
* **Multi-Agent AI:** A team of specialized agents (Planner, Researcher, Summarizer, Analyst) that work together to answer complex financial queries.
* **MCP Tooling:** The agents don't hallucinate; they use standard MCP tools to query the Lakehouse directly.
* **Full Observability:** Prometheus and Grafana keep a watchful eye on my agents and data pipelines, making sure nobody is slacking off.
* **100% Local:** No cloud credits required. I run everything locally because I like my data close and my AWS bills non-existent.

## 🏗️ Architecture at a Glance

*(For a deep dive, see our [System Architecture](docs/03_System_Architecture.md) document)*

![System Architecture Placeholder](docs/assets/diagrams/architecture.png)

*Our scrapers whisper into Kafka, the Lakehouse refines the gossip, and DuckDB serves it up on a silver platter to our AI Agents.*

## 🛠️ Technology Stack

* **Storage & Processing:** MinIO, DuckDB, Apache Spark, Kafka
* **AI & Search:** Qdrant, KeyBERT, Sentence Transformers
* **Backend:** FastAPI, MCP (Model Context Protocol)
* **Frontend:** React (Dynamic Dashboard)
* **Observability:** Prometheus, Grafana
* **Infrastructure:** Docker Compose

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/agentic_datalake.git
cd agentic_datalake
```

### 2. Set up Python Environment
Create a virtual environment and install the required dependencies so you don't pollute your global Python installation:
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Follow the Installation Guide
I've put together a comprehensive, step-by-step guide to configure your `.env` variables and start the data infrastructure. 

👉 **[Read the Installation Guide](docs/00_Installation_Guide.md)**

### 4. Spin it up!

You can launch the entire platform (Infrastructure, Backend, Frontend, Health Checks) with a single command:

#### Option A: One-Command Startup (Recommended)

* **On Windows (PowerShell):**
  ```powershell
  .\scripts\start.ps1
  # To start without opening the browser automatically:
  .\scripts\start.ps1 -NoBrowser
  ```
* **On Linux / macOS (Bash):**
  ```bash
  ./scripts/start.sh
  # To start without opening the browser automatically:
  ./scripts/start.sh --no-browser
  ```

> 💡 **Tip:** The startup script automatically validates your environment, starts Docker infrastructure, verifies service health, launches FastAPI on port 8000, starts the React Dashboard on port 5173, and opens your browser (unless `-NoBrowser` / `--no-browser` is passed). All logs are conveniently written to the `logs/` directory (`backend.log`, `frontend.log`, `startup.log`, `healthcheck.log`). To stop everything cleanly, run `.\scripts\stop.ps1` (or `./scripts/stop.sh`).

#### Option B: Manual / Dual-Terminal Startup (Legacy Method)

If you prefer to run and inspect the backend and frontend in separate terminal windows manually:

**Terminal 1 (Backend & Infrastructure):**
```bash
docker-compose up -d
cd src/serving/api
uvicorn main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd dashboard
npm run dev
```

Then visit `http://localhost:5173` in your browser to meet your new AI data team and experience the dashboard!

---

## 📚 Documentation

The real treasure of this repository isn't just the code—it's the documentation. I treat our docs like a first-class citizen. 

If you want to understand *how* this was built and *why* I made the decisions I did, start here:

* 📖 **[Documentation Index](docs/README.md)** - The table of contents for everything.
* 🏛️ **[Project Overview](docs/01_Project_Overview.md)** - A deeper dive into the philosophy.
* 🗺️ **[Repository Tour](docs/02_Repository_Tour.md)** - A guided tour of the codebase.
* 📓 **[Developer Journey](docs/developer_journey/01_The_Idea.md)** - Our raw, unfiltered engineering journal. Read about our struggles, our wins, and why I made certain choices.

## 🤝 Contributing

Want to help make the Datalake even smarter? Check out our [Contributing Guide](CONTRIBUTING.md).

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
