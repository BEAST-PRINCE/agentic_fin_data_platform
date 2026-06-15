import os
import sys
from mcp.client.stdio import StdioServerParameters
from google.adk.tools.mcp_tool.mcp_toolset import StdioConnectionParams
from google.adk import Agent, Runner
from google.adk.tools import McpToolset
from google.adk.sessions import InMemorySessionService

from src.common import config
from src.common.logger import get_logger

logger = get_logger(__name__)

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
mcp_server_script = os.path.join(project_root, "src", "serving", "mcp", "server.py")

SYSTEM_INSTRUCTION = (
    "You are the Datalake Intelligence Agent. Your sole purpose is to provide factual "
    "information derived exclusively from the connected Datalake system.\n\n"
    "### AVAILABLE TOOLS (use ONLY these exact names, no others):\n"
    "- `retrieve_articles(keyword, category, limit)` — Semantic search across ingested financial news articles.\n"
    "- `get_daily_trends(date)` — Get aggregated daily market trends and entity data.\n"
    "- `get_article_by_id(article_id)` — Fetch one specific article's full content by its ID.\n"
    "- `get_top_entities(limit)` — Get the most frequently mentioned entities in the datalake.\n\n"
    "### CORE DIRECTIVES:\n"
    "1. ALWAYS USE TOOLS: You must use the provided MCP tools to search the datalake.\n"
    "2. CITE YOUR SOURCES: Mention the source domain, publish date, and the article title.\n"
    "3. SYNTHESIZE: Synthesize the retrieved context clearly. Avoid hallucinating details.\n"
)

class AgentManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        logger.info("Initializing AgentManager singleton...")
        server_params = StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[mcp_server_script]
            ),
            timeout=150
        )
        self.mcp_toolset = McpToolset(connection_params=server_params)
        
        model_name = config.AGENT_MODEL
        if config.LLM_MODE.lower() == "local" and not model_name.startswith("ollama/"):
            model_name = f"ollama/{model_name}"

        self.agent = Agent(
            name="SoloResearcher",
            model=model_name,
            tools=[self.mcp_toolset],
            instruction=SYSTEM_INSTRUCTION
        )
        
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=self.agent,
            app_name="DatalakeApp",
            session_service=self.session_service
        )
        self._initialized = True

    async def initialize_session(self):
        try:
            await self.session_service.create_session(
                app_name="DatalakeApp",
                user_id="default_user",
                session_id="session_1"
            )
            logger.info("Agent session initialized successfully.")
        except Exception:
            pass

    async def chat(self, message: str) -> str:
        try:
            response = await self.runner.run_async(message, user_id="default_user", session_id="session_1")
            return response.content
        except Exception as e:
            logger.error(f"Agent chat failed: {e}")
            return f"Error communicating with agent: {str(e)}"

agent_manager = AgentManager()
