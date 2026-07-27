# 19 - Glossary

Data Engineering and Artificial Intelligence both have terrible habits of creating confusing acronyms and jargon. 

When you mash the two fields together, it gets even worse. Here is a plain-English translation of the terminology used throughout this project.

## Data Engineering Terms

* **Lakehouse:** A hybrid architecture that combines the cheap, massive storage of a Data Lake (MinIO) with the structured, fast querying capabilities of a Data Warehouse (DuckDB).
* **Medallion Architecture:** A data design pattern consisting of three layers: Bronze (raw, messy data), Silver (cleaned, deduplicated data), and Gold (aggregated, business-ready data).
* **Parquet:** An open-source, column-oriented data file format. It is vastly superior to CSV for analytical queries because the database only has to read the specific columns it needs from disk, rather than scanning whole rows.
* **Partitioning:** Organizing Parquet files into nested folders based on a column value (e.g., `publish_date=2026-07-27/`). This allows query engines to skip reading irrelevant files, massively speeding up search times.
* **MinIO:** An open-source object storage server that uses the exact same API as Amazon S3. 
* **DuckDB:** An in-process SQL database designed for fast analytical queries (OLAP). It runs inside the Python script rather than as a standalone server.

## AI & Machine Learning Terms

* **LLM (Large Language Model):** The "Brain" (e.g., Llama 3, GPT-4, Claude). It generates text based on patterns. In this project, it is used to power the Agents.
* **Agent:** An LLM wrapped in a Python loop that has been given a specific persona (via a system prompt) and access to tools.
* **MCP (Model Context Protocol):** A standardized way for an AI Agent to request data from an external system. It replaces brittle, custom "tool calling" scripts with a universal protocol.
* **Vector Embedding:** A way of converting text (like a news headline) into an array of numbers (a vector) so that a computer can understand its semantic meaning.
* **Cosine Similarity:** The mathematical formula used to determine how close two vectors are to each other in multi-dimensional space. Used to find articles that share the same "meaning."
* **Qdrant:** The Vector Database. It stores the embeddings and performs the rapid Cosine Similarity math when the AI wants to search for something.
* **KeyBERT:** A machine learning model used to extract the most important keywords/phrases from a block of text.

---
⬅️ **Previous:** [18 - Known Limitations](18_Known_Limitations.md) | **Next:** [20 - FAQ](20_FAQ.md) ➡️
