# 00 - Installation Guide

I designed this project to be entirely local. You don't need AWS credits, an OpenAI API key (if you use a local model), or a Snowflake account. Everything runs on your machine.

Here is how you get it up and running.

## 📋 Prerequisites

Before you start, make sure you have the following installed:

1. **Docker and Docker Compose:** This is non-negotiable. I use Docker to spin up Kafka, Zookeeper, MinIO, Qdrant, Prometheus, and Grafana.
2. **Python 3.11+:** The backend, Spark jobs, and agents are all written in Python.
3. **Node.js 18+ (Optional but recommended):** If you want to run the React dashboard locally for development instead of in a container.
4. **Git:** To clone the repository.

## 🛠️ Step-1: Clone and Environment Setup

First, grab the code:

```bash
git clone https://github.com/yourusername/agentic_datalake.git
cd agentic_datalake
```

Next, set up your Python virtual environment. I highly recommend doing this so you don't pollute your global Python installation.

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

## 🔐 Step-2: Environment Variables

You need an `.env` file at the root of the project. I have provided an `.env.example` file. 

```bash
cp .env.example .env
```

Open `.env` and fill it out. The defaults are generally fine for local Docker Compose execution, but if you want to use external LLMs for the agents (like Anthropic or OpenAI), you will need to paste your API keys here.

## 🐳 Step-3: Spin up the Infrastructure

This is where the magic happens. I put all the heavy lifting into `docker-compose.yml`.

Navigate to the `infra/` folder (or run it from the root depending on where the `docker-compose.yml` lives):

```bash
docker-compose up -d
```

This will download and start:
* **MinIO** (Accessible at `http://localhost:9001`) - Default login is usually `minioadmin` / `minioadmin`.
* **Kafka & Zookeeper** (Running on port 9092)
* **Qdrant** (Accessible at `http://localhost:6333/dashboard`)
* **Prometheus & Grafana** (Grafana at `http://localhost:3000`)

*Wait a minute or two* for Kafka to fully wake up before moving to the next step.

## 🚀 Step-4: Start the API and Dashboard

Once the infrastructure is humming along, you need to start the FastAPI backend.

```bash
cd src/serving/api
uvicorn main:app --reload --port 8000
```

Open a new terminal, and start the React dashboard:

```bash
cd dashboard
npm install
npm run dev
```

The dashboard should now be available at `http://localhost:5173`.

## 🚨 Common Installation Errors

* **"Port already in use" (e.g., 9000 or 3000):** You probably have another service running on your machine taking up MinIO's or Grafana's port. Stop the conflicting service, or change the port mapping in `docker-compose.yml`.
* **"Kafka Broker not available":** Sometimes Kafka takes a while to start up, or Docker networking is being stubborn. Try `docker-compose restart kafka`.
* **"ModuleNotFoundError: No module named 'pyspark'":** You forgot to activate your virtual environment before running the Spark jobs!

## 🎉 First Successful Run

To test if everything works:
1. Open MinIO (`localhost:9001`) and create the `bronze`, `silver`, and `gold` buckets if they aren't created automatically.
2. Run one of the scrapers in `src/scrapers/`.
3. Check your FastAPI logs. If it's silent and not throwing errors, you're good.
4. Go to the dashboard and type: "What is the latest news regarding Apple?" If the agents respond, you have successfully built a multi-agent lakehouse.

---
⬅️ **Previous:** [Documentation Index](README.md) | **Next:** [01 - Project Overview](01_Project_Overview.md) ➡️
