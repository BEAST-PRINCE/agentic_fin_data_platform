"""
Interactive CLI for the multi-agent Financial Intelligence pipeline.

Run independently from the solo agent:
  python -m src.serving.agent.multi_agent.runner
"""

from __future__ import annotations

import asyncio
import sys

from google.genai import types as genai_types

try:
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
except ImportError as e:
    print(f"WARNING: Google ADK not found or import failed: {e}")
    sys.exit(1)

from src.common import config
from src.common.logger import get_logger
from src.serving.agent.common import create_mcp_toolset, resolve_model_name
from src.serving.agent.multi_agent.memory import ConversationMemory
from src.serving.agent.multi_agent.pipeline import build_multi_agent_pipeline

logger = get_logger(__name__)

APP_NAME = "MultiAgentFinancialIntelligence"
USER_ID = "multi_agent_user"
SESSION_ID = "multi_agent_session_1"


async def run_multi_agent_cli():
    model_name = resolve_model_name()
    print(
        f"Starting Multi-Agent Financial Intelligence System ({model_name}) "
        f"via Google ADK + MCP..."
    )
    print("Agents: Planner → Research → Summarizer → Analyst → Synthesizer")
    print("(Independent from solo_agent.py — type 'exit' to quit)\n")

    mcp_toolset = create_mcp_toolset(timeout=150)
    memory = ConversationMemory()

    try:
        root_agent = build_multi_agent_pipeline(mcp_toolset, model=model_name)
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
        )

        while True:
            user_input = input("\nUser: ").strip()
            if user_input.lower() in ("exit", "quit", "bye", "q"):
                print("Goodbye!")
                break
            if not user_input:
                continue

            context_block = memory.format_for_planner()
            if context_block:
                message_text = f"{context_block}\n\nCurrent question:\n{user_input}"
            else:
                message_text = user_input

            message = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=message_text)],
            )

            print("\nPipeline running (plan → research → summarize → analyze → synthesize)...")
            print("\nAgent Team: ", end="", flush=True)

            final_text = ""
            try:
                async for event in runner.run_async(
                    user_id=USER_ID,
                    session_id=SESSION_ID,
                    new_message=message,
                ):
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    final_text += part.text
                print(final_text)
                memory.add_turn(user_input, final_text)
            except Exception as e:
                logger.error(f"Multi-agent pipeline error: {e}")
                print(f"\nPipeline Error: {e}")

    finally:
        close_result = mcp_toolset.close()
        if asyncio.iscoroutine(close_result):
            await close_result


def _suppress_cancel_scope_errors(loop, context):
    exc = context.get("exception")
    if isinstance(exc, RuntimeError) and "cancel scope" in str(exc):
        return
    loop.default_exception_handler(context)


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    loop.set_exception_handler(_suppress_cancel_scope_errors)
    try:
        loop.run_until_complete(run_multi_agent_cli())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
