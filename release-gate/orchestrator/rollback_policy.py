"""
Evaluation Rollback Policy
==========================

Defines when and how to rollback evaluation infrastructure.

Production evaluation systems can fail in ways that compromise
safety assessment. This module defines rollback triggers and
recovery procedures.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime, timedelta, timezone


class RollbackTrigger(Enum):
    """Events that can trigger rollback."""

    EVAL_INFRASTRUCTURE_FAILURE = "eval_infrastructure_failure"
    DRIFT_DETECTION_FAILURE = "drift_detection_failure"
    FALSE_POSITIVE_SPIKE = "false_positive_spike"
    FALSE_NEGATIVE_DETECTION = "false_negative_detection"
    SLO_BREACH = "slo_breach"
    BUDGET_EXHAUSTION = "budget_exhaustion"
    MANUAL_TRIGGER = "manual_trigger"


class RollbackAction(Enum):
    """Actions to take on rollback."""

    PAUSE_EVAL = "pause_eval"
    REVERT_CONFIG = "revert_config"
    SWITCH_TO_BASELINE = "switch_to_baseline"
    FULL_ROLLBACK = "full_rollback"
    ALERT_ONLY = "alert_only"


@dataclass
class RollbackEvent:
    """Record of a rollback event."""

    timestamp: datetime
    trigger: RollbackTrigger
    action: RollbackAction
    affected_models: List[str]
    root_cause: str
    recovery_eta: Optional[datetime]
    resolved: bool


@dataclass
class RollbackPolicy:
    """Policy defining rollback behavior."""

    name: str
    enabled: bool
    triggers: Dict[RollbackTrigger, RollbackAction]
    cooldown_minutes: int
    auto_recovery: bool
    escalation_contacts: List[str]


# Default rollback policy
DEFAULT_POLICY = RollbackPolicy(
    name="default",
    enabled=True,
    triggers={
        RollbackTrigger.EVAL_INFRASTRUCTURE_FAILURE: RollbackAction.PAUSE_EVAL,
        RollbackTrigger.DRIFT_DETECTION_FAILURE: RollbackAction.SWITCH_TO_BASELINE,
        RollbackTrigger.FALSE_POSITIVE_SPIKE: RollbackAction.REVERT_CONFIG,
        RollbackTrigger.FALSE_NEGATIVE_DETECTION: RollbackAction.FULL_ROLLBACK,
        RollbackTrigger.SLO_BREACH: RollbackAction.PAUSE_EVAL,
        RollbackTrigger.BUDGET_EXHAUSTION: RollbackAction.ALERT_ONLY,
        RollbackTrigger.MANUAL_TRIGGER: RollbackAction.FULL_ROLLBACK,
    },
    cooldown_minutes=30,
    auto_recovery=True,
    escalation_contacts=["oncall-safety@company.com"]
)


class RollbackController:
    """
    Controls evaluation rollback logic.

    Monitors for rollback triggers and executes appropriate actions.
    """

    def __init__(self, policy: RollbackPolicy = DEFAULT_POLICY):
        self.policy = policy
        self.events: List[RollbackEvent] = []
        self.last_rollback: Optional[datetime] = None

    def check_trigger(self, trigger: RollbackTrigger, context: Dict) -> Optional[RollbackEvent]:
        """
        Check if trigger should cause rollback.

        Args:
            trigger: The triggering event
            context: Additional context (metrics, affected models, etc.)

        Returns:
            RollbackEvent if rollback initiated, None otherwise
        """
        if not self.policy.enabled:
            return None

        # Check cooldown
        if self.last_rollback:
            cooldown_end = self.last_rollback + timedelta(minutes=self.policy.cooldown_minutes)
            if datetime.now(timezone.utc) < cooldown_end:
                return None  # Still in cooldown

        # Determine action
        action = self.policy.triggers.get(trigger, RollbackAction.ALERT_ONLY)

        # Create event
        event = RollbackEvent(
            timestamp=datetime.now(timezone.utc),
            trigger=trigger,
            action=action,
            affected_models=context.get("affected_models", []),
            root_cause=context.get("root_cause", "Unknown"),
            recovery_eta=self._estimate_recovery(action),
            resolved=False
        )

        self.events.append(event)
        self.last_rollback = event.timestamp

        # Execute action
        self._execute_action(action, context)

        return event

    def _execute_action(self, action: RollbackAction, context: Dict):
        """Execute rollback action."""

        if action == RollbackAction.PAUSE_EVAL:
            print("[ROLLBACK] Pausing evaluation pipeline")
            # In real implementation: pause scheduler, drain queues

        elif action == RollbackAction.REVERT_CONFIG:
            print("[ROLLBACK] Reverting to previous configuration")
            # In real implementation: restore config from backup

        elif action == RollbackAction.SWITCH_TO_BASELINE:
            print("[ROLLBACK] Switching to baseline evaluation model")
            # In real implementation: swap model pointers

        elif action == RollbackAction.FULL_ROLLBACK:
            print("[ROLLBACK] Full rollback initiated")
            # In real implementation: full system restore

        elif action == RollbackAction.ALERT_ONLY:
            print("[ALERT] Rollback trigger detected, alerting only")
            # In real implementation: send alerts

        # Always notify
        self._send_notification(action, context)

    def _estimate_recovery(self, action: RollbackAction) -> datetime:
        """Estimate recovery time based on action severity."""
        recovery_times = {
            RollbackAction.ALERT_ONLY: 0,
            RollbackAction.PAUSE_EVAL: 15,
            RollbackAction.REVERT_CONFIG: 30,
            RollbackAction.SWITCH_TO_BASELINE: 60,
            RollbackAction.FULL_ROLLBACK: 120,
        }
        minutes = recovery_times.get(action, 60)
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)

    def _send_notification(self, action: RollbackAction, context: Dict):
        """Send notification to escalation contacts."""
        for contact in self.policy.escalation_contacts:
            print(f"[NOTIFY] Sending rollback alert to {contact}")

    def resolve_event(self, event_index: int, resolution: str):
        """Mark a rollback event as resolved."""
        if 0 <= event_index < len(self.events):
            self.events[event_index].resolved = True
            print(f"[RESOLVED] Event resolved: {resolution}")

    def get_active_events(self) -> List[RollbackEvent]:
        """Get unresolved rollback events."""
        return [e for e in self.events if not e.resolved]


# Rollback trigger detection functions

def detect_false_positive_spike(metrics: Dict, threshold: float = 0.15) -> bool:
    """Detect if false positive rate has spiked."""
    current_fpr = metrics.get("false_positive_rate", 0)
    baseline_fpr = metrics.get("baseline_fpr", 0.05)
    return current_fpr > baseline_fpr + threshold


def detect_false_negative(incidents: List[Dict]) -> bool:
    """Detect if a false negative (missed violation) occurred."""
    return any(i.get("type") == "false_negative" for i in incidents)


def detect_slo_breach(metrics: Dict, slo_config: Dict) -> bool:
    """Detect if SLO is breached."""
    latency = metrics.get("p99_latency_ms", 0)
    availability = metrics.get("availability", 1.0)

    latency_breach = latency > slo_config.get("max_latency_ms", 1000)
    availability_breach = availability < slo_config.get("min_availability", 0.999)

    return latency_breach or availability_breach


if __name__ == "__main__":
    # Example usage
    controller = RollbackController()

    # Simulate trigger
    context = {
        "affected_models": ["claude-3.5", "gpt-4"],
        "root_cause": "Drift detector calibration error"
    }

    event = controller.check_trigger(
        RollbackTrigger.DRIFT_DETECTION_FAILURE,
        context
    )

    if event:
        print("\nRollback initiated:")
        print(f"  Trigger: {event.trigger.value}")
        print(f"  Action: {event.action.value}")
        print(f"  Recovery ETA: {event.recovery_eta}")
