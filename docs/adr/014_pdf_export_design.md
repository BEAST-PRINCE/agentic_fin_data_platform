# ADR 014: Markdown-Native Report Generation

**Status:** Accepted  
**Date:** July 2026  

## 📜 Context and Problem Statement
A core feature of the Agentic Datalake is its ability to act as an automated financial analyst. When a user asks, "Generate a report comparing Qualcomm and Nvidia's market risks," they expect a formal, professional document—not just a chat bubble. 

Initially, I considered building a backend PDF generation service using Python libraries like `reportlab` or `WeasyPrint` to convert the AI's output into a downloadable PDF report.

## 🤔 Considered Options
1. **Backend PDF Generation (ReportLab):** Heavy, requires complex font management, and styling is a nightmare to code in Python.
2. **HTML Generation:** Have the AI output raw HTML. Very prone to injection attacks and broken tags if the LLM hallucinates formatting.
3. **Markdown-Native Output:** Force the Synthesizer agent to output strict GitHub-flavored Markdown, and let the React frontend handle the rendering.

## ✅ Decision
I chose **Markdown-Native Output**. 

In the `SYNTHESIZER_INSTRUCTION` (inside `instructions.py`), the agent is explicitly instructed to adapt its formatting based on the user's intent. If the user asks for a report, it must output a structured document with specific Markdown headers (`# Executive Summary`, `## Risks`, etc.).

The React dashboard receives this raw Markdown string and renders it using `react-markdown` with Tailwind Typography (`prose`). If the user wants a PDF, they simply use the browser's native "Print to PDF" functionality, which utilizes a specialized CSS `@media print` stylesheet to remove the dashboard navigation and format the report perfectly for an 8.5x11 page.

## 📈 Consequences
* **Positive:** Zero backend overhead. The FastAPI server just returns a string.
* **Positive:** Styling is handled entirely in CSS/Tailwind, making it incredibly easy to tweak the look of the reports without touching Python code.
* **Positive:** Markdown is the native language of LLMs, so the Synthesizer agent rarely makes formatting errors.
* **Negative:** Relies on the user's browser for PDF generation, which means slight variations in margins or fonts depending on whether they use Chrome, Safari, or Edge.

---
⬅️ **Previous:** [ADR 013: Parquet Partitioning](013_parquet_partitioning.md) | **Next:** [ADR 015: Agent Workflow UI](015_agent_workflow_ui.md) ➡️

### 📚 Further Reading
* [08 - Multi-Agent System](../08_Multi_Agent_System.md)
