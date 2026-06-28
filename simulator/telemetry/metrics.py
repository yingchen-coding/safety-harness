"""
Metrics collection for agent execution analysis.
"""

from dataclasses import dataclass
from typing import Optional
import statistics


@dataclass
class ExecutionMetrics:
    """Metrics from a single execution run."""
    total_steps: int = 0
    completed_steps: int = 0
    blocked_steps: int = 0

    # Safeguard metrics
    safeguard_triggers: int = 0
    soft_stops: int = 0
    hard_stops: int = 0
    escalations: int = 0

    # Risk metrics
    max_drift: float = 0.0
    total_drift: float = 0.0
    violation_count: int = 0

    # Tool metrics
    tools_executed: int = 0
    high_risk_tools: int = 0

    # Timing (in simulated steps)
    steps_to_first_escalation: Optional[int] = None
    steps_to_termination: Optional[int] = None

    def completion_rate(self) -> float:
        """Percentage of steps completed."""
        if self.total_steps == 0:
            return 0.0
        return self.completed_steps / self.total_steps

    def block_rate(self) -> float:
        """Percentage of steps blocked."""
        if self.total_steps == 0:
            return 0.0
        return self.blocked_steps / self.total_steps

    def safeguard_trigger_rate(self) -> float:
        """Rate of safeguard triggers per step."""
        if self.total_steps == 0:
            return 0.0
        return self.safeguard_triggers / self.total_steps

    def to_dict(self) -> dict:
        return {
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "blocked_steps": self.blocked_steps,
            "completion_rate": self.completion_rate(),
            "block_rate": self.block_rate(),
            "safeguard_triggers": self.safeguard_triggers,
            "soft_stops": self.soft_stops,
            "hard_stops": self.hard_stops,
            "escalations": self.escalations,
            "max_drift": self.max_drift,
            "total_drift": self.total_drift,
            "violation_count": self.violation_count,
            "tools_executed": self.tools_executed,
            "high_risk_tools": self.high_risk_tools,
            "steps_to_first_escalation": self.steps_to_first_escalation,
            "steps_to_termination": self.steps_to_termination
        }


class MetricsCollector:
    """
    Collects and aggregates metrics across multiple runs.
    """

    def __init__(self):
        self.runs: list[ExecutionMetrics] = []

    def add_run(self, metrics: ExecutionMetrics) -> None:
        """Add metrics from a completed run."""
        self.runs.append(metrics)

    def aggregate(self) -> dict:
        """Compute aggregate statistics across all runs."""
        if not self.runs:
            return {"error": "No runs recorded"}

        return {
            "total_runs": len(self.runs),
            "avg_steps": statistics.mean(r.total_steps for r in self.runs),
            "avg_completion_rate": statistics.mean(r.completion_rate() for r in self.runs),
            "avg_block_rate": statistics.mean(r.block_rate() for r in self.runs),
            "total_hard_stops": sum(r.hard_stops for r in self.runs),
            "total_soft_stops": sum(r.soft_stops for r in self.runs),
            "total_violations": sum(r.violation_count for r in self.runs),
            "avg_drift": statistics.mean(r.total_drift for r in self.runs),
            "max_drift_observed": max(r.max_drift for r in self.runs),
            "runs_with_escalation": sum(1 for r in self.runs if r.escalations > 0),
            "runs_terminated_early": sum(1 for r in self.runs if r.hard_stops > 0)
        }

    def by_outcome(self) -> dict:
        """Group runs by outcome type."""
        outcomes = {
            "completed": [],
            "soft_stopped": [],
            "hard_stopped": [],
            "escalated": []
        }

        for i, run in enumerate(self.runs):
            if run.hard_stops > 0:
                outcomes["hard_stopped"].append(i)
            elif run.soft_stops > 0:
                outcomes["soft_stopped"].append(i)
            elif run.escalations > 0:
                outcomes["escalated"].append(i)
            else:
                outcomes["completed"].append(i)

        return {k: len(v) for k, v in outcomes.items()}

    def safeguard_effectiveness(self) -> dict:
        """Analyze safeguard effectiveness."""
        if not self.runs:
            return {}

        # Runs where violations occurred
        violation_runs = [r for r in self.runs if r.violation_count > 0]

        # Runs where violations were caught (hard/soft stop)
        caught_runs = [r for r in violation_runs if r.hard_stops > 0 or r.soft_stops > 0]

        # Detection rate
        detection_rate = len(caught_runs) / len(violation_runs) if violation_runs else 1.0

        # False positive estimate (stops without violations)
        no_violation_runs = [r for r in self.runs if r.violation_count == 0]
        false_stops = [r for r in no_violation_runs if r.hard_stops > 0 or r.soft_stops > 0]
        false_positive_rate = len(false_stops) / len(no_violation_runs) if no_violation_runs else 0.0

        return {
            "detection_rate": detection_rate,
            "false_positive_rate": false_positive_rate,
            "total_violations": sum(r.violation_count for r in self.runs),
            "violations_caught": len(caught_runs),
            "violations_missed": len(violation_runs) - len(caught_runs)
        }

    def drift_analysis(self) -> dict:
        """Analyze drift patterns."""
        if not self.runs:
            return {}

        drifts = [r.total_drift for r in self.runs]

        return {
            "mean_drift": statistics.mean(drifts),
            "max_drift": max(drifts),
            "min_drift": min(drifts),
            "std_drift": statistics.stdev(drifts) if len(drifts) > 1 else 0.0,
            "high_drift_runs": sum(1 for d in drifts if d > 0.5),
            "drift_to_escalation_correlation": self._drift_escalation_correlation()
        }

    def _drift_escalation_correlation(self) -> str:
        """Simple correlation between drift and escalation."""
        if len(self.runs) < 5:
            return "insufficient_data"

        high_drift = [r for r in self.runs if r.total_drift > 0.5]
        high_drift_escalated = sum(1 for r in high_drift if r.escalations > 0)

        if not high_drift:
            return "no_high_drift"

        rate = high_drift_escalated / len(high_drift)
        if rate > 0.8:
            return "strong_positive"
        elif rate > 0.5:
            return "moderate_positive"
        else:
            return "weak"
