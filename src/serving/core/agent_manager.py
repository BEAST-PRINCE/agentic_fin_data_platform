import os
import sys
import time
import uuid
from mcp.client.stdio import StdioServerParameters
from google.adk.tools.mcp_tool.mcp_toolset import StdioConnectionParams
from google.adk import Agent, Runner
from google.adk.tools import McpToolset
from google.adk.sessions import InMemorySessionService
from google.genai import types

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
        # Heavy components are lazily loaded
        pass

    async def initialize_agent(self):
        if self._initialized:
            return
            
        logger.info("Initializing AgentManager heavy components...")
        import os
        env = os.environ.copy()
        env["TQDM_DISABLE"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        
        server_params = StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[mcp_server_script],
                env=env
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
        if not self._initialized:
            logger.info("[SoloAgent] Agent was not initialized on boot. Initializing now...")
            await self.initialize_agent()
            
        start_time = time.time()
        session_id = f"solo_session_{uuid.uuid4().hex}"
        
        try:
            await self.session_service.create_session(
                app_name="DatalakeApp",
                user_id="default_user",
                session_id=session_id
            )
            logger.info(f"[SoloAgent] Processing prompt: '{message[:80]}...' | Session: {session_id}")
            
            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)]
            )
            
            gen = self.runner.run_async(
                user_id="default_user", 
                session_id=session_id,
                new_message=content
            )
            
            full_response = ""
            event_count = 0
            async for event in gen:
                event_count += 1
                author = getattr(event, "author", "SoloResearcher")
                
                # ADK events store text in event.content.parts
                if hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            full_response += part.text
                        elif hasattr(part, "function_call") and part.function_call:
                            logger.info(f"[SoloAgent Step] Tool Call requested by model: {part.function_call.name}")
                        elif hasattr(part, "function_response") and part.function_response:
                            logger.info(f"[SoloAgent Step] Tool Response received for: {part.function_response.name}")

            elapsed_ms = int((time.time() - start_time) * 1000)
            if not full_response:
                logger.warn(f"[SoloAgent Completed] Processed request in {elapsed_ms} ms ({event_count} events) but returned empty text.")
                return "Agent processed the request but returned no text."
                
            logger.info(f"[SoloAgent Completed] Responded in {elapsed_ms} ms ({event_count} events) | Response length: {len(full_response)} chars")
            return full_response
        except Exception as e:
            logger.error(f"[SoloAgent Error] Chat failed: {e}", exc_info=True)
            return f"Error communicating with agent: {str(e)}"

agent_manager = AgentManager()
