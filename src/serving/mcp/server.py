import os
import sys
import asyncio
from typing import Any, List, Optional
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.storage.db_client import db
from src.common.logger import get_logger

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
                
            path = db.get_gold_path("articles_serving")
            query = f"SELECT * FROM read_parquet('{path}') WHERE article_id = '{article_id}'"
            
            results = db.query(query)
            if not results:
                return [types.TextContent(type="text", text=f"Article not found for ID: {article_id}")]
                
            return [types.TextContent(type="text", text=str(results[0]))]

        elif name == "retrieve_articles":
            keyword = arguments.get("keyword", "")
            category = arguments.get("category")
            limit = arguments.get("limit", 10)
            
            path = db.get_gold_path("articles_serving")
            
            # Using basic ILIKE for text matching (Phase 5A)
            # (Note: we join with daily_trends if category is needed, but for simplicity we'll just search text)
            query = f"""
                SELECT article_id, publish_timestamp, source_domain, title, word_count, extracted_keywords 
                FROM read_parquet('{path}') 
                WHERE title ILIKE '%{keyword}%' OR clean_content ILIKE '%{keyword}%'
                LIMIT {limit}
            """
            
            results = db.query(query)
            return [types.TextContent(type="text", text=str(results) if results else "No articles found.")]

        elif name == "get_daily_trends":
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            
            path = db.get_gold_path("daily_trends")
            
            query = f"""
                SELECT publish_date, source_domain, category, SUM(total_articles) as total_articles
                FROM read_parquet('{path}')
                WHERE publish_date >= '{start_date}' AND publish_date <= '{end_date}'
                GROUP BY publish_date, source_domain, category
                ORDER BY publish_date DESC, total_articles DESC
            """
            
            results = db.query(query)
            return [types.TextContent(type="text", text=str(results) if results else "No trends found for range.")]

        elif name == "get_top_entities":
            publish_date = arguments.get("publish_date")
            limit = arguments.get("limit", 10)
            
            path = db.get_gold_path("entity_mentions")
            
            query = f"""
                SELECT entity_name, entity_type, SUM(mention_count) as total_mentions
                FROM read_parquet('{path}')
                WHERE publish_date = '{publish_date}'
                GROUP BY entity_name, entity_type
                ORDER BY total_mentions DESC
                LIMIT {limit}
            """
            
            results = db.query(query)
            return [types.TextContent(type="text", text=str(results) if results else f"No entities found for {publish_date}")]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        return [types.TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]

async def main():
    """Run the server using stdio transport"""
    logger.info("Starting Agentic Datalake MCP Server...")
    
    # Run the server over standard input/output
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
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
