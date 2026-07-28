# ADR 008: Local-First Architecture

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
When building a modern data stack combined with generative AI, the default behavior for most developers is to immediately reach for cloud services: AWS S3, Databricks, Pinecone, and OpenAI.

While these tools are incredible, they come with a massive downside for experimental development: **Cost**. 
Running a multi-stage data pipeline that continuously scrapes data, runs heavy Spark aggregations, generates thousands of vector embeddings, and executes a multi-agent orchestrated reasoning loop can easily rack up a $500 AWS bill in a single weekend if you make a mistake.

I needed an environment where I could fail, write infinite loops, and process millions of rows without looking at a billing dashboard.

## 🤔 Considered Options
1. **Cloud-Native (AWS/GCP):** Infinitely scalable, but expensive and requires complex IAM/Terraform setup just to get a prototype running.
2. **Hybrid:** Host the database locally, but use cloud APIs for embeddings and LLMs.
3. **Local-First:** Run every single component (storage, databases, embeddings, and orchestration) on a local consumer-grade machine using Docker Compose.

## ✅ Decision
I committed strictly to a **Local-First Architecture**.

* Storage is handled by a local **MinIO** container (simulating S3).
* Analytics is handled by local **DuckDB** and **Spark**.
* Vectors are stored in a local **Qdrant** container.
* Embeddings are generated locally using **KeyBERT** and **Sentence Transformers**.
* (Optional) LLMs can be run locally via **Ollama**.

## 📈 Consequences
* **Positive:** Development cost is exactly $0.00. I can process data all day without financial stress.
* **Positive:** Incredible iteration speed. There is no network latency between the backend and the database because they share the same Docker bridge network or the same host machine memory.
* **Positive:** Easy migration. Because MinIO uses the exact S3 API, if the project scales beyond my laptop, I only have to change one line in the `.env` file (`MINIO_ENDPOINT`) to point to a real AWS S3 bucket. The code doesn't change.
* **Negative:** I am constrained by the RAM and CPU of my local machine. I cannot process terabytes of data, and I occasionally hit OutOfMemory (OOM) errors in Spark if I don't batch my processing correctly.

---
⬅️ **Previous:** [ADR 007: MCP](007_mcp.md) | **Next:** [ADR 009: Prometheus](009_prometheus.md) ➡️

### 📚 Further Reading
* [14 - Project Decisions](../14_Project_Decisions.md)
* [21 - Deployment Guide](../21_Deployment_Guide.md)
