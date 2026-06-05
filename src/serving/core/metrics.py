from prometheus_client import Gauge, Counter, Histogram

# --- Platform Health Metrics ---
KAFKA_UP = Gauge("kafka_up", "1 if Kafka is reachable, 0 otherwise")
MINIO_UP = Gauge("minio_up", "1 if MinIO is reachable, 0 otherwise")
DUCKDB_UP = Gauge("duckdb_up", "1 if DuckDB is reachable, 0 otherwise")
QDRANT_UP = Gauge("qdrant_up", "1 if Qdrant is reachable, 0 otherwise")
LAKEHOUSE_READY = Gauge("lakehouse_ready", "1 if all data lake components are healthy, 0 otherwise")

# --- Lakehouse Data Metrics ---
BRONZE_RECORDS = Gauge("bronze_records_total", "Total raw messages in Bronze layer")
SILVER_RECORDS = Gauge("silver_records_total", "Total cleaned articles in Silver layer")
GOLD_RECORDS = Gauge("gold_records_total", "Total serving articles in Gold layer")

# --- Vector Search Metrics ---
VECTOR_SEARCH_REQUESTS = Counter("vector_search_requests_total", "Total number of semantic search requests")
VECTOR_SEARCH_LATENCY = Histogram("vector_search_latency_seconds", "Latency of semantic search requests in seconds")
QDRANT_VECTORS_TOTAL = Gauge("qdrant_vectors_total", "Total vectors stored in Qdrant")
