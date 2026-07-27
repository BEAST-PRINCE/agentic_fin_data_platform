# Agents (`src/agents/`)

## 🤖 Why does this folder exist?

This folder contains the "intelligence" of my platform. Instead of a single, monolithic LLM prompt trying to do everything at once (and failing), I built a multi-agent system. Each agent in this folder has a specific role, distinct prompts, and a designated place in the reasoning pipeline.

## 👥 Responsibilities & Internal Structure

Here is how I divided the labor among my agents:

* **Planner Agent:** The manager. When a user asks a complex question, the Planner breaks it down into actionable steps.
* **Researcher Agent:** The data gatherer. It takes the Planner's steps and uses MCP tools to query DuckDB and Qdrant for facts.
* **Analyst Agent:** The number cruncher. It looks at the raw data the Researcher found and performs financial analysis or trend identification.
* **Summarizer / Synthesizer Agent:** The communicator. It takes the messy, JSON-heavy output from the Analyst and Researcher, and drafts a clean, human-readable final response for the dashboard.

## 🔄 Data Flow

1. User query enters via the API.
2. The **Planner** creates an execution plan.
3. The **Researcher** executes the plan, fetching context.
4. The **Analyst** processes the fetched context.
5. The **Synthesizer** formats the final output.
6. The final output (and the intermediate steps) are returned to the React dashboard.

## 🔌 Dependencies & Extension Points

* **Dependencies:** These agents rely heavily on the MCP tools defined in `src/serving/`. They also require access to a local LLM or API provider to generate responses.
* **Extension Points:** Adding a new agent is simple. Create a new agent class, define its system prompt, and insert it into the pipeline workflow defined in the orchestrator.

## 🐛 Debugging Tips

* **Agent Hallucinations:** If an agent is making things up, check the prompt in this folder first. It might be lacking strict constraints. Also, check if the MCP tools are actually returning data (an agent with no data will try to guess).
* **Workflow Stalling:** If the multi-agent pipeline hangs, it usually means an agent is failing to output valid JSON for the next step. Check the raw LLM outputs in the console logs.
