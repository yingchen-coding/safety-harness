"""
Escalation policies for safeguards.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EscalationLevel(Enum):
    """Levels of escalation."""
    NONE = "none"
    CLARIFY = "clarify"      # Ask for clarification
    WARN = "warn"            # Warn user but continue
    SOFT_STOP = "soft_stop"  # Pause execution
    HARD_STOP = "hard_stop"  # Block execution
    HUMAN_REVIEW = "human_review"  # Flag for human review


@dataclass
class EscalationDecision:
    """Decision from escalation policy."""
    level: EscalationLevel
    reason: str
    action: str  # What action to take
    message: Optional[str] = None  # Message to user


class EscalationPolicy:
    """
    Determines appropriate escalation based on safeguard signals.

    Combines:
    - Drift score
    - Violation count
    - Uncertainty level
    - Tool risk
    """

    def __init__(
        self,
        drift_threshold: float = 0.5,
        violation_threshold: int = 1,
        uncertainty_threshold: float = 0.4
    ):
        self.drift_threshold = drift_threshold
        self.violation_threshold = violation_threshold
        self.uncertainty_threshold = uncertainty_threshold

    def evaluate(
        self,
        drift_score: float,
        violation_count: int,
        uncertainty: float,
        tool_risk: float = 0.0,
        step_count: int = 0
    ) -> EscalationDecision:
        """
        Evaluate current state and determine escalation.

        Args:
            drift_score: Cumulative drift from stated goal
            violation_count: Number of policy violations
            uncertainty: Planner uncertainty (1 - confidence)
            tool_risk: Risk level of current tool
            step_count: Number of steps executed

        Returns:
            EscalationDecision with appropriate action
        """
        # Hard stop conditions
        if violation_count >= self.violation_threshold:
            return EscalationDecision(
                level=EscalationLevel.HARD_STOP,
                reason=f"Policy violation detected ({violation_count} violations)",
                action="block",
                message="I cannot continue with this request due to policy concerns."
            )

        if drift_score >= 0.8:
            return EscalationDecision(
                level=EscalationLevel.HARD_STOP,
                reason=f"Severe drift from stated goal ({drift_score:.2f})",
                action="block",
                message="This conversation has deviated significantly from the original request."
            )

        # Human review conditions
        if drift_score >= 0.6 and uncertainty >= self.uncertainty_threshold:
            return EscalationDecision(
                level=EscalationLevel.HUMAN_REVIEW,
                reason="High drift combined with uncertainty",
                action="flag",
                message="This request has been flagged for human review."
            )

        # Soft stop conditions
        if drift_score >= self.drift_threshold:
            return EscalationDecision(
                level=EscalationLevel.SOFT_STOP,
                reason=f"Drift threshold exceeded ({drift_score:.2f})",
                action="pause",
                message="I'd like to clarify something before continuing."
            )

        if tool_risk >= 0.7:
            return EscalationDecision(
                level=EscalationLevel.SOFT_STOP,
                reason=f"High-risk tool ({tool_risk:.2f})",
                action="pause",
                message="This action requires additional confirmation."
            )

        # Clarification conditions
        if uncertainty >= self.uncertainty_threshold:
            return EscalationDecision(
                level=EscalationLevel.CLARIFY,
                reason=f"High uncertainty ({uncertainty:.2f})",
                action="ask",
                message="Could you provide more details about what you're trying to accomplish?"
            )

        # Warning conditions
        if drift_score >= 0.3:
            return EscalationDecision(
                level=EscalationLevel.WARN,
                reason=f"Minor drift detected ({drift_score:.2f})",
                action="log",
                message=None  # No user-facing message
            )

        # No escalation needed
        return EscalationDecision(
            level=EscalationLevel.NONE,
            reason="All signals within normal range",
            action="continue",
            message=None
        )


class AdaptiveEscalationPolicy(EscalationPolicy):
    """
    Escalation policy that adapts thresholds based on context.
    """

    def __init__(self, base_sensitivity: float = 0.5):
        # Adjust thresholds based on sensitivity
        # Higher sensitivity = lower thresholds = stricter
        super().__init__(
            drift_threshold=0.5 * (1.1 - base_sensitivity),
            violation_threshold=1,
            uncertainty_threshold=0.4 * (1.1 - base_sensitivity)
        )
        self.base_sensitivity = base_sensitivity

    def adjust_for_context(self, context_risk: float) -> None:
        """
        Adjust thresholds based on context risk.

        Higher risk contexts get stricter thresholds.
        """
        risk_factor = 1 - (context_risk * 0.3)
        self.drift_threshold *= risk_factor
        self.uncertainty_threshold *= risk_factor
