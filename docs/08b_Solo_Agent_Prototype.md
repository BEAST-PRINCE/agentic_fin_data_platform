# 08b. The Solo Agent Prototype

While the Agentic Datalake is primarily driven by a 5-stage Multi-Agent pipeline, the repository still contains the original **Solo Agent** prototype (`src/serving/agent/solo_agent.py`). 

This document explains what it is, how it works, and why it was ultimately superseded by the Multi-Agent system.

## 🤖 What is the Solo Agent?

The Solo Agent is a single Google Agentic Development Kit (ADK) agent. Instead of breaking down a user query into a plan, researching, summarizing, and synthesizing sequentially, the Solo Agent is given a massive system prompt and direct access to all Model Context Protocol (MCP) tools at once.

### The System Prompt
The agent is instructed to be the "Datalake Intelligence Agent" and is given strict directives:
- Use tools first (never rely on base knowledge).
- Cite source domains and publish dates.
- Output clean Markdown instead of raw JSON.

## 🛠️ How to Run It

You can run the Solo Agent directly from the terminal for testing or simple queries without spinning up the full FastAPI backend and React dashboard.

```bash
# Ensure your virtual environment is active
python -m src.serving.agent.solo_agent
```

This spins up an interactive terminal session where you can chat directly with the agent. It will use the `StdioConnectionParams` to spin up a local MCP server subprocess and connect to the DuckDB/Qdrant lakehouse.

## 📉 Why it Failed (The "Serious Upgrades")

As documented in our Developer Journey and ADR 010, the Solo Agent was a great prototype but failed to scale into an "industry-grade" solution.

When testing complex queries (e.g., "Analyze the risks to the EV market over the past week and format as a report"), the Solo Agent struggled significantly:
1. **Attention Fatigue:** The agent would fetch 10 articles, filling its context window with thousands of tokens. By the time it reached the end of the data, it forgot the original prompt instructions and would hallucinate facts.
2. **Formatting vs. Reasoning:** Trying to make a single LLM reason about complex financial data *while simultaneously* forcing it to output perfectly formatted Markdown is a recipe for failure. 
3. **Session Cross-Talk:** Because it held the entire conversation history in a single memory buffer, consecutive questions would bleed into each other, leading to hallucinations (like confusing Tesla's battery supply chain with general interest rate hikes).

### The Solution
These failures directly inspired the **Multi-Agent System** (Planner -> Researcher -> Summarizer -> Analyst -> Synthesizer). By isolating the JSON "Thinking" from the Markdown "Formatting," and forcing strict state resets, the pipeline became drastically more stable.

The Solo Agent remains in the codebase as a lightweight, terminal-based fallback, and as a stark reminder of why orchestration is necessary in Generative AI.

---
⬅️ **Previous:** [08 - Multi-Agent System](08_Multi_Agent_System.md) | **Next:** [09 - Dashboard](09_Dashboard.md) ➡️
