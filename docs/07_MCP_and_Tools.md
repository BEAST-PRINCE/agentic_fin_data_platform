# 07 - MCP and Tools

Large Language Models are inherently isolated. They only know what was in their training data. 

To make my agents useful, I had to give them tools. I implemented this using the **Model Context Protocol (MCP)**. 

MCP is a standardization that allows the AI agents to request data from my FastAPI backend. Think of it like an API, but designed specifically for an AI to read and execute.

## 🛠️ How MCP Works Here

When the Researcher agent decides it needs information, it looks at a predefined list of tools. 

Every tool has three components:
1. **Name:** A unique identifier (e.g., `retrieve_articles`).
2. **Description:** A highly detailed docstring. *This is the most critical part.* The LLM relies entirely on this text to understand when and how to use the tool.
3. **Input Schema:** A strict JSON schema defining exactly what arguments the tool requires.

If the agent formats the JSON correctly, my FastAPI backend intercepts it, translates it into a DuckDB or Qdrant query, and returns the raw data back to the agent's context window.

## 🧰 The Tool Directory

Here are the exact tools I've armed my agents with, as defined in `src/serving/mcp/server.py`:

### `retrieve_articles`
* **Description:** Search for articles in the Gold layer containing specific keywords or from a specific category. This performs a semantic search over Qdrant.
* **Input:** `keyword` (string), `category` (string, optional), `limit` (integer).
* **Used By:** The Researcher Agent.

### `get_article_by_id`
* **Description:** Fetch a specific article's full content and metadata using its unique article_id.
* **Input:** `article_id` (string).
* **Used By:** The Researcher Agent when it needs deep context on a single piece of news.

### `get_daily_trends`
* **Description:** Get the aggregate daily trends (total articles) broken down by source and category for a date range. This queries DuckDB's `gold_daily_trends` table.
* **Input:** `start_date` (string, YYYY-MM-DD), `end_date` (string, YYYY-MM-DD).
* **Used By:** The Researcher Agent to spot spikes in news volume.

### `get_top_entities`
* **Description:** Retrieve the most frequently mentioned entities (keywords) across all articles for a specific date. This queries DuckDB's `gold_entity_mentions` table.
* **Input:** `publish_date` (string, YYYY-MM-DD), `limit` (integer).
* **Used By:** The Researcher Agent to understand what companies or themes dominated the news cycle on a given day.

## 🚧 MCP Pipeline

I execute the MCP server locally over `stdio` using `anyio`. Because C-level libraries (like PyTorch and Rust tokenizers used by KeyBERT) occasionally write directly to the OS-level `STDOUT` file descriptor, they can corrupt the JSON-RPC pipe that MCP relies on. 

I had to build a custom OS-level file descriptor redirect in `server.py` to route all random stdout logs to stderr, keeping the standard output pure for the agent's JSON communication!

---
⬅️ **Previous:** [06 - Semantic Search](06_Semantic_Search.md) | **Next:** [08 - Multi_Agent_System](08_Multi_Agent_System.md) ➡️
