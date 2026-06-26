"""Shared helpers for solo and multi-agent runners."""

import os
import sys

from mcp.client.stdio import StdioServerParameters
from google.adk.tools.mcp_tool.mcp_toolset import StdioConnectionParams

from src.common import config

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
MCP_SERVER_SCRIPT = os.path.join(PROJECT_ROOT, "src", "serving", "mcp", "server.py")


def resolve_model_name(model: str | None = None) -> str:
    """Normalize model id for LiteLLM / Ollama."""
    name = model or config.AGENT_MODEL
    if config.LLM_MODE.lower() == "local" and not name.startswith("ollama/"):
        name = f"ollama/{name}"
    return name


def create_mcp_toolset(timeout: int = 150):
    """Create MCP toolset connected to the datalake MCP server."""
    from google.adk.tools import McpToolset

    server_params = StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[MCP_SERVER_SCRIPT],
        ),
        timeout=timeout,
    )
    return McpToolset(connection_params=server_params)
