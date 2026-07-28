# 04 - The Lakehouse 

*Date: May 2026*

With Spark successfully cleaning data, I needed a place to store it that wasn't just a local Windows folder. 

I decided to deploy MinIO via Docker Compose. It instantly gave my local environment a true S3-compatible API. I could now write my Spark jobs using `s3a://` URIs, which meant the code was completely cloud-ready. 

But storing data is only half the battle. I needed to query it.

I originally looked at PostgreSQL. But setting up a Postgres container, defining schemas, and writing a daily ETL job to pull data out of MinIO and push it into Postgres felt exhausting. I didn't want to duplicate my data.

That's when I discovered DuckDB.

DuckDB blew my mind. It could sit directly inside my FastAPI Python backend and query the Parquet files sitting in MinIO using the `httpfs` extension. No external database server required.

But there was a catch. When I hooked DuckDB up to my FastAPI server, I created a single global connection object. FastAPI is highly concurrent. When I fired multiple API requests at it simultaneously, the global DuckDB connection locked up. It forced every API request to wait in line sequentially. 

I had to dive deep into threading. I ended up implementing a `threading.local()` connection pool in `db_client.py`. Every time a FastAPI worker thread needed to query the Lakehouse, it got its own isolated, in-memory DuckDB instance pointing to MinIO. The performance skyrocketed. The API could now handle massive concurrent aggregations instantly.

---
⬅️ **Previous:** [03 - Data Engineering](03_Data_Engineering.md) | **Next:** [05 - Vector Search](05_Vector_Search.md) ➡️
