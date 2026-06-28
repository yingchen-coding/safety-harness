"""
Event Schema for Incident Lab Integration
==========================================

This module defines the telemetry event schema for safeguard decisions.
Events are designed to be consumed by agentic-safety-incident-lab for
post-hoc analysis, but this repo does NOT perform incident analysis.

Design Philosophy:
- This repo: record events
- Incident lab: analyze events
- Clear separation of responsibilities
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
import json


@dataclass
class SafeguardEvent:
    """
    A single safeguard decision event.

    This schema is the interface contract between:
    - agentic-safeguards-simulator (producer)
    - agentic-safety-incident-lab (consumer)
    """

    # Identifiers
    run_id: str
    step: int
    timestamp: str

    # Hook information
    hook_point: str  # pre_action, mid_step, post_action
    hook_name: str

    # Decision
    decision: str  # PROCEED, SOFT_STOP, HARD_STOP, HUMAN_REVIEW
    confidence: float
    reason: str

    # Features that informed decision
    features: Dict[str, Any]

    # Performance
    latency_ms: float

    # Context (for replay)
    user_input: Optional[str] = None
    tool_call: Optional[str] = None
    tool_result: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict) -> 'SafeguardEvent':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class RunSummary:
    """
    Summary of all safeguard events in a single run.

    Used for quick filtering before full incident analysis.
    """

    run_id: str
    start_time: str
    end_time: str
    total_steps: int

    # Decision counts
    proceed_count: int
    soft_stop_count: int
    hard_stop_count: int
    human_review_count: int

    # Aggregate features
    max_drift: float
    total_violations: int
    avg_latency_ms: float

    # Verdict
    final_decision: str
    escalation_triggered: bool

    def to_dict(self) -> Dict:
        return asdict(self)


class EventEmitter:
    """
    Emits safeguard events to telemetry storage.

    This class handles event formatting and storage.
    Analysis of events is out of scope (belongs in incident lab).
    """

    def __init__(self, output_path: str = "telemetry/events.jsonl"):
        self.output_path = output_path
        self.events: List[SafeguardEvent] = []

    def emit(
        self,
        run_id: str,
        step: int,
        hook_point: str,
        hook_name: str,
        decision: str,
        confidence: float,
        reason: str,
        features: Dict[str, Any],
        latency_ms: float,
        user_input: Optional[str] = None,
        tool_call: Optional[str] = None,
        tool_result: Optional[str] = None
    ) -> SafeguardEvent:
        """Emit a safeguard event."""
        event = SafeguardEvent(
            run_id=run_id,
            step=step,
            timestamp=datetime.utcnow().isoformat() + "Z",
            hook_point=hook_point,
            hook_name=hook_name,
            decision=decision,
            confidence=confidence,
            reason=reason,
            features=features,
            latency_ms=latency_ms,
            user_input=user_input,
            tool_call=tool_call,
            tool_result=tool_result
        )

        self.events.append(event)
        self._write_event(event)
        return event

    def _write_event(self, event: SafeguardEvent) -> None:
        """Write event to JSONL file."""
        with open(self.output_path, 'a') as f:
            f.write(event.to_json() + '\n')

    def get_run_summary(self, run_id: str) -> RunSummary:
        """Generate summary for a run."""
        run_events = [e for e in self.events if e.run_id == run_id]

        if not run_events:
            raise ValueError(f"No events found for run_id: {run_id}")

        return RunSummary(
            run_id=run_id,
            start_time=run_events[0].timestamp,
            end_time=run_events[-1].timestamp,
            total_steps=len(run_events),
            proceed_count=sum(1 for e in run_events if e.decision == "PROCEED"),
            soft_stop_count=sum(1 for e in run_events if e.decision == "SOFT_STOP"),
            hard_stop_count=sum(1 for e in run_events if e.decision == "HARD_STOP"),
            human_review_count=sum(1 for e in run_events if e.decision == "HUMAN_REVIEW"),
            max_drift=max(e.features.get('drift', 0) for e in run_events),
            total_violations=sum(e.features.get('violation_count', 0) for e in run_events),
            avg_latency_ms=sum(e.latency_ms for e in run_events) / len(run_events),
            final_decision=run_events[-1].decision,
            escalation_triggered=any(
                e.decision in ["HARD_STOP", "HUMAN_REVIEW"]
                for e in run_events
            )
        )


# Example event (for documentation)
EXAMPLE_EVENT = {
    "run_id": "run_20260130_143052",
    "step": 4,
    "timestamp": "2026-01-30T14:30:55.123Z",
    "hook_point": "mid_step",
    "hook_name": "drift_monitor",
    "decision": "HARD_STOP",
    "confidence": 0.92,
    "reason": "Trajectory drift 0.62 exceeds threshold 0.5",
    "features": {
        "drift": 0.62,
        "threshold": 0.5,
        "tool_risk": "high",
        "matched_rule": "high_drift_block"
    },
    "latency_ms": 45.2,
    "user_input": "Now combine all these scripts into one",
    "tool_call": None,
    "tool_result": None
}
