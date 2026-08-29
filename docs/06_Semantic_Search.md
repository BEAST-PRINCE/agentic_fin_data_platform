# 06 - Semantic Search

When you ask a database for articles about "electric vehicles," a standard SQL query (`LIKE '%electric vehicles%'`) will completely miss articles that only mention "Tesla," "Rivian," or "EV battery supply chains." 

To build an intelligent AI system, I needed the database to understand *meaning*, not just keywords. This is where Semantic Search and Vector Databases come in.

Here is how I gave the Datalake a conceptual understanding of financial news.

## 🧠 The Embedding Model

To search by meaning, you have to turn text into numbers (vectors). 

I chose **MiniLM (`all-MiniLM-L6-v2`)** from the `sentence-transformers` library.
* **Why this model?** Because I am running everything locally. I don't want to pay OpenAI $0.0001 every time I need to vectorize a news headline. MiniLM is incredibly fast, very small (around 80MB), and produces high-quality 384-dimensional embeddings that run easily on CPU.

## 🔑 KeyBERT for Semantic Tagging

KeyBERT is used during Gold processing to extract semantic keywords from the title, description, and content. The vector indexer then embeds the Gold article text (title plus cleaned content); it does not embed only the KeyBERT keyword list.

These keywords are stored as metadata and are also used by the Gold entity-mentions table. They are not the sole input to the Qdrant vector.

## 🎯 Qdrant: The Vector Database

Once I have these 384-dimensional arrays of floating-point numbers, I need a place to store and query them. I chose **Qdrant**.

* **Why Qdrant?** It's written in Rust, it's insanely fast, and it has a fantastic local Docker container. More importantly, it supports **Payload Filtering**.
* **Payloads:** A vector by itself is not enough. The indexer attaches the title, source domain, publication timestamp, source tags, and semantic keywords. The article ID is used as the Qdrant point ID.

## 🔄 The Search Workflow

Here is exactly what happens when the AI Researcher agent wants to find context:

1. **The Query:** The agent asks for "recent supply chain issues in the EV sector."
2. **Vectorization:** The backend uses the configured embedding engine and model to turn that phrase into a vector. The default Sentence Transformers model is `all-MiniLM-L6-v2` with 384 dimensions.
3. **Similarity Search:** We send that vector to Qdrant and ask: *"Find the 5 vectors in your database that have the highest cosine similarity to this one."*
4. **Filtering:** The current `semantic_search` implementation does not apply a date or category payload filter; it only limits the number of similarity results.
5. **The Result:** Qdrant returns stored metadata for the most conceptually similar articles. Full article content can be fetched separately by ID.

This improves retrieval relevance, but it does not eliminate hallucinations; results still depend on source quality, index freshness, model behavior, and agent prompts.

---
⬅️ **Previous:** [05 - Lakehouse](05_Lakehouse.md) | **Next:** [07 - MCP and Tools](07_MCP_and_Tools.md) ➡️
