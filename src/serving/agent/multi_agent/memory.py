"""Lightweight conversation memory for multi-agent sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ConversationMemory:
    """Stores recent user/assistant turns for context injection."""

    max_turns: int = 8
    turns: List[dict] = field(default_factory=list)

    def add_turn(self, user: str, assistant: str) -> None:
        self.turns.append({"user": user, "assistant": assistant})
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns :]

    def format_for_planner(self) -> str:
        if not self.turns:
            return ""
        lines = ["### Recent conversation context"]
        for i, turn in enumerate(self.turns[-3:], 1):
            lines.append(f"Turn {i} User: {turn['user']}")
            lines.append(f"Turn {i} Assistant: {turn['assistant'][:500]}...")
        return "\n".join(lines)

    def clear(self) -> None:
        self.turns.clear()
