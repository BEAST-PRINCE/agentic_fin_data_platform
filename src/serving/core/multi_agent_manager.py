"""
API-facing manager for the multi-agent pipeline (separate from solo AgentManager).
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from google.genai import types as genai_types

try:
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
except ImportError:
    Runner = None
    InMemorySessionService = None

from src.common.logger import get_logger
from src.serving.agent.common import create_mcp_toolset
from src.serving.agent.multi_agent.memory import ConversationMemory
from src.serving.agent.multi_agent.pipeline import build_multi_agent_pipeline

logger = get_logger(__name__)

APP_NAME = "MultiAgentFinancialIntelligence"
USER_ID = "api_multi_agent_user"

AGENT_NAMES_MAP = {
    "PlannerAgent": 0,
    "ResearchAgent": 1,
    "SummarizationAgent": 2,
    "AnalystAgent": 3,
    "SynthesizerAgent": 4,
}


class MultiAgentManager:
    """Lazy-initialized multi-agent pipeline for HTTP/API use."""

    def __init__(self):
        self._initialized = False
        self.mcp_toolset = None
        self.runner = None
        self.session_service = None
        self.memory = ConversationMemory()

    async def initialize(self) -> None:
        if self._initialized:
            return
        if Runner is None:
            raise RuntimeError("Google ADK is not installed.")

        logger.info("Initializing MultiAgentManager...")
        self.mcp_toolset = create_mcp_toolset(timeout=150)
        root_agent = build_multi_agent_pipeline(self.mcp_toolset)
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=self.session_service,
        )
        self._initialized = True
        logger.info("MultiAgentManager ready.")

    async def chat(self, message: str) -> dict[str, Any]:
        await self.initialize()

        # Each query gets a clean, isolated session to avoid state accumulation issues
        session_id = f"multi_session_{uuid.uuid4().hex}"
        await self.session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )

        logger.info(f"[MultiAgent Pipeline] Starting pipeline execution for query: '{message[:80]}...' | Session: {session_id}")

        context_block = self.memory.format_for_planner()
        if context_block:
            message_text = f"{context_block}\n\nCurrent question:\n{message}"
        else:
            message_text = message

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=message_text)],
        )

        workflow_steps = []
        final_text = ""
        fallback_agent_idx = 0
        pipeline_start_time = time.time()
        step_start_time = pipeline_start_time

        async for event in self.runner.run_async(
            user_id=USER_ID,
            session_id=session_id,
            new_message=content,
        ):
            author = (
                getattr(event, "author", None)
                or getattr(event, "agent_name", None)
                or getattr(event, "source", None)
            )

            # Log tool calls if present in parts
            if hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
                for part in event.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        logger.info(f"[MultiAgent Tool Call] Agent '{author}' calling tool: {part.function_call.name}")
                    elif hasattr(part, "function_response") and part.function_response:
                        logger.info(f"[MultiAgent Tool Response] Received output for tool: {part.function_response.name}")

            if event.is_final_response():
                if event.content and event.content.parts:
                    step_text = ""
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            step_text += part.text

                    if step_text.strip():
                        now = time.time()
                        exec_time_ms = max(10, int((now - step_start_time) * 1000))
                        step_start_time = now

                        if author in AGENT_NAMES_MAP:
                            agent_idx = AGENT_NAMES_MAP[author]
                        else:
                            agent_idx = fallback_agent_idx
                            fallback_agent_idx += 1

                        # Parse step info
                        step_info = self._parse_agent_step(agent_idx, step_text, exec_time_ms)
                        workflow_steps.append(step_info)
                        logger.info(f"[MultiAgent Step {len(workflow_steps)}/5] Agent '{step_info['agent']}' completed in {exec_time_ms} ms | {step_info['summary']}")

                        if author == "SynthesizerAgent" or agent_idx == 4:
                            final_text = step_text

        total_pipeline_ms = int((time.time() - pipeline_start_time) * 1000)
        if not final_text and workflow_steps:
            final_text = workflow_steps[-1].get("details", "")
            if not isinstance(final_text, str):
                final_text = str(final_text)

        reply_output = final_text or "No response generated by the multi-agent pipeline."
        self.memory.add_turn(message, reply_output)

        logger.info(f"[MultiAgent Pipeline Completed] Finished in {total_pipeline_ms} ms across {len(workflow_steps)} steps | Output length: {len(reply_output)} chars")

        return {
            "reply": reply_output,
            "workflow_steps": workflow_steps,
        }

    def _parse_agent_step(self, agent_idx: int, text: str, execution_time_ms: int) -> dict[str, Any]:
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        data = None
        try:
            import json
            data = json.loads(clean_text)
        except Exception:
            pass

        if agent_idx == 0:
            name = "Planner Agent"
            if isinstance(data, dict):
                intent = data.get("intent", "market_analysis")
                focus = data.get("focus", "")
                summary = f"Intent: {intent}" + (f" • {focus}" if focus else "")
            else:
                summary = "Generated execution plan."
        elif agent_idx == 1:
            name = "Research Agent"
            if isinstance(data, dict):
                articles = len(data.get("articles", []))
                trends = len(data.get("trends", []))
                summary = f"Retrieved {articles} articles & {trends} trend records."
            else:
                summary = "Retrieved market evidence from datalake."
        elif agent_idx == 2:
            name = "Summarization Agent"
            if isinstance(data, dict):
                themes = len(data.get("themes", []))
                clusters = len(data.get("topic_clusters", []))
                summary = f"Extracted {themes} key themes across {clusters} topic clusters."
            else:
                summary = "Compressed evidence into themes."
        elif agent_idx == 3:
            name = "Analyst Agent"
            if isinstance(data, dict):
                insights = len(data.get("insights", []))
                confidence = str(data.get("confidence", "medium")).upper()
                summary = f"Generated {insights} insights (Confidence: {confidence})."
            else:
                summary = "Analyzed market impact and risks."
        else:
            name = "Synthesizer Agent"
            summary = "Produced final response report."

        return {
            "agent": name,
            "status": "completed",
            "summary": summary,
            "details": data if data is not None else text,
            "execution_time_ms": execution_time_ms,
        }

    async def shutdown(self) -> None:
        if self.mcp_toolset:
            close_result = self.mcp_toolset.close()
            if asyncio.iscoroutine(close_result):
                await close_result
        self._initialized = False


multi_agent_manager = MultiAgentManager()
