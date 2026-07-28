# ADR 006: Using Google Agentic Development Kit (ADK)

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
Once the data pipeline was built and the MCP (Model Context Protocol) server was running, I needed a way to actually build the AI Agents. 

The industry standard for building agents is LangChain or LlamaIndex. However, writing custom multi-agent orchestration loops in LangChain often results in deeply nested, brittle, and overly abstracted code that is very difficult to debug when an agent enters an infinite loop or drops a tool call.

I needed a framework that was explicit, natively supported the Model Context Protocol (MCP), and allowed for clear state management between the Planner, Researcher, Analyst, and Synthesizer agents.

## 🤔 Considered Options
1. **LangChain / LangGraph:** Powerful, but extremely abstracted. Native MCP support often requires complex wrapper classes.
2. **AutoGen (Microsoft):** Great for conversational agents, but felt too heavy for a strict, deterministic pipeline.
3. **Google Agentic Development Kit (ADK):** A newer SDK designed specifically for building reliable, production-grade agents with native, first-class support for MCP toolsets.

## ✅ Decision
I chose the **Google ADK** as the core orchestration framework for the Multi-Agent system (`src/serving/agent/common.py`).

Instead of writing custom LangChain wrappers to hit my FastAPI server, I simply use `McpToolset` from `google.adk.tools` and pass it the `StdioConnectionParams` pointing to my local `server.py`. 

The ADK seamlessly connects the underlying LLM (whether it is an OpenAI model, Anthropic, or local Ollama model routed via LiteLLM) to the MCP server.

## 📈 Consequences
* **Positive:** Unbelievably clean code. In `src/serving/agent/common.py`, connecting the entire Lakehouse to the AI agent requires less than 15 lines of code.
* **Positive:** Because the ADK handles the MCP JSON-RPC protocol natively, I didn't have to write any HTTP retry logic or error handling for the tool calls.
* **Negative:** The ADK is slightly less ubiquitous than LangChain, meaning finding StackOverflow answers for obscure errors requires more reading of the actual source code.

---
⬅️ **Previous:** [ADR 005: Sentence Transformers](005_sentence_transformers.md) | **Next:** [ADR 007: MCP](007_mcp.md) ➡️

### 📚 Further Reading
* [08 - Multi-Agent System](../08_Multi_Agent_System.md)
