# 06 - The Multi-Agent System

*Date: Late June 2026*

With the Lakehouse and Vector DB fully operational, it was time to build the "Brain."

Initially, I tried building a single, massive LLM prompt. I gave it access to database tools and told it to do everything. It failed constantly. The context window filled up, it forgot to call tools, and it hallucinated data.

I needed to break the task down into specialized agents. 

To connect the agents to my databases, I didn't want to use brittle LangChain wrappers. I spent some time researching external plugin architectures (even investigating how things like the `ponytail` agent plugin worked) to understand how to build robust tool integrations. This led me to the **Model Context Protocol (MCP)**. 

MCP was a game changer. I wrapped my database queries in an MCP server running over `stdio`. But that introduced *another* C-level bug: machine learning libraries (like tokenizers) often print warnings directly to the OS-level `STDOUT`. MCP relies on `STDOUT` to pass JSON messages. Those random warnings corrupted the JSON stream, crashing the agents. I had to write a low-level `os.dup2` redirect to force all random prints to `STDERR`, saving the pure JSON communication pipe.

For orchestration, I adopted the **Google Agentic Development Kit (ADK)**. It had native MCP support and was much cleaner than LangChain. 

I finally settled on a strict 5-agent pipeline: Planner -> Researcher -> Summarizer -> Analyst -> Synthesizer. To prevent the LLMs from getting confused by conversational text, I forced the intermediate agents to communicate exclusively using strict JSON schemas. The Multi-Agent system was finally stable, and highly accurate.

---
⬅️ **Previous:** [05 - Vector Search](05_Vector_Search.md) | **Next:** [07 - Observability](07_Observability.md) ➡️
