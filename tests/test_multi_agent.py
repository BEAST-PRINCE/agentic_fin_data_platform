"""Tests for multi-agent module structure (no LLM/MCP required)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_instructions_contain_state_placeholders():
    from src.serving.agent.multi_agent.instructions import (
        RESEARCH_INSTRUCTION,
        SUMMARIZER_INSTRUCTION,
        ANALYST_INSTRUCTION,
        SYNTHESIZER_INSTRUCTION,
    )

    assert "{plan}" in RESEARCH_INSTRUCTION
    assert "{evidence}" in SUMMARIZER_INSTRUCTION
    assert "{summary_package}" in ANALYST_INSTRUCTION
    assert "{analysis_package}" in SYNTHESIZER_INSTRUCTION


def test_conversation_memory():
    from src.serving.agent.multi_agent.memory import ConversationMemory

    mem = ConversationMemory(max_turns=2)
    mem.add_turn("q1", "a1")
    mem.add_turn("q2", "a2")
    mem.add_turn("q3", "a3")
    assert len(mem.turns) == 2
    assert "q2" in mem.format_for_planner()


def test_resolve_model_name_local():
    from src.serving.agent.common import resolve_model_name
    from src.common import config

    original = config.LLM_MODE
    try:
        config.LLM_MODE = "local"
        name = resolve_model_name("qwen2.5:7b")
        assert name.startswith("ollama/")
    finally:
        config.LLM_MODE = original
