# 03 - Data Engineering 

*Date: April 2026*

To fix the brittleness of the raw JSON scrapes, I adopted the Medallion Architecture (Bronze, Silver, Gold).

I introduced Apache Spark to handle the heavy lifting. The plan was beautiful:
1. Scrapers push to Kafka.
2. Spark reads Kafka and dumps raw JSON to the Bronze layer.
3. A Silver Spark job cleans it.
4. A Gold Spark job structures it.

But distributed computing is never that simple. 

I hit my first major roadblock when the Gold layer pipeline started acting strange. It wasn't crashing, but it was stalling. A PySpark job that usually took 30 seconds suddenly started taking 40 minutes. 

It took me days to diagnose this. The job was silently failing when trying to read the incremental state JSON file (`silver_state.json`) which had become corrupted. Because of the silent exception handling in my PySpark script, instead of throwing an error and stopping, the script simply caught the exception and fell back to the default date: `1970-01-01`. 

It was silently reprocessing the entire historical Bronze bucket every single time I ran it! I fixed the error-handling logic, cleaned up the corrupted S3 data, and the pipeline went back to taking 30 seconds. 

That was a hard lesson in the dangers of `try...except pass` in data engineering.

## The "Serious Upgrades"

Eventually, I reached the end of the Phase 4 execution plan. The Gold layer was officially built. My PySpark job was happily churning out aggregations, everything was landing in the `gold` MinIO bucket, and the script was executing flawlessly. 

I felt like a true Data Engineering god. I sat back in my chair, opened my AI coding agent, and proudly asked:

*"Is the Phase 4 fully complete as per the execution plan?? Check if anything is left or any serious upgrade that needs to be done."*

I fully expected a digital pat on the back. Instead, my own AI agent effectively looked at my flat Parquet files, sighed, and told me that while it was technically "complete," it wasn't exactly "industry-grade." 

It handed me a list of "Serious Upgrades." 

The biggest offender? **Data Partitioning**. I was dumping everything into massive, unpartitioned Parquet files. The AI politely informed me that if I didn't partition the Gold tables by `publish_date`, DuckDB was going to choke on full-table scans the moment the dataset grew. 

It was a humbling moment. You build a state-of-the-art AI Datalake, and the very AI you built it with tells you that you forgot basic Hive-style partitioning. I immediately went back to the drawing board, implemented strategic partitioning for the aggregate tables, but stubbornly left `gold_articles_serving` unpartitioned just to ensure my point-lookups (by UUID) stayed fast. Take that, AI.

---
⬅️ **Previous:** [02 - First Prototype](02_First_Prototype.md) | **Next:** [04 - Lakehouse](04_Lakehouse.md) ➡️
