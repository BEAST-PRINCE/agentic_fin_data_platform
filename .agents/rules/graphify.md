---
trigger: always_on
description: Consult the graphify knowledge graph at graphify_project/graphify_project.json for codebase and architecture questions.
---

## graphify

This project has a graphify knowledge graph at graphify_project/graphify_project.json.

Rules:
- For codebase or architecture questions, when `graphify_project/graphify_project.json` exists, first run `graphify_project\tool\venv\Scripts\python -m graphify query "<question>" --graph graphify_project/graphify_project.json` (CLI) or `query_graph` (MCP). Use `graphify path "<A>" "<B>" --graph graphify_project/graphify_project.json` / `shortest_path` for relationships and `graphify explain "<concept>" --graph graphify_project/graphify_project.json` / `get_node` for focused concepts. These return a scoped subgraph, usually much smaller than `GRAPH_REPORT.md` or raw grep output.
- If graphify_project/wiki/index.md exists, navigate it instead of reading raw files
- Read graphify_project/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context
- After modifying code files in this session, run `graphify_project\tool\venv\Scripts\python -m graphify update . --graph graphify_project/graphify_project.json` to keep the graph current (AST-only, no API cost)
