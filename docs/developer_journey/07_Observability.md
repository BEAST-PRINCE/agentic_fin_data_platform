# 07 - Observability & The Dashboard

*Date: July 2026*

The backend was stable, but the user experience was terrible. 

Because the 5-agent pipeline took 20-30 seconds to run, pinging the API from a terminal script felt like dropping a coin into a bottomless well. I needed deep observability, both for me (the developer) and for the end-user.

For myself, I integrated Prometheus and Grafana. I added custom timing metrics to the API to track the exact execution time of every single agent and MCP tool call. This allowed me to visually see when the LLM was slowing down versus when DuckDB was slow. 

For the end-user, I built a React/Vite dashboard. I had a major problem: the Multi-Agent pipeline was spitting out raw, intermediate JSON thoughts directly into the final chat UI. Users would ask "What is Nvidia's stock doing?" and the UI would dump 50 lines of JSON from the Researcher agent before finally giving the answer.

I needed to isolate the JSON. I spent days wrestling with React state, eventually building the **Agent Workflow Accordion**. I shoved all the raw JSON from the Planner, Researcher, Summarizer, and Analyst into collapsible UI elements. This was a massive win for observability—you could literally watch the agents "think" without the UI looking like a matrix code dump. Watching the AI "think" turned a frustrating 30-second wait into an engaging, transparent experience.

But then, the final boss of the project appeared: **Session Isolation Corruption**.

During testing, I asked the dashboard a question about "Tesla." It gave a great answer. Then, in the same session, I asked a completely unrelated question about "Interest Rates." The Analyst agent confidently told me that Interest Rates were affecting Tesla's battery production. 

The agents were experiencing extreme cross-talk. Because the API endpoints weren't properly isolating the state between consecutive queries, the Planner and Analyst were happily mixing context from previous questions into the new ones. It was like trying to have a serious conversation with someone who couldn't stop bringing up their ex.

I had to rip open the multi-agent orchestrator (`src/serving/agent/multi_agent/runner.py`) and rigorously enforce state resets. I explicitly cleared the memory buffers and forced the pipeline to instantiate entirely new agent instances for every single query. 

With that fixed, the Agentic Datalake finally felt like a complete, mature application.

---
⬅️ **Previous:** [06 - Multi-Agent System](06_Multi_Agent.md) | **Next:** [08 - Lessons Learned](08_Lessons_Learned.md) ➡️
