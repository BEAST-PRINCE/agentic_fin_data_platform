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
from src.common import config
from src.common.logger import get_logger

logger = get_logger(__name__)

# ─── Global singletons for the vector search pipeline ───
# Lazy-initialized on first use to avoid startup cost if tools aren't called.
_embedder = None
_qdrant = None

def _get_embedder():
    """Lazily initialize the sentence-transformer embedder (once per process)."""
    global _embedder
    if _embedder is None:
        from src.processing.embeddings import EmbedderFactory
        _embedder = EmbedderFactory.get_embedder(engine=config.VECTOR_EMBEDDING_ENGINE, device='cuda')
    return _embedder

def _get_qdrant():
    """Lazily initialize the Qdrant client (once per process)."""
    global _qdrant
    if _qdrant is None:
        from qdrant_client import QdrantClient
        _qdrant = QdrantClient(url="http://localhost:6333")
    return _qdrant

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
            limit = arguments.get("limit", 10)
            
            try:
                embedder = _get_embedder()
                qdrant = _get_qdrant()
                
                # Embed the query
                query_vector = embedder.embed([keyword])[0]
                
                # Search Qdrant
                search_results = qdrant.query_points(
                    collection_name="articles",
                    query=query_vector,
                    limit=limit
                ).points
                
                # Format results
                formatted_results = []
                for hit in search_results:
                    formatted_results.append({
                        "article_id": hit.id,
                        "score": hit.score,
                        "title": hit.payload.get("title"),
                        "source_domain": hit.payload.get("source_domain"),
                        "publish_timestamp": hit.payload.get("publish_timestamp"),
                        "extracted_keywords": hit.payload.get("extracted_keywords", [])
                    })
                    
                return [types.TextContent(type="text", text=str(formatted_results) if formatted_results else "No articles found.")]
            except Exception as e:
                logger.error(f"Semantic search failed: {e}")
                return [types.TextContent(type="text", text=f"Semantic Search failed: {e}")]

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
