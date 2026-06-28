"""
Agent Memory - Stores conversation history and state.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class MemoryEntry:
    """A single entry in agent memory."""
    timestamp: datetime
    entry_type: str  # "user", "agent", "tool", "system"
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentState:
    """Current state of the agent."""
    current_goal: Optional[str] = None
    step_count: int = 0
    total_drift: float = 0.0
    violations: int = 0
    escalations: int = 0
    is_blocked: bool = False
    block_reason: Optional[str] = None


class Memory:
    """
    Manages agent memory and state.

    Provides:
    - Conversation history
    - State tracking
    - Context retrieval for planning
    """

    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self.entries: list[MemoryEntry] = []
        self.state = AgentState()

    def add(
        self,
        entry_type: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> None:
        """Add entry to memory."""
        entry = MemoryEntry(
            timestamp=datetime.now(),
            entry_type=entry_type,
            content=content,
            metadata=metadata or {}
        )
        self.entries.append(entry)

        # Trim if exceeds max
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def add_user_message(self, content: str) -> None:
        """Add user message to memory."""
        self.add("user", content)

    def add_agent_response(self, content: str) -> None:
        """Add agent response to memory."""
        self.add("agent", content)

    def add_tool_result(self, tool: str, result: str) -> None:
        """Add tool execution result to memory."""
        self.add("tool", result, {"tool": tool})

    def add_system_event(self, event: str, details: Optional[dict] = None) -> None:
        """Add system event to memory."""
        self.add("system", event, details)

    def get_recent(self, n: int = 10) -> list[MemoryEntry]:
        """Get n most recent entries."""
        return self.entries[-n:]

    def get_conversation_context(self) -> str:
        """Get conversation history as context string."""
        recent = self.get_recent(10)
        lines = []
        for entry in recent:
            if entry.entry_type == "user":
                lines.append(f"User: {entry.content}")
            elif entry.entry_type == "agent":
                lines.append(f"Agent: {entry.content}")
        return "\n".join(lines)

    def update_state(
        self,
        drift_delta: float = 0.0,
        violation: bool = False,
        escalation: bool = False
    ) -> None:
        """Update agent state."""
        self.state.step_count += 1
        self.state.total_drift += drift_delta
        if violation:
            self.state.violations += 1
        if escalation:
            self.state.escalations += 1

    def set_goal(self, goal: str) -> None:
        """Set current goal."""
        self.state.current_goal = goal

    def block(self, reason: str) -> None:
        """Block agent with reason."""
        self.state.is_blocked = True
        self.state.block_reason = reason

    def reset(self) -> None:
        """Reset memory and state."""
        self.entries.clear()
        self.state = AgentState()
