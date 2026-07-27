# 17 - Troubleshooting

> *Disclaimer: If you encounter an error not listed here, don't panic. Just copy the stack trace, @-mention your favorite AI Coding Agent, and tell them to fix it for you. We live in the future now—don't debug alone!* 🙃

If you prefer to fix things yourself, here is a catalog of the most common issues in the Agentic Datalake.

## 🐋 Infrastructure Issues (Docker)

### "Kafka Broker not available"
* **Symptom:** Scrapers throw connection errors, or the Spark Bronze job crashes immediately on startup.
* **Cause:** Kafka is notoriously slow to start up. Zookeeper has to boot, then Kafka has to register.
* **Fix:** Wait 60 seconds after running `docker-compose up -d`. If it still fails, run `docker-compose restart kafka`.

### "MinIO connection refused" or "S3A Error"
* **Symptom:** Spark jobs fail with `java.net.ConnectException: Connection refused` or DuckDB throws an IO Error.
* **Cause:** Your code is trying to reach MinIO on `localhost:9000`, but if the code is running *inside* another Docker container (like the API), `localhost` refers to that container, not the host machine.
* **Fix:** Ensure your `.env` is correctly mapping `MINIO_ENDPOINT`. Use `localhost:9000` when running Spark/FastAPI directly on your host machine, but use `minio:9000` if they are running in the Docker bridge network.

## 🐍 Python & C-Level Issues

### MCP Server JSON-RPC Corruption
* **Symptom:** The Agent Orchestrator says "Failed to parse JSON" when calling an MCP tool.
* **Cause:** You imported a library (like PyTorch or `transformers`) that prints initialization warnings directly to standard output (STDOUT) using C-level bindings. MCP uses STDOUT to communicate via JSON. The warning corrupts the JSON stream.
* **Fix:** Look at `src/serving/mcp/server.py`. You MUST maintain the OS-level `os.dup2(2, 1)` redirect to force all rogue print statements to STDERR before importing heavy ML libraries.

### PyTorch / OpenMP Deadlock
* **Symptom:** The FastAPI server completely hangs on startup or during the first search request. No errors, just frozen.
* **Cause:** FastAPIs `anyio` thread workers clash with PyTorch's C++ OpenMP multi-threading if the embedding model is initialized lazily inside a background thread.
* **Fix:** Always pre-load the embedding models on the main thread during FastAPI's `@app.on_event("startup")` hook (as seen in `main.py`).

## ⚙️ Data Pipeline Issues

### Spark OutOfMemory (OOM) Error
* **Symptom:** The Gold layer job crashes with `java.lang.OutOfMemoryError: Java heap space`.
* **Cause:** You are trying to process too much data on a local machine without enough RAM assigned to the Spark JVM.
* **Fix:** Increase the memory allocation in the `SparkSession.builder` by adding `.config("spark.driver.memory", "4g")` or process the data in smaller incremental batches.

### The Pipeline is "Stuck" doing a Full-Load
* **Symptom:** The Spark job takes 40 minutes instead of 30 seconds.
* **Cause:** The PySpark job encountered a silent exception when trying to read the incremental state JSON file from MinIO, causing it to fall back to the `1970-01-01` default date and reprocess the entire Bronze bucket.
* **Fix:** Check the `system-logs` bucket in MinIO and verify that the `silver_state.json` and `vector_indexer_state.json` files are not corrupted.

---
⬅️ **Previous:** [16 - Performance and Scaling](16_Performance_and_Scaling.md) | **Next:** [18 - Known Limitations](18_Known_Limitations.md) ➡️
