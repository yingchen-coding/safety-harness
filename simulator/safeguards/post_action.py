"""
Post-action safeguards - Audit after completion.
"""

from typing import Optional

from .base import BaseSafeguard, SafeguardResult, SafeguardLevel
from agent.planner import Action
from agent.memory import Memory
from agent.tools import ToolResult, ToolStatus


class OutcomeVerifier(BaseSafeguard):
    """
    Verifies action outcomes match expectations.
    """

    name = "outcome_verifier"
    description = "Post-action outcome verification"

    def check(
        self,
        action: Action,
        tool_result: Optional[ToolResult],
        memory: Memory
    ) -> SafeguardResult:
        """Verify action outcome."""
        if not tool_result:
            return SafeguardResult(
                level=SafeguardLevel.PASS,
                score=0.0,
                reason="No tool result to verify",
                details={"status": "ok"}
            )

        # Check tool execution status
        if tool_result.status == ToolStatus.ERROR:
            return SafeguardResult(
                level=SafeguardLevel.WARN,
                score=0.3,
                reason="Tool execution error",
                details={"status": "error", "tool": tool_result.tool}
            )

        if tool_result.status == ToolStatus.BLOCKED:
            return SafeguardResult(
                level=SafeguardLevel.WARN,
                score=0.5,
                reason="Tool was blocked",
                details={"status": "blocked", "tool": tool_result.tool}
            )

        # Check risk score
        if tool_result.risk_score > 0.7:
            return SafeguardResult(
                level=SafeguardLevel.WARN,
                score=tool_result.risk_score,
                reason="High-risk tool execution completed",
                details={
                    "status": "high_risk",
                    "tool": tool_result.tool,
                    "risk": tool_result.risk_score
                }
            )

        return SafeguardResult(
            level=SafeguardLevel.PASS,
            score=0.0,
            reason="Outcome verified",
            details={"status": "ok", "tool": tool_result.tool}
        )


class AnomalyDetector(BaseSafeguard):
    """
    Detects anomalies in tool outputs.
    """

    name = "anomaly_detector"
    description = "Post-action anomaly detection"

    ANOMALY_INDICATORS = [
        "error", "failed", "denied", "unauthorized",
        "unexpected", "malformed", "invalid"
    ]

    def check(
        self,
        action: Action,
        tool_result: Optional[ToolResult],
        memory: Memory
    ) -> SafeguardResult:
        """Check for anomalies in output."""
        if not tool_result or not tool_result.output:
            return SafeguardResult(
                level=SafeguardLevel.PASS,
                score=0.0,
                reason="No output to analyze"
            )

        output_lower = str(tool_result.output).lower()
        anomalies = [ind for ind in self.ANOMALY_INDICATORS if ind in output_lower]

        if anomalies:
            return SafeguardResult(
                level=SafeguardLevel.WARN,
                score=min(len(anomalies) / 3, 1.0),
                reason=f"Anomalies detected: {', '.join(anomalies)}",
                details={"anomalies": anomalies, "status": "anomaly"}
            )

        return SafeguardResult(
            level=SafeguardLevel.PASS,
            score=0.0,
            reason="No anomalies detected",
            details={"status": "ok"}
        )


def create_post_action_hook(sensitivity: float = 0.5):
    """Create a post-action hook combining auditors."""
    outcome_verifier = OutcomeVerifier(sensitivity)
    anomaly_detector = AnomalyDetector(sensitivity)

    def hook(
        action: Action,
        tool_result: Optional[ToolResult],
        memory: Memory
    ) -> dict:
        outcome_result = outcome_verifier.check(action, tool_result, memory)
        anomaly_result = anomaly_detector.check(action, tool_result, memory)

        # Combine statuses
        status = outcome_result.details.get("status", "ok")
        if anomaly_result.details.get("status") == "anomaly":
            status = "anomaly"

        return {
            "status": status,
            "outcome_score": outcome_result.score,
            "anomaly_score": anomaly_result.score,
            "details": {
                **outcome_result.details,
                **anomaly_result.details
            }
        }

    return hook
