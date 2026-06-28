"""
Pluggable Safeguard Hook API
============================

This module defines the stable API for safeguard hooks. All safeguards
must implement this interface to be registered with the runtime.

Design Philosophy:
- Hooks are plugins, not hard-coded logic
- Runtime orchestrates; hooks decide
- Each hook owns one decision point
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time


class Decision(Enum):
    """Safeguard decision outcomes."""
    PROCEED = "proceed"           # Allow action to continue
    SOFT_STOP = "soft_stop"       # Request clarification
    HARD_STOP = "hard_stop"       # Block action
    HUMAN_REVIEW = "human_review" # Escalate to human
    LOG_ONLY = "log_only"         # Log but don't intervene


@dataclass
class GuardContext:
    """Context passed to all safeguard hooks."""
    run_id: str
    step: int
    conversation_history: List[Dict[str, Any]]
    stated_goal: Optional[str] = None
    cumulative_drift: float = 0.0
    violation_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GuardDecision:
    """Decision output from a safeguard hook."""
    decision: Decision
    confidence: float
    reason: str
    features: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    hook_name: str = ""


class SafeguardHook(ABC):
    """
    Abstract base class for safeguard hooks.

    Subclasses implement specific detection logic for one hook point.
    The runtime calls hooks at appropriate points in the agent loop.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this hook."""
        pass

    @property
    @abstractmethod
    def hook_point(self) -> str:
        """Where this hook runs: 'pre_action', 'mid_step', or 'post_action'."""
        pass

    @abstractmethod
    def evaluate(self, ctx: GuardContext, event: Dict[str, Any]) -> GuardDecision:
        """
        Evaluate the event and return a decision.

        Args:
            ctx: Current guard context with conversation state
            event: The event to evaluate (user input, tool call, or tool result)

        Returns:
            GuardDecision with decision, confidence, and explanation
        """
        pass


class PreActionHook(SafeguardHook):
    """Hook that runs before any action is taken."""

    @property
    def hook_point(self) -> str:
        return "pre_action"


class MidStepHook(SafeguardHook):
    """Hook that runs during multi-step execution."""

    @property
    def hook_point(self) -> str:
        return "mid_step"


class PostActionHook(SafeguardHook):
    """Hook that runs after action completion."""

    @property
    def hook_point(self) -> str:
        return "post_action"


class SafeguardsRuntime:
    """
    Runtime orchestrator for safeguard hooks.

    Responsibilities:
    - Register and manage hooks
    - Call hooks at appropriate points
    - Aggregate decisions when multiple hooks fire
    - Emit telemetry events

    Does NOT:
    - Implement detection logic (that's in hooks)
    - Define policies (that's in policy DSL)
    - Run evaluations (that's in eval pipeline)
    """

    def __init__(self):
        self.hooks: Dict[str, List[SafeguardHook]] = {
            "pre_action": [],
            "mid_step": [],
            "post_action": []
        }
        self._telemetry_callback = None

    def register(self, hook: SafeguardHook) -> None:
        """Register a safeguard hook."""
        self.hooks[hook.hook_point].append(hook)

    def set_telemetry_callback(self, callback) -> None:
        """Set callback for telemetry emission."""
        self._telemetry_callback = callback

    def step(
        self,
        hook_point: str,
        ctx: GuardContext,
        event: Dict[str, Any]
    ) -> GuardDecision:
        """
        Run all hooks for a given hook point.

        Args:
            hook_point: 'pre_action', 'mid_step', or 'post_action'
            ctx: Current guard context
            event: Event to evaluate

        Returns:
            Aggregated GuardDecision (most restrictive wins)
        """
        decisions = []

        for hook in self.hooks[hook_point]:
            start = time.time()
            decision = hook.evaluate(ctx, event)
            decision.latency_ms = (time.time() - start) * 1000
            decision.hook_name = hook.name
            decisions.append(decision)

            # Emit telemetry
            if self._telemetry_callback:
                self._telemetry_callback(self._to_telemetry(ctx, decision))

        # Aggregate: most restrictive decision wins
        return self._aggregate_decisions(decisions)

    def _aggregate_decisions(self, decisions: List[GuardDecision]) -> GuardDecision:
        """Aggregate multiple hook decisions (most restrictive wins)."""
        if not decisions:
            return GuardDecision(
                decision=Decision.PROCEED,
                confidence=1.0,
                reason="No hooks registered"
            )

        # Priority: HARD_STOP > HUMAN_REVIEW > SOFT_STOP > LOG_ONLY > PROCEED
        priority = {
            Decision.HARD_STOP: 4,
            Decision.HUMAN_REVIEW: 3,
            Decision.SOFT_STOP: 2,
            Decision.LOG_ONLY: 1,
            Decision.PROCEED: 0
        }

        most_restrictive = max(decisions, key=lambda d: priority[d.decision])

        # Combine features from all decisions
        combined_features = {}
        for d in decisions:
            combined_features.update(d.features)

        return GuardDecision(
            decision=most_restrictive.decision,
            confidence=most_restrictive.confidence,
            reason=most_restrictive.reason,
            features=combined_features,
            latency_ms=sum(d.latency_ms for d in decisions),
            hook_name=",".join(d.hook_name for d in decisions)
        )

    def _to_telemetry(self, ctx: GuardContext, decision: GuardDecision) -> Dict:
        """Convert decision to telemetry event."""
        return {
            "run_id": ctx.run_id,
            "step": ctx.step,
            "hook": decision.hook_name,
            "decision": decision.decision.value,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "features": decision.features,
            "latency_ms": decision.latency_ms
        }


# Example hook implementation
class DriftMonitorHook(MidStepHook):
    """Example: Monitor trajectory drift."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    @property
    def name(self) -> str:
        return "drift_monitor"

    def evaluate(self, ctx: GuardContext, event: Dict[str, Any]) -> GuardDecision:
        drift = ctx.cumulative_drift

        if drift > self.threshold:
            return GuardDecision(
                decision=Decision.HARD_STOP,
                confidence=0.9,
                reason=f"Trajectory drift {drift:.2f} exceeds threshold {self.threshold}",
                features={"drift": drift, "threshold": self.threshold}
            )
        elif drift > self.threshold * 0.6:
            return GuardDecision(
                decision=Decision.SOFT_STOP,
                confidence=0.7,
                reason=f"Trajectory drift {drift:.2f} approaching threshold",
                features={"drift": drift, "threshold": self.threshold}
            )
        else:
            return GuardDecision(
                decision=Decision.PROCEED,
                confidence=0.95,
                reason="Drift within acceptable range",
                features={"drift": drift}
            )
