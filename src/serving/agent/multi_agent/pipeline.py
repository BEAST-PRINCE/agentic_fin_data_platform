"""Build the multi-agent SequentialAgent pipeline."""

from __future__ import annotations

from google.adk import Agent

from src.serving.agent.common import resolve_model_name
from src.serving.agent.multi_agent.instructions import (
    ANALYST_INSTRUCTION,
    PLANNER_INSTRUCTION,
    RESEARCH_INSTRUCTION,
    SUMMARIZER_INSTRUCTION,
    SYNTHESIZER_INSTRUCTION,
)


def _import_sequential_agent():
    try:
        from google.adk.agents.sequential_agent import SequentialAgent

        return SequentialAgent
    except ImportError:
        from google.adk.agents import SequentialAgent

        return SequentialAgent


def build_multi_agent_pipeline(mcp_toolset, model: str | None = None):
    """
    Create the 5-agent pipeline:
    Planner → Research (MCP) → Summarizer → Analyst → Synthesizer
    """
    SequentialAgent = _import_sequential_agent()
    model_name = resolve_model_name(model)

    planner = Agent(
        name="PlannerAgent",
        model=model_name,
        instruction=PLANNER_INSTRUCTION,
        output_key="plan",
    )

    researcher = Agent(
        name="ResearchAgent",
        model=model_name,
        tools=[mcp_toolset],
        instruction=RESEARCH_INSTRUCTION,
        output_key="evidence",
    )

    summarizer = Agent(
        name="SummarizationAgent",
        model=model_name,
        instruction=SUMMARIZER_INSTRUCTION,
        output_key="summary_package",
    )

    analyst = Agent(
        name="AnalystAgent",
        model=model_name,
        instruction=ANALYST_INSTRUCTION,
        output_key="analysis_package",
    )

    synthesizer = Agent(
        name="SynthesizerAgent",
        model=model_name,
        instruction=SYNTHESIZER_INSTRUCTION,
        output_key="final_report",
    )

    pipeline = SequentialAgent(
        name="FinancialIntelligencePipeline",
        sub_agents=[planner, researcher, summarizer, analyst, synthesizer],
        description=(
            "Orchestrates planner, research, summarization, analysis, and synthesis "
            "for financial intelligence queries over the datalake."
        ),
    )
    return pipeline
