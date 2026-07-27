# 06 - Semantic Search

When you ask a database for articles about "electric vehicles," a standard SQL query (`LIKE '%electric vehicles%'`) will completely miss articles that only mention "Tesla," "Rivian," or "EV battery supply chains." 

To build an intelligent AI system, I needed the database to understand *meaning*, not just keywords. This is where Semantic Search and Vector Databases come in.

Here is how I gave the Datalake a conceptual understanding of financial news.

## 🧠 The Embedding Model

To search by meaning, you have to turn text into numbers (vectors). 

I chose **MiniLM (`all-MiniLM-L6-v2`)** from the `sentence-transformers` library.
* **Why this model?** Because I am running everything locally. I don't want to pay OpenAI $0.0001 every time I need to vectorize a news headline. MiniLM is incredibly fast, very small (around 80MB), and produces high-quality 384-dimensional embeddings that run easily on CPU.

## 🔑 KeyBERT for Semantic Tagging

I don't just embed the raw text of an article. That can sometimes dilute the meaning if the article is long.

Before generating the final embedding, I pass the text through **KeyBERT**. 
KeyBERT uses BERT embeddings to find the sub-phrases in a document that are the most similar to the document itself. 

So, an article about a new factory in Berlin might get semantic tags like: `['Gigafactory expansion', 'Berlin manufacturing', 'European EV market']`. I embed these highly concentrated semantic tags instead of (or alongside) the raw text, which dramatically improves search relevance.

## 🎯 Qdrant: The Vector Database

Once I have these 384-dimensional arrays of floating-point numbers, I need a place to store and query them. I chose **Qdrant**.

* **Why Qdrant?** It's written in Rust, it's insanely fast, and it has a fantastic local Docker container. More importantly, it supports **Payload Filtering**.
* **Payloads:** A vector by itself is useless. When I store a vector in Qdrant, I attach a JSON payload containing the article's URL, the publication date, and the ticker symbol.

## 🔄 The Search Workflow

Here is exactly what happens when the AI Researcher agent wants to find context:

1. **The Query:** The agent asks for "recent supply chain issues in the EV sector."
2. **Vectorization:** The backend uses MiniLM to turn that exact phrase into a 384-dimensional vector.
3. **Similarity Search:** We send that vector to Qdrant and ask: *"Find the 5 vectors in your database that have the highest cosine similarity to this one."*
4. **Filtering:** We also pass a filter to Qdrant: *"Only return vectors where the payload `date` is within the last 7 days."*
5. **The Result:** Qdrant returns the payloads (the actual text and URLs) of the 5 most conceptually relevant articles, which the agent then uses to write its report.

By combining the structured filtering of payloads with the fuzzy conceptual matching of cosine similarity, the agents almost never suffer from hallucination due to lack of context.

---
⬅️ **Previous:** [05 - Lakehouse](05_Lakehouse.md) | **Next:** [07 - MCP and Tools](07_MCP_and_Tools.md) ➡️
