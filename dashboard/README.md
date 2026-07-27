# Dashboard (`dashboard/`)

## 🖥️ Why does this folder exist?

This is the face of the Agentic Datalake. Having an incredibly powerful multi-agent AI pipeline and a blazing-fast Lakehouse is great, but without a good user interface, it's just text flashing on a terminal. I built this React dashboard to provide a beautiful, interactive window into the system. It's designed to make interrogating complex financial data feel as easy as chatting with a colleague.

## 🎨 Responsibilities & Internal Structure

This folder is a standard React application. 

Key responsibilities include:
* **The Chat Interface:** The primary way users interact with the agents. It handles streaming responses and markdown rendering.
* **Agent Workflow Viewer:** An interactive accordion UI that exposes the "inner monologue" of the multi-agent system. Instead of just seeing the final answer, users can click in and see exactly what the Planner, Researcher, and Analyst did to arrive at that conclusion.
* **Data Visualization:** Rendering charts and graphs based on structured data returned by DuckDB through the API.
* **System Health:** Displaying top-level metrics on Lakehouse data volume and pipeline status.

## 🔄 Data Flow

`User Input` ➔ `React State` ➔ `FastAPI (src/serving/)` ➔ *(Agents do their thing)* ➔ `FastAPI Response` ➔ `React Component Renders`

## 🔌 Dependencies & Extension Points

* **Dependencies:** Built with React (usually via Vite or Next.js), using modern styling (Tailwind CSS or styled-components). It relies heavily on the FastAPI endpoints running in the backend.
* **Extension Points:** 
  * Want to add a new chart for stock volatility? Create a new component in the `components/` subfolder, wire it up to a new API endpoint, and drop it onto the dashboard layout.
  * Integrating PDF exports will likely require a new "Export" component here that triggers the backend PDF generation service.

## 🐛 Debugging Tips

* **CORS Errors:** If the dashboard suddenly refuses to talk to the backend, open the browser console. If you see a CORS (Cross-Origin Resource Sharing) error, ensure the FastAPI backend is configured to accept requests from the exact port the dashboard is running on (usually `http://localhost:3000` or `5173`).
* **Blank Screen / React Crash:** If the UI breaks completely when an agent responds, check the Markdown rendering component. Agents sometimes hallucinate weird markdown (like unclosed code blocks or nested tables) that can break strict React renderers.
