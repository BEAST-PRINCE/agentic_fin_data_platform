# 05 - Vector Search (and the PyTorch Deadlocks)

*Date: June 2026*

DuckDB was great for answering questions like, "How many articles were published yesterday?" But it was terrible at answering questions like, "What are the risks to the EV market?"

I needed semantic search. I deployed Qdrant (a Rust-based vector database) and integrated the `sentence-transformers` library to generate embeddings locally using the `all-MiniLM-L6-v2` model.

This is where I hit the most infuriating bug of the entire project.

I wrote an API endpoint to perform a semantic search. When I hit the endpoint for the first time, the FastAPI server completely froze. No error message. No stack trace. Just silence.

I spent hours adding print statements everywhere. I eventually traced the freeze to the exact line where `sentence-transformers` was loaded into memory. 

It turns out that PyTorch (which powers the embeddings) uses a C++ threading library called OpenMP. FastAPI uses an asynchronous library called `anyio` to manage background worker threads. When `anyio` spun up a new background thread to handle an API request, and *then* PyTorch tried to initialize OpenMP inside that background thread on Windows... they deadlocked. 

The fix was deceptively simple: I had to move the model initialization to the main thread during FastAPI's `@app.on_event("startup")` hook. By loading the heavy C-level ML libraries before any async workers were spawned, the deadlock disappeared. 

I also integrated KeyBERT to extract semantic keywords during the Spark Gold job. Running row-by-row Python UDFs was too slow, so I learned how to use PySpark's `pandas_udf` to feed chunks of the dataset into KeyBERT, letting it run batch processing on the GPU. The semantic pipeline was finally optimized.

---
⬅️ **Previous:** [04 - Lakehouse](04_Lakehouse.md) | **Next:** [06 - Multi-Agent System](06_Multi_Agent.md) ➡️
