# 07 - Observability & The Dashboard

*Date: July 2026*

The backend was stable, but the user experience was terrible. 

Because the 5-agent pipeline took 20-30 seconds to run, pinging the API from a terminal script felt like dropping a coin into a bottomless well. I needed deep observability, both for me (the developer) and for the end-user.

For myself, I integrated Prometheus and Grafana. I added custom timing metrics to the API to track the exact execution time of every single agent and MCP tool call. This allowed me to visually see when the LLM was slowing down versus when DuckDB was slow. 

For the end-user, I built a React/Vite dashboard. The primary goal was to mask the AI latency. 
I built the "Agent Workflow" accordion. Instead of a spinning loading wheel, the FastAPI backend streamed the intermediate, non-human-readable JSON state updates from the Planner, Researcher, Summarizer, and Analyst directly to the UI. Watching the AI "think" turned a frustrating 30-second wait into an engaging, transparent experience.

However, the dashboard surfaced a new critical bug: **Session Isolation**. 
If a user asked a question, and then asked a *second* question immediately after, the agents would sometimes corrupt each other's context. The Planner would try to answer the first question using the second question's data. I had to go back into the orchestrator logic and ensure strict conversational boundaries and state resets across consecutive queries, preventing state corruption in the multi-agent pipeline.

With that fixed, the Agentic Datalake finally felt like a complete, mature application.

---
⬅️ **Previous:** [06 - Multi-Agent System](06_Multi_Agent.md) | **Next:** [08 - Lessons Learned](08_Lessons_Learned.md) ➡️
