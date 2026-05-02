import os
import sys
import asyncio

# Google ADK imports
try:
    from adk import Agent, Model
    from adk.mcp import MCPClient
except ImportError:
    # Fallback to standard MCP + Ollama if adk isn't fully installed or structure differs
    print("WARNING: ADK module 'adk' not found. Ensure google-adk is correctly installed.")
    sys.exit(1)

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
mcp_server_script = os.path.join(project_root, "src", "serving", "mcp", "server.py")

async def run_solo_agent():
    print("Starting Solo Researcher Agent (gemma:2b) via Google ADK + MCP...")
    
    # Connect to the local MCP Server using ADK's native MCP client adapter
    try:
        mcp_client = MCPClient.from_stdio(
            command=sys.executable,  # Use current python executable
            args=[mcp_server_script]
        )
        await mcp_client.connect()
        print("Connected to MCP Server natively via ADK.")
    except Exception as e:
        print(f"Failed to connect to MCP Server: {e}")
        return
    
    # Initialize the Agent with Ollama gemma:2b
    agent = Agent(
        model=Model(provider="ollama", name="gemma:2b"),
        tools=mcp_client.get_tools(),
        system_prompt=(
            "You are the Datalake Intelligence Agent. Your sole purpose is to provide factual information derived exclusively from the connected Datalake system.\n\n"
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
            "- Keep your answers focused on the user's query. Do not add unnecessary filler text."
            "- If results are empty, admit it. Do not guess.\n"
        )
    )
    
    print("\nSolo Researcher is ready! Type 'exit' to quit.")
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        try:
            # The ADK agent autonomously handles the tool orchestration, looping, and reasoning
            response = await agent.run(user_input)
            print(f"\nAgent: {response.text}")
        except Exception as e:
            print(f"\nAgent Error: {e}")

if __name__ == "__main__":
    # Ensure event loop handles subprocesses properly on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_solo_agent())
