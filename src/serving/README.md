# Serving & API (`src/serving/`)

## 🚀 Why does this folder exist?

All the data in the world is useless if you can't interact with it. This folder is the bridge between my backend infrastructure (Lakehouse, Vector Database, AI Agents) and the front-end user experience (React Dashboard). It serves the API endpoints and, crucially, defines the MCP (Model Context Protocol) tools that give my AI agents their superpowers.

## 🌉 Responsibilities & Internal Structure

This folder contains the FastAPI application and its associated routers.

* **API Endpoints:** Handles incoming HTTP requests from the React dashboard (e.g., retrieving historical data, sending a chat message, checking pipeline status).
* **MCP Tool Definitions:** This is where I define the exact schemas, inputs, and descriptions for the tools the Multi-Agent system uses. When the Researcher agent wants to "search for recent Apple news," it calls a Python function defined here.
* **Orchestration:** Kicking off the agent workflow when a user submits a query.

## 🔄 Data Flow

`React Dashboard` ➔ `FastAPI Route` ➔ `Agent Orchestrator` ➔ `MCP Tool Execution` ➔ `Database (DuckDB/Qdrant)` ➔ `Agent Reasoning` ➔ `FastAPI Response` ➔ `React Dashboard`

## 🔌 Dependencies & Extension Points

* **Dependencies:** Built heavily on `FastAPI` and `Pydantic` for strict request/response validation. It relies on `src/storage/` to actually execute the database queries.
* **Extension Points:**
  * Need a new chart on the dashboard? Add a new `GET` route here.
  * Want the agents to be able to do something new (like calculate a moving average)? Define a new MCP tool function here and expose it to the agents.

## 🐛 Debugging Tips

* **Pydantic Validation Errors:** If the dashboard suddenly stops working and the API returns a 422 Unprocessable Entity, check the Pydantic schemas defined here against the actual JSON being returned by the database layer.
* **Agent Tool Failures:** If an agent tries to use a tool and hallucinates the arguments, check the tool's docstring and Pydantic schema in this folder. The LLM relies *entirely* on those text descriptions to understand how to format its tool call. If the description is vague, the agent will guess (and usually guess wrong).
