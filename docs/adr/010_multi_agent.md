# ADR 010: Multi-Agent System

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
When I first built the Datalake, I used a single "Solo Agent." I gave it a massive system prompt telling it how to query DuckDB, how to read Qdrant, how to summarize data, and how to write a final report. 

This failed miserably. The agent would get confused, forget to call tools, hallucinate data, or simply run out of context window when analyzing multiple long articles. I needed a way to execute complex, multi-step research tasks reliably.

## 🤔 Considered Options
1. **Zero-Shot Solo LLM:** Cheap, but highly unreliable for complex workflows.
2. **ReAct Loop (Single Agent):** Better, but the agent's context window fills up quickly with tool call history, causing "attention fatigue."
3. **Multi-Agent Orchestration:** Splitting the problem into small, specialized agents that pass data to each other like an assembly line.

## ✅ Decision
I implemented a **Multi-Agent System** consisting of 5 distinct personas (defined in `instructions.py`):
1. **Planner:** Translates the user query into a JSON task list. (No tools).
2. **Researcher:** Executes the tools via MCP to fetch data.
3. **Summarizer:** Compresses the raw data to save context tokens.
4. **Analyst:** Reasons about the summarized data to find risks/insights.
5. **Synthesizer:** Formats the final human-readable report.

Crucially, the intermediate agents (1 through 4) communicate *exclusively* via strict JSON schemas. They are not allowed to output markdown or conversational text. The orchestration script validates the JSON before passing it to the next agent.

## 📈 Consequences
* **Positive:** Incredible reliability. Because the Planner only has to write a plan (and doesn't have to worry about formatting a final report), it rarely makes mistakes.
* **Positive:** Context window management. By inserting the Summarizer agent between the Researcher and the Analyst, I drastically reduce the token count, allowing the Analyst to reason clearly without getting lost in the noise of 50 raw articles.
* **Negative:** Latency and Cost. Running 5 sequential prompts takes 5 times as long (typically 15-30 seconds) and consumes more tokens than a single prompt.

---
**Next:** [ADR 011: Dashboard Redesign](011_dashboard_redesign.md) ➡️

### 📚 Further Reading
* [08 - Multi-Agent System](../08_Multi_Agent_System.md)
