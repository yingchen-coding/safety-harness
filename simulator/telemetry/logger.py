"""
Telemetry logging for agent execution.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Any


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Single log entry."""
    timestamp: str
    level: str
    event: str
    details: dict = field(default_factory=dict)
    step: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)


class TelemetryLogger:
    """
    Structured logging for agent execution.

    Captures:
    - Action executions
    - Safeguard decisions
    - Escalation events
    - Tool results
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.entries: list[LogEntry] = []
        self.current_step = 0

    def log(
        self,
        level: LogLevel,
        event: str,
        details: Optional[dict] = None,
        step: Optional[int] = None
    ) -> None:
        """Log an event."""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            event=event,
            details=details or {},
            step=step or self.current_step
        )
        self.entries.append(entry)

    def debug(self, event: str, details: Optional[dict] = None) -> None:
        self.log(LogLevel.DEBUG, event, details)

    def info(self, event: str, details: Optional[dict] = None) -> None:
        self.log(LogLevel.INFO, event, details)

    def warning(self, event: str, details: Optional[dict] = None) -> None:
        self.log(LogLevel.WARNING, event, details)

    def error(self, event: str, details: Optional[dict] = None) -> None:
        self.log(LogLevel.ERROR, event, details)

    def critical(self, event: str, details: Optional[dict] = None) -> None:
        self.log(LogLevel.CRITICAL, event, details)

    def log_action(self, action: Any, step: int) -> None:
        """Log action execution."""
        self.current_step = step
        self.info("action_executed", {
            "tool": action.tool,
            "description": action.description,
            "risk_level": action.risk_level
        })

    def log_safeguard(self, safeguard_name: str, result: dict) -> None:
        """Log safeguard check result."""
        level = LogLevel.WARNING if result.get("blocked") else LogLevel.INFO
        self.log(level, f"safeguard_{safeguard_name}", result)

    def log_escalation(self, decision: Any) -> None:
        """Log escalation decision."""
        level_map = {
            "none": LogLevel.DEBUG,
            "clarify": LogLevel.INFO,
            "warn": LogLevel.WARNING,
            "soft_stop": LogLevel.WARNING,
            "hard_stop": LogLevel.ERROR,
            "human_review": LogLevel.CRITICAL
        }
        level = level_map.get(decision.level.value, LogLevel.INFO)
        self.log(level, "escalation_decision", {
            "level": decision.level.value,
            "reason": decision.reason,
            "action": decision.action
        })

    def log_tool_result(self, tool: str, status: str, risk_score: float) -> None:
        """Log tool execution result."""
        level = LogLevel.WARNING if risk_score > 0.5 else LogLevel.INFO
        self.log(level, "tool_result", {
            "tool": tool,
            "status": status,
            "risk_score": risk_score
        })

    def get_entries(self, level: Optional[LogLevel] = None) -> list[LogEntry]:
        """Get log entries, optionally filtered by level."""
        if level is None:
            return self.entries
        return [e for e in self.entries if e.level == level.value]

    def get_warnings_and_above(self) -> list[LogEntry]:
        """Get all warning, error, and critical entries."""
        levels = {LogLevel.WARNING.value, LogLevel.ERROR.value, LogLevel.CRITICAL.value}
        return [e for e in self.entries if e.level in levels]

    def to_json(self) -> str:
        """Export log as JSON."""
        return json.dumps({
            "session_id": self.session_id,
            "entries": [e.to_dict() for e in self.entries]
        }, indent=2)

    def summary(self) -> dict:
        """Get log summary statistics."""
        level_counts = {}
        for entry in self.entries:
            level_counts[entry.level] = level_counts.get(entry.level, 0) + 1

        return {
            "session_id": self.session_id,
            "total_entries": len(self.entries),
            "by_level": level_counts,
            "steps_logged": self.current_step
        }
