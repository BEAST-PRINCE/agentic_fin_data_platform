# ADR 015: The Agent Workflow Accordion (UI)

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
The biggest UX hurdle with Multi-Agent systems is latency. 

When a user asks a complex question, the Orchestrator has to run the Planner, wait for the Researcher to query the database, wait for the Summarizer, wait for the Analyst, and finally wait for the Synthesizer. This entire process can take 20 to 30 seconds.

If a web application hangs for 30 seconds with nothing but a spinning loading wheel, users will assume it is broken and refresh the page, killing the backend process.

## 🤔 Considered Options
1. **Server-Sent Events (SSE) Streaming:** Stream the final answer token-by-token. However, because the Synthesizer agent is the *last* step in the pipeline, the user would still stare at a blank screen for 25 seconds before the first token appeared.
2. **WebSocket Progress Bar:** A simple "20% complete" bar. Not very engaging or informative.
3. **Exposing the "Thoughts" (JSON State):** Stream the intermediate JSON outputs of the agents directly to the UI as they complete their tasks.

## ✅ Decision
I built the **Agent Workflow Accordion** in the React dashboard.

Instead of hiding the complexity of the Multi-Agent system, I turned it into a feature. When the user submits a query, the FastAPI backend immediately begins streaming status updates. 

As soon as the Planner finishes its JSON plan, that plan is pushed to the UI and rendered in a collapsible accordion. As the Researcher fetches articles, the article count pops up. As the Analyst finds risks, they populate the screen.

## 📈 Consequences
* **Positive:** Massive UX improvement. 30 seconds feels like 5 seconds when the user is actively reading the intermediate steps and watching the AI "think."
* **Positive:** Extreme observability. If the final answer is wrong, the user can open the Workflow Accordion, look at the Researcher's JSON evidence package, and immediately see if the database failed to return relevant articles.
* **Negative:** It required building a complex state management system in the React frontend to parse and render the intermediate JSON structures without breaking the UI.

---
⬅️ **Previous:** [ADR 014: Markdown Export Design](014_pdf_export_design.md) | **Back to Start:** [Documentation Index](../README.md) 🏠
