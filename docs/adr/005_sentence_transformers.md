# ADR 005: Using Sentence Transformers for Embeddings

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
To make the financial news searchable by the AI agents via Qdrant (the Vector Database), the text of the articles must be converted into numerical vectors (embeddings). 

The industry default is to use OpenAI's `text-embedding-3-small` or `text-embedding-3-large`. However, passing every single historical article through an external API during the `vector_indexer.py` job violates the Local-First philosophy of this project and introduces a massive network bottleneck.

## 🤔 Considered Options
1. **OpenAI / External API:** High quality, but requires network calls, API costs, and sacrifices data privacy.
2. **Ollama / Local LLMs (Llama 3):** Great for generating text, but very heavy and slow for generating thousands of embeddings in a batch process.
3. **Sentence Transformers (`sentence-transformers` library):** Specifically designed to generate high-quality embeddings locally using small, hyper-optimized models.

## ✅ Decision
I chose the **Sentence Transformers** Python library, specifically standardizing on the `all-MiniLM-L6-v2` model.

This model maps sentences and paragraphs to a 384-dimensional dense vector space. It is incredibly small (under 100MB) and runs blindingly fast on a local CPU, and even faster if CUDA (NVIDIA GPU) is available. 

This is implemented in `src/processing/embeddings.py` (via the `EmbedderFactory`) and used heavily in `vector_indexer.py` to upsert data into Qdrant.

## 📈 Consequences
* **Positive:** Complete data privacy. The raw scraped text never leaves the local network.
* **Positive:** Speed. Because the model is loaded into memory, the `vector_indexer` can batch process 64 articles at a time, generating embeddings in milliseconds.
* **Negative:** A 384-dimensional vector from MiniLM is not quite as nuanced as a 1536-dimensional vector from OpenAI, meaning it might struggle slightly with highly complex, nuanced financial reasoning queries. However, because we also attach KeyBERT semantic tags and DuckDB tabular data to the payload, the agents still have plenty of accurate context.

---
⬅️ **Previous:** [ADR 004: KeyBERT](004_keybert.md) | **Next:** [ADR 006: Google ADK](006_google_adk.md) ➡️

### 📚 Further Reading
* [06 - Semantic Search](../06_Semantic_Search.md)
