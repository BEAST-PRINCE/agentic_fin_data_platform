# ADR 004: Using KeyBERT for Semantic Keyword Extraction

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
When analyzing financial news, the AI agents need to know what a specific article is about at a glance. In the Bronze layer, some news scrapers provide "tags," but they are often inaccurate, clickbait, or completely missing. 

To power the `gold_entity_mentions` table—which allows the dashboard to show trending topics—I needed a way to programmatically extract the true "entities" (companies, themes, people) from the raw text of the articles during the Gold layer processing.

## 🤔 Considered Options
1. **Named Entity Recognition (NER) via spaCy:** Very fast, but rigid. It finds "Apple" as an ORG, but might miss broad thematic concepts like "Electric Vehicle Demand."
2. **LLM Extraction (OpenAI API / Llama 3):** Extremely accurate. However, making an API call to an LLM for every single one of the 10,000+ scraped articles would take hours and cost a fortune.
3. **KeyBERT:** A minimal, open-source machine learning model that leverages BERT embeddings to find the sub-phrases in a document that are most semantically similar to the document itself.

## ✅ Decision
I chose **KeyBERT** for semantic keyword extraction in the PySpark Gold layer (`src/processing/gold_layer.py`).

By combining KeyBERT with a lightweight `all-MiniLM-L6-v2` embedding model, I can extract highly relevant bi-grams (two-word phrases) from the article's text without relying on an external LLM.

## 📈 Consequences
* **Positive:** Cost is zero. KeyBERT runs locally alongside the Spark job.
* **Positive:** It extracts themes, not just proper nouns (e.g., it will extract "inflation fears" instead of just "Federal Reserve").
* **Negative:** KeyBERT is inherently slower than regex or simple word counts. To mitigate this bottleneck, I wrapped the KeyBERT extraction in a PySpark `pandas_udf`. This allows KeyBERT to process the articles in large Pandas Series batches on the GPU (or optimized CPU threads), dramatically speeding up the extraction time compared to row-by-row UDFs.

---
⬅️ **Previous:** [ADR 003: Qdrant](003_qdrant.md) | **Next:** [ADR 005: Sentence Transformers](005_sentence_transformers.md) ➡️

### 📚 Further Reading
* [12 - Data Model](../12_Data_Model.md)
