import os
import sys
import asyncio
from mcp.client.stdio import StdioServerParameters
from google.adk.tools.mcp_tool.mcp_toolset import StdioConnectionParams
from google.genai import types as genai_types

try:
    from google.adk import Agent, Runner
    from google.adk.tools import McpToolset
    from google.adk.sessions import InMemorySessionService
except ImportError as e:
    print(f"WARNING: Google ADK not found or import failed: {e}")
    sys.exit(1)

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from src.common import config
mcp_server_script = os.path.join(project_root, "src", "serving", "mcp", "server.py")

SYSTEM_INSTRUCTION = (
    "You are the Datalake Intelligence Agent. Your sole purpose is to provide factual "
    "information derived exclusively from the connected Datalake system.\n\n"

    "### AVAILABLE TOOLS (use ONLY these exact names, no others):\n"
    "- `retrieve_articles(keyword, category, limit)` — Semantic search across ingested financial news articles.\n"
    "  Use this for ANY question about articles, news, topics, or summaries.\n"
    "- `get_daily_trends(date)` — Get aggregated daily market trends and entity data.\n"
    "  Use this for questions about trends, top entities, sentiment on a specific date.\n"
    "- `get_article_by_id(article_id)` — Fetch one specific article's full content by its ID.\n"
    "- `get_top_entities(limit)` — Get the most frequently mentioned entities in the datalake.\n\n"

    "### CORE DIRECTIVES:\n"
    "1. ALWAYS USE TOOLS: You must use the provided MCP tools to search the datalake (`retrieve_articles`), fetch trends (`get_daily_trends`), or look up specific articles before answering. Never rely solely on your base knowledge.\n"
    "2. CITE YOUR SOURCES: When providing an answer based on tool results, mention the source domain, publish date, and the article title.\n"
    "3. SYNTHESIZE: Synthesize the retrieved context clearly. Avoid hallucinating details that are not present in the tool outputs. Do not just dump raw JSON.\n\n"
    
    "### STRICT DIRECTIVES:\n"
    "1. NO FABRICATION: Do not provide any information from your internal training data. Every fact, date, name, and trend must be derived directly from the results of the MCP tools provided.\n"
    "2. TOOL-FIRST REASONING: Before answering any query, you MUST use the appropriate tool (`retrieve_articles`, `get_daily_trends`, etc.). If the tools do not provide an answer, state: 'The requested information is not available in the datalake.'\n"
    "3. STRICTOR THAN TRUTH: Even if you 'know' something is true based on your general knowledge, if it is not in the tool results, you must NOT include it.\n"
    "4. SOURCE CITATION: Always cite the source_domain and publish_date for every claim.\n\n"
    
    "### CONSTRAINTS:\n"
    "- If a tool returns no results, clearly state that no relevant information was found in the datalake.\n"
    "- Do not expose raw JSON output to the user. Always format your responses into clean, readable markdown with bullet points where appropriate.\n"
    "- Keep your answers focused on the user's query. Do not add unnecessary filler text.\n"
    "- If results are empty, admit it. Do not guess.\n"
)

async def run_solo_agent():
    print(f"Starting Solo Researcher Agent ({config.AGENT_MODEL}) via Google ADK + MCP...")

    server_params = StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[mcp_server_script]
        ),
        timeout=150  # seconds — give ollama enough time to respond
    )

    # McpToolset does not support async context manager — use try/finally with close()
    mcp_toolset = McpToolset(connection_params=server_params)
    print("Configured MCP Toolset (timeout=150s).")

    model_name = config.AGENT_MODEL
    
    if config.LLM_MODE.lower() == "local":
        # Ensure the model string has the ollama/ prefix required by LiteLLM for local models
        if not model_name.startswith("ollama/"):
            model_name = f"ollama/{model_name}"

    try:
        agent = Agent(
            name="SoloResearcher",
            model=model_name,  # Fetched from .env via config.py
            tools=[mcp_toolset],
            instruction=SYSTEM_INSTRUCTION
        )

        # Runner is the orchestration engine in ADK
        session_service = InMemorySessionService()
        runner = Runner(
            agent=agent,
            app_name="DatalakeApp",
            session_service=session_service
        )

        # Pre-create the session so it exists when run_async is called
        await session_service.create_session(
            app_name="DatalakeApp",
            user_id="default_user",
            session_id="session_1"
        )

        print("\nSolo Researcher is ready! Type 'exit' to quit.")
        while True:
            user_input = input("\nUser: ")
            if user_input.strip().lower() in ['exit', 'quit', 'bye', 'q']:
                print("Goodbye!")
                break

            try:
                # ADK requires a typed Content object, not a plain string
                message = genai_types.Content(
                    role="user",
                    parts=[genai_types.Part(text=user_input)]
                )

                print("\nAgent: ", end="", flush=True)
                async for event in runner.run_async(
                    user_id="default_user",
                    session_id="session_1",
                    new_message=message
                ):
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    print(part.text, end="", flush=True)
                print()  # Newline after response
            except Exception as e:
                print(f"\nAgent Error: {e}")

    finally:
        # close() terminates the MCP stdio subprocess cleanly — this is what fixes the hang
        close_result = mcp_toolset.close()
        if asyncio.iscoroutine(close_result):
            await close_result


def _suppress_cancel_scope_errors(loop, context):
    """Suppress the known anyio/MCP cancel scope teardown error on Windows.
    This is a bug in google-adk's MCP session cleanup — not our code.
    """
    exc = context.get("exception")
    if isinstance(exc, RuntimeError) and "cancel scope" in str(exc):
        return  # Silently swallow the known teardown noise
    loop.default_exception_handler(context)


if __name__ == "__main__":
    # IMPORTANT: Use SelectorEventLoop on Windows — anyio cancel scopes are
    # incompatible with ProactorEventLoop and cause a crash on clean exit.
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    loop.set_exception_handler(_suppress_cancel_scope_errors)
    try:
        loop.run_until_complete(run_solo_agent())
    finally:
        loop.close()
