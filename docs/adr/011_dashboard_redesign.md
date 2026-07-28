# ADR 011: Dashboard Redesign (React/Vite over Streamlit)

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
In the early days of the project, interaction with the AI was done via the terminal or a very basic Streamlit prototype. While Streamlit is fantastic for rapid prototyping in Python, it fundamentally struggles with complex, asynchronous state management and real-time streaming UI updates.

As the Multi-Agent system grew to take 20+ seconds to respond, a simple Streamlit spinner was no longer an acceptable user experience. Furthermore, because my intermediate agents were forced to output strict JSON schemas, the frontend was occasionally dumping 50 lines of unreadable "matrix code" directly into the user's chat window before arriving at the final synthesized answer. The users (and I) needed a UI capable of isolating this raw JSON while still showing *what* the agents were doing in real-time.

## 🤔 Considered Options
1. **Streamlit / Gradio:** Easy to write in Python, but severely limited in UI customization and complex async state management.
2. **Next.js:** Very powerful, but overkill for a dashboard that doesn't need SEO or server-side rendering.
3. **React + Vite:** The industry standard for Single Page Applications (SPAs). Lightning fast development server, massive ecosystem of charting libraries.

## ✅ Decision
I chose **React compiled with Vite** for the frontend dashboard (`/dashboard/`). 

The dashboard connects to the FastAPI backend via standard REST endpoints. I utilized TailwindCSS for styling to ensure the interface felt modern, responsive, and clean without writing thousands of lines of custom CSS. 

## 📈 Consequences
* **Positive:** Total UI control. I was able to build the "Agent Workflow Accordion" (see ADR 015) which requires fine-grained DOM updates that Streamlit cannot handle cleanly.
* **Positive:** The Vite development server provides sub-second hot-module replacement (HMR), making frontend iterations incredibly fast.
* **Negative:** It requires maintaining two separate tech stacks (Python for backend/data, TypeScript/JavaScript for frontend) and running two separate development servers during debugging.

---
⬅️ **Previous:** [ADR 010: Multi-Agent System](010_multi_agent.md) | **Next:** [ADR 012: DuckDB Query Service](012_duckdb_query_service.md) ➡️

### 📚 Further Reading
* [09 - Dashboard](../09_Dashboard.md)
