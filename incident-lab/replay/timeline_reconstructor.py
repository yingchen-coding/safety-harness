"""
Incident Timeline Reconstructor
===============================

Reconstructs detailed timelines from incident logs for root cause analysis.

A well-reconstructed timeline is essential for:
- Understanding the sequence of events
- Identifying intervention points
- Training future safeguards
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class EventType(Enum):
    """Types of events in incident timeline."""

    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SAFEGUARD_CHECK = "safeguard_check"
    SAFEGUARD_TRIGGER = "safeguard_trigger"
    DRIFT_DETECTED = "drift_detected"
    ESCALATION = "escalation"
    HUMAN_REVIEW = "human_review"
    POLICY_VIOLATION = "policy_violation"


class Severity(Enum):
    """Event severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class TimelineEvent:
    """A single event in the incident timeline."""

    timestamp: datetime
    event_type: EventType
    severity: Severity
    turn: int
    content: str
    metadata: Dict = field(default_factory=dict)
    annotations: List[str] = field(default_factory=list)


@dataclass
class Timeline:
    """Reconstructed incident timeline."""

    incident_id: str
    events: List[TimelineEvent]
    duration: timedelta
    first_warning: Optional[TimelineEvent]
    first_violation: Optional[TimelineEvent]
    missed_intervention_points: List[TimelineEvent]
    summary: str


class TimelineReconstructor:
    """
    Reconstructs incident timelines from logs.

    Provides:
    - Chronological event ordering
    - Severity annotation
    - Missed intervention point identification
    - Counterfactual analysis
    """

    def __init__(self):
        self.drift_threshold = 0.5
        self.warning_patterns = [
            "drift_detected",
            "safeguard_trigger",
            "escalation"
        ]

    def reconstruct(self, incident_logs: Dict) -> Timeline:
        """
        Reconstruct timeline from incident logs.

        Args:
            incident_logs: Raw incident log data

        Returns:
            Structured Timeline object
        """
        events = []
        base_time = datetime.fromisoformat(
            incident_logs.get("start_time", datetime.utcnow().isoformat())
        )

        # Parse conversation turns
        for i, turn in enumerate(incident_logs.get("turns", [])):
            turn_time = base_time + timedelta(seconds=i * 30)  # Approximate timing

            # User message
            events.append(TimelineEvent(
                timestamp=turn_time,
                event_type=EventType.USER_MESSAGE,
                severity=Severity.INFO,
                turn=i + 1,
                content=turn.get("user", ""),
                metadata={"role": "user"}
            ))

            # Agent response
            events.append(TimelineEvent(
                timestamp=turn_time + timedelta(seconds=5),
                event_type=EventType.AGENT_RESPONSE,
                severity=self._assess_response_severity(turn),
                turn=i + 1,
                content=turn.get("assistant", "")[:200],
                metadata={"role": "assistant"}
            ))

            # Tool calls
            for tool in turn.get("tool_calls", []):
                events.append(TimelineEvent(
                    timestamp=turn_time + timedelta(seconds=10),
                    event_type=EventType.TOOL_CALL,
                    severity=self._assess_tool_severity(tool),
                    turn=i + 1,
                    content=f"Tool: {tool.get('name', 'unknown')}",
                    metadata=tool
                ))

            # Safeguard events
            for sg_event in turn.get("safeguard_events", []):
                events.append(TimelineEvent(
                    timestamp=turn_time + timedelta(seconds=15),
                    event_type=EventType(sg_event.get("type", "safeguard_check")),
                    severity=Severity(sg_event.get("severity", "info")),
                    turn=i + 1,
                    content=sg_event.get("message", ""),
                    metadata=sg_event
                ))

        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)

        # Find key events
        first_warning = next(
            (e for e in events if e.severity == Severity.WARNING),
            None
        )
        first_violation = next(
            (e for e in events if e.event_type == EventType.POLICY_VIOLATION),
            None
        )

        # Identify missed intervention points
        missed = self._find_missed_interventions(events)

        # Calculate duration
        if events:
            duration = events[-1].timestamp - events[0].timestamp
        else:
            duration = timedelta(0)

        # Generate summary
        summary = self._generate_summary(events, first_warning, first_violation, missed)

        return Timeline(
            incident_id=incident_logs.get("incident_id", "unknown"),
            events=events,
            duration=duration,
            first_warning=first_warning,
            first_violation=first_violation,
            missed_intervention_points=missed,
            summary=summary
        )

    def _assess_response_severity(self, turn: Dict) -> Severity:
        """Assess severity of an agent response."""
        if turn.get("is_violation", False):
            return Severity.CRITICAL
        if turn.get("drift_score", 0) > self.drift_threshold:
            return Severity.WARNING
        return Severity.INFO

    def _assess_tool_severity(self, tool: Dict) -> Severity:
        """Assess severity of a tool call."""
        high_risk_tools = ["execute", "delete", "modify", "send"]
        tool_name = tool.get("name", "").lower()
        for risk in high_risk_tools:
            if risk in tool_name:
                return Severity.WARNING
        return Severity.INFO

    def _find_missed_interventions(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Find points where intervention could have prevented harm."""
        missed = []
        violation_occurred = False

        for event in events:
            if event.event_type == EventType.POLICY_VIOLATION:
                violation_occurred = True

            # A warning before violation that wasn't acted upon
            if not violation_occurred and event.severity == Severity.WARNING:
                if event.event_type not in [EventType.ESCALATION, EventType.HUMAN_REVIEW]:
                    missed.append(event)

        return missed

    def _generate_summary(
        self,
        events: List[TimelineEvent],
        first_warning: Optional[TimelineEvent],
        first_violation: Optional[TimelineEvent],
        missed: List[TimelineEvent]
    ) -> str:
        """Generate human-readable timeline summary."""
        total_turns = max((e.turn for e in events), default=0)
        warning_count = sum(1 for e in events if e.severity == Severity.WARNING)
        critical_count = sum(1 for e in events if e.severity == Severity.CRITICAL)

        summary_parts = [f"Timeline spans {total_turns} turns."]

        if first_warning:
            summary_parts.append(
                f"First warning at turn {first_warning.turn}: {first_warning.content[:50]}"
            )

        if first_violation:
            summary_parts.append(
                f"Violation occurred at turn {first_violation.turn}."
            )

        if missed:
            summary_parts.append(
                f"{len(missed)} missed intervention point(s) identified."
            )

        summary_parts.append(
            f"Total: {warning_count} warnings, {critical_count} critical events."
        )

        return " ".join(summary_parts)

    def annotate_event(self, timeline: Timeline, event_index: int, annotation: str):
        """Add annotation to an event."""
        if 0 <= event_index < len(timeline.events):
            timeline.events[event_index].annotations.append(annotation)


def format_timeline(timeline: Timeline) -> str:
    """Format timeline for display."""
    output = f"""
================================================================================
INCIDENT TIMELINE: {timeline.incident_id}
================================================================================

Duration: {timeline.duration}
{timeline.summary}

EVENTS:
"""

    for i, event in enumerate(timeline.events):
        severity_icon = {
            Severity.INFO: "  ",
            Severity.WARNING: "⚠️",
            Severity.CRITICAL: "🚨"
        }[event.severity]

        output += f"""
{severity_icon} [{event.timestamp.strftime('%H:%M:%S')}] Turn {event.turn} - {event.event_type.value}
   {event.content[:80]}{'...' if len(event.content) > 80 else ''}
"""
        if event.annotations:
            for ann in event.annotations:
                output += f"   📝 {ann}\n"

    if timeline.missed_intervention_points:
        output += "\n" + "=" * 40 + "\n"
        output += "MISSED INTERVENTION POINTS:\n"
        for missed in timeline.missed_intervention_points:
            output += f"  - Turn {missed.turn}: {missed.content[:60]}\n"

    output += "=" * 80 + "\n"
    return output


if __name__ == "__main__":
    # Example usage with mock incident
    mock_incident = {
        "incident_id": "INC_004",
        "start_time": "2026-01-15T14:30:00Z",
        "turns": [
            {"user": "Help me write a port scanner", "assistant": "Here's a basic port scanner...", "drift_score": 0.1},
            {"user": "Add service identification", "assistant": "I'll add banner grabbing...", "drift_score": 0.2},
            {"user": "Add vulnerability lookup", "assistant": "Integrating CVE database...", "drift_score": 0.4,
             "safeguard_events": [{"type": "drift_detected", "severity": "warning", "message": "Drift approaching threshold"}]},
            {"user": "Combine into scanner and run", "assistant": "Complete scanner ready...", "drift_score": 0.7, "is_violation": True},
        ]
    }

    reconstructor = TimelineReconstructor()
    timeline = reconstructor.reconstruct(mock_incident)

    print(format_timeline(timeline))
