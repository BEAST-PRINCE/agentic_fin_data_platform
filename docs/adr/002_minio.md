# ADR 002: Using MinIO for the Local Data Lake

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
This project utilizes a Medallion Architecture (Bronze, Silver, Gold). This requires storing raw JSON scrapes, cleaned intermediate data, and highly structured Parquet tables. 

Initially, I could have just saved these files directly to the local file system (e.g., `d:/data/bronze/`). However, building data pipelines against local file paths (`file:///`) creates extreme tech debt. If I ever wanted to deploy this project to the cloud, I would have to rewrite every Spark script and DuckDB connection string. 

I needed a local storage solution that mimicked enterprise cloud storage.

## 🤔 Considered Options
1. **Local File System:** Easy to set up. Impossible to scale. Terrible for cloud migration.
2. **Localstack (AWS Mock):** Simulates S3 perfectly, but is incredibly heavy and resource-intensive because it tries to mock the entire AWS ecosystem.
3. **MinIO:** A high-performance, open-source object storage server that is 100% API compatible with Amazon S3.

## ✅ Decision
I chose **MinIO** as the foundation of the Lakehouse.

MinIO runs in a lightweight Docker container (`infra/docker-compose.yml`) and exposes an S3-compatible API on port 9000. 

All Spark jobs and DuckDB connections are configured to use the `s3a://` protocol. They authenticate with MinIO using standard Access and Secret keys defined in the `.env` file, exactly as they would with a real AWS S3 bucket.

## 📈 Consequences
* **Positive:** **"Cloud-Ready" Code.** Because the code is already written using `s3a://`, migrating this project to AWS or GCP requires exactly zero code changes. I only need to update the `MINIO_ENDPOINT` in the `.env` file to point to the real cloud bucket.
* **Positive:** MinIO provides a beautiful web console (port 9001) that allows me to visually inspect the Parquet partitions and debug data issues easily.
* **Negative:** It adds a slight overhead to the Docker Compose stack compared to writing to a local folder, but the architectural purity is absolutely worth the 200MB of RAM MinIO consumes.

---
⬅️ **Previous:** [ADR 001: DuckDB](001_duckdb.md) | **Next:** [ADR 003: Qdrant](003_qdrant.md) ➡️

### 📚 Further Reading
* [04 - Data Pipeline](../04_Data_Pipeline.md)
* [21 - Deployment Guide](../21_Deployment_Guide.md)
