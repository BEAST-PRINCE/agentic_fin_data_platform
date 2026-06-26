import os
import sys

# CRITICAL FIX: OS-level redirect of STDOUT to STDERR!
# Some C-level libraries (PyTorch, Rust tokenizers, etc) bypass Python's sys.stdout
# and write directly to file descriptor 1 (STDOUT), which corrupts the MCP JSON-RPC pipe.
# 1. Duplicate the original STDOUT (fd 1) so we can still use it for MCP
original_stdout_fd = os.dup(1)
true_stdout = os.fdopen(original_stdout_fd, 'w', encoding='utf-8')

# 2. Redirect fd 1 to fd 2 (STDERR) at the OS level!
os.dup2(2, 1)

# 3. Also redirect Python's sys.stdout
sys.stdout = sys.stderr

import asyncio
from typing import Any, List, Optional
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
import anyio

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.storage.db_client import db
from src.common import config
from src.common.logger import get_logger
from src.serving.core import retrieval

logger = get_logger(__name__)

# Initialize the MCP Server
server = Server("agentic_datalake_mcp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List the available tools that an AI Agent can call.
    """
    return [
        types.Tool(
            name="get_article_by_id",
            description="Fetch a specific article's full content and metadata using its unique article_id.",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "string",
                        "description": "The unique UUID or hash of the article."
                    }
                },
                "required": ["article_id"]
            }
        ),
        types.Tool(
            name="retrieve_articles",
            description="Search for articles in the Gold layer containing specific keywords or from a specific category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The keyword to search for in the title or content."
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter (e.g., 'finance', 'technology')."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default 10)."
                    }
                },
                "required": ["keyword"]
            }
        ),
        types.Tool(
            name="get_daily_trends",
            description="Get the aggregate daily trends (total articles) broken down by source and category for a date range.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format."
                    }
                },
                "required": ["start_date", "end_date"]
            }
        ),
        types.Tool(
            name="get_top_entities",
            description="Retrieve the most frequently mentioned entities (keywords) across all articles for a specific date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "publish_date": {
                        "type": "string",
                        "description": "The target date in YYYY-MM-DD format."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of top entities to return (default 10)."
                    }
                },
                "required": ["publish_date"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle the execution of a tool when an agent requests it.
    """
    if not arguments:
        arguments = {}

    try:
        if name == "get_article_by_id":
            article_id = arguments.get("article_id")
            if not article_id:
                raise ValueError("Missing article_id")
            
            result = retrieval.fetch_article_by_id(article_id)
            if not result:
                return [types.TextContent(type="text", text=f"Article not found for ID: {article_id}")]
                
            return [types.TextContent(type="text", text=str(result))]

        elif name == "retrieve_articles":
            keyword = arguments.get("keyword", "")
            limit = arguments.get("limit", 10)
            
            try:
                results = retrieval.semantic_search(keyword, limit)
                return [types.TextContent(type="text", text=str(results) if results else "No articles found.")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Semantic Search failed: {e}")]

        elif name == "get_daily_trends":
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            
            results = retrieval.fetch_daily_trends(start_date, end_date)
            return [types.TextContent(type="text", text=str(results) if results else "No trends found for range.")]

        elif name == "get_top_entities":
            publish_date = arguments.get("publish_date")
            limit = arguments.get("limit", 10)
            
            results = retrieval.fetch_top_entities(publish_date, limit)
            return [types.TextContent(type="text", text=str(results) if results else f"No entities found for {publish_date}")]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        return [types.TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]

async def main():
    """Run the server using stdio transport"""
    logger.info("Starting Agentic Datalake MCP Server...")
    
    # Pre-initialize heavy PyTorch models before starting anyio threads.
    # PyTorch's C++ multi-threading and OpenMP initialization can disrupt
    # the fragile anyio thread workers reading sys.stdin on Windows if 
    # initialized dynamically in the middle of the event loop.
    logger.info("Pre-loading semantic search models...")
    retrieval._get_embedder()
    logger.info("Model pre-loaded.")
    
    # Run the server over standard input/output using the safely preserved true_stdout
    async_stdin = anyio.wrap_file(sys.stdin)
    async_stdout = anyio.wrap_file(true_stdout)
    
    async with mcp.server.stdio.stdio_server(stdin=async_stdin, stdout=async_stdout) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="agentic_datalake_mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
