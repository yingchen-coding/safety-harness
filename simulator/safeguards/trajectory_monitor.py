"""
Mid-trajectory safeguards - Monitor during execution.
"""

from typing import Optional

from .base import BaseSafeguard, SafeguardResult, SafeguardLevel
from agent.planner import Action, Plan
from agent.memory import Memory
from agent.tools import ToolResult


class DriftMonitor(BaseSafeguard):
    """
    Monitors semantic drift from stated goal.

    Detects when the conversation is moving away from
    the original stated intent.
    """

    name = "drift_monitor"
    description = "Mid-trajectory drift detection"

    # Topic categories for drift detection
    TOPIC_KEYWORDS = {
        "benign": ["help", "learn", "understand", "plan", "create", "write"],
        "risky": ["hack", "bypass", "exploit", "attack", "steal", "trick"],
        "sensitive": ["password", "credential", "private", "secret", "personal"],
    }

    def __init__(self, sensitivity: float = 0.5):
        super().__init__(sensitivity)
        self.baseline_topics = None

    def check(
        self,
        action: Action,
        tool_result: Optional[ToolResult],
        memory: Memory,
        plan: Plan
    ) -> SafeguardResult:
        """Check for trajectory drift."""
        context = memory.get_conversation_context()
        current_topics = self._extract_topics(context + action.description)

        # Establish baseline on first check
        if self.baseline_topics is None:
            self.baseline_topics = self._extract_topics(plan.goal)

        # Calculate drift
        drift_score = self._calculate_drift(self.baseline_topics, current_topics)

        # Check for topic escalation (benign → risky)
        escalation = self._check_escalation(current_topics)

        # Combined score
        combined_score = 0.6 * drift_score + 0.4 * escalation

        # Accumulate drift in memory
        current_total = memory.state.total_drift + combined_score * 0.2

        # Determine level
        soft_threshold = self.adjust_threshold(0.4)
        hard_threshold = self.adjust_threshold(0.7)

        if current_total >= hard_threshold:
            level = SafeguardLevel.HARD_STOP
            reason = f"Significant drift detected (total: {current_total:.2f})"
        elif current_total >= soft_threshold:
            level = SafeguardLevel.SOFT_STOP
            reason = f"Drift threshold approaching (total: {current_total:.2f})"
        elif combined_score >= 0.2:
            level = SafeguardLevel.WARN
            reason = "Minor drift detected"
        else:
            level = SafeguardLevel.PASS
            reason = "Trajectory on track"

        return SafeguardResult(
            level=level,
            score=combined_score,
            reason=reason,
            details={
                "drift": combined_score,
                "total_drift": current_total,
                "escalation": escalation,
                "violation": current_total >= hard_threshold,
                "escalation_triggered": level in [SafeguardLevel.SOFT_STOP, SafeguardLevel.HARD_STOP]
            }
        )

    def _extract_topics(self, text: str) -> dict[str, int]:
        """Extract topic counts from text."""
        text_lower = text.lower()
        topics = {}
        for category, keywords in self.TOPIC_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            topics[category] = count
        return topics

    def _calculate_drift(self, baseline: dict, current: dict) -> float:
        """Calculate drift from baseline topics."""
        if not baseline or not current:
            return 0.0

        # Check if risky topics increased
        baseline_risky = baseline.get("risky", 0)
        current_risky = current.get("risky", 0)

        if current_risky > baseline_risky:
            return min((current_risky - baseline_risky) / 3, 1.0)

        return 0.0

    def _check_escalation(self, topics: dict) -> float:
        """Check for escalation to risky topics."""
        risky = topics.get("risky", 0)
        sensitive = topics.get("sensitive", 0)

        return min((risky + sensitive) / 4, 1.0)


class ViolationMonitor(BaseSafeguard):
    """
    Monitors for policy violations during execution.
    """

    name = "violation_monitor"
    description = "Mid-trajectory violation detection"

    VIOLATION_PATTERNS = [
        "unauthorized", "illegal", "prohibited", "restricted",
        "confidential", "classified", "harmful", "dangerous"
    ]

    def check(
        self,
        action: Action,
        tool_result: Optional[ToolResult],
        memory: Memory,
        plan: Plan
    ) -> SafeguardResult:
        """Check for policy violations."""
        # Check tool result for violations
        if tool_result and tool_result.output:
            output_lower = str(tool_result.output).lower()
            violations = [p for p in self.VIOLATION_PATTERNS if p in output_lower]

            if violations:
                return SafeguardResult(
                    level=SafeguardLevel.HARD_STOP,
                    score=1.0,
                    reason=f"Violation detected: {violations[0]}",
                    details={"violations": violations}
                )

        # Check action risk
        if action.risk_level >= 0.8:
            return SafeguardResult(
                level=SafeguardLevel.SOFT_STOP,
                score=action.risk_level,
                reason="High-risk action",
                details={"action_risk": action.risk_level}
            )

        return SafeguardResult(
            level=SafeguardLevel.PASS,
            score=0.0,
            reason="No violations detected"
        )


def create_mid_trajectory_hook(sensitivity: float = 0.5):
    """Create a mid-trajectory hook combining monitors."""
    drift_monitor = DriftMonitor(sensitivity)
    violation_monitor = ViolationMonitor(sensitivity)

    def hook(
        action: Action,
        tool_result: Optional[ToolResult],
        memory: Memory,
        plan: Plan
    ) -> dict:
        # Run both monitors
        drift_result = drift_monitor.check(action, tool_result, memory, plan)
        violation_result = violation_monitor.check(action, tool_result, memory, plan)

        # Combine results
        max(drift_result.score, violation_result.score)
        violation = drift_result.details.get("violation", False) or violation_result.blocked

        # Take the more severe level
        if violation_result.level.value > drift_result.level.value:
            primary = violation_result
        else:
            primary = drift_result

        return {
            **primary.to_dict(),
            "drift": drift_result.score,
            "total_drift": drift_result.details.get("total_drift", 0.0),
            "violation": violation,
            "escalation": primary.level in [SafeguardLevel.SOFT_STOP, SafeguardLevel.HARD_STOP]
        }

    return hook
