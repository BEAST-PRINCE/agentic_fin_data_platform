# 08 - Lessons Learned

*Date: August 2026*

Building the Agentic Datalake was an exercise in smashing two very different worlds together: the deterministic, highly structured world of Data Engineering (Spark, Parquet, SQL), and the non-deterministic, probabilistic world of Generative AI.

Here are the biggest lessons I took away from the journey:

## 1. Local-First is the Ultimate Sandbox
I cannot overstate how valuable it was to build this entirely on Docker Compose with MinIO, DuckDB, Qdrant, and local models/MCP servers. If I had built this on AWS from day one, I would have spent $1,000 in mistakes, out-of-memory errors, and infinite loops. Local-first architecture allows for fearless iteration.

## 2. LLMs are Bad at Formatting, Good at JSON
Trying to make an LLM output a perfectly formatted markdown report while simultaneously running complex logic is a recipe for failure. Separating the "Thinking" (JSON) from the "Formatting" (Markdown) into different agents was the single biggest breakthrough for pipeline stability. 

## 3. Databases are Fast. AI is Slow.
I spent days optimizing Spark partitions and DuckDB thread pools to shave 200 milliseconds off a query. Meanwhile, the LLM took 25 seconds just to generate tokens. The bottleneck in modern AI applications is rarely the database; it is almost always the model inference. Masking that latency with streaming UI updates (the Workflow Accordion) is just as important as writing efficient SQL.

## 4. Documentation is Code
This documentation wasn't written as an afterthought. It was written as part of the engineering process. If you can't explain your architecture clearly in a Markdown file, you probably don't understand it well enough to code it.

*End of Journal.*

---
⬅️ **Previous:** [07 - Observability](07_Observability.md) | **Back to Start:** [Documentation Index](../README.md) 🏠
