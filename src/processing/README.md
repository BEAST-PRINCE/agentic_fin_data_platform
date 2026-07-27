# Data Processing (`src/processing/`)

## ⚙️ Why does this folder exist?

This is the heavy machinery of the project. Data coming from the scrapers is messy, unstructured, and completely unsuitable for AI agents to query. I built this folder to house my Apache Spark jobs that implement a complete Medallion Lakehouse Architecture (Bronze, Silver, Gold). This is where chaos becomes order.

## 🏭 Responsibilities & Internal Structure

This folder contains the ETL (Extract, Transform, Load) logic that moves data through the lakehouse:

* **Bronze Jobs:** The consumers. They read raw JSON messages from Kafka topics and dump them as-is into MinIO as Parquet files. No schema enforcement, just raw history.
* **Silver Jobs:** The cleaners. They read from Bronze, enforce schemas, deduplicate records, drop nulls, and clean up messy text strings.
* **Gold Jobs:** The aggregators & enrichers. They take the pristine Silver data and format it specifically for the downstream consumers. This includes preparing the exact schema that DuckDB expects, and generating the textual representations that the Vector Search pipeline will embed.

## 🔄 Data Flow

The flow here is the classic Medallion architecture:

`Kafka Topic` ➔ **(Bronze Job)** ➔ `MinIO (Bronze Bucket)` ➔ **(Silver Job)** ➔ `MinIO (Silver Bucket)` ➔ **(Gold Job)** ➔ `MinIO (Gold Bucket)`

## 🔌 Dependencies & Extension Points

* **Dependencies:** PySpark is the king here. These scripts require a working Spark environment and connection to the MinIO object storage.
* **Extension Points:** If I introduce a new data entity (e.g., Company Financials), I will create a new set of Bronze/Silver/Gold PySpark scripts in this folder dedicated to processing that specific entity.

## 🐛 Debugging Tips

* **Thousands of Tiny Files:** If DuckDB is suddenly running very slowly, check the Spark output in this folder. Are the jobs writing thousands of 2KB Parquet files? Look for `.coalesce()` or `.repartition()` calls in the Spark code to optimize file sizes.
* **Silent Failures in Silver:** If data stops arriving in Gold, check the Silver logs. Strict schema enforcement means that if a scraper suddenly changes the format of a date string, the Silver job might silently drop all incoming records as invalid.
* **Spark OutOfMemory (OOM):** If a job crashes locally, it's usually memory. I am running this on local hardware, so tweaking the `spark.executor.memory` and `spark.driver.memory` in the SparkSession builder is critical.
