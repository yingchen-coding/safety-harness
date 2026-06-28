"""
Adapter for scalable-safeguards-eval-pipeline trajectory evaluation.
"""

from dataclasses import dataclass
from typing import Optional
import random


@dataclass
class TrajectoryResult:
    """Results from trajectory evaluation."""
    model: str
    total_trajectories: int
    policy_violations: int
    policy_erosion_slope: float
    avg_first_failure: Optional[float]
    max_drift: float
    avg_drift: float

    def to_dict(self) -> dict:
        return {
            'model': self.model,
            'total_trajectories': self.total_trajectories,
            'policy_violations': self.policy_violations,
            'policy_erosion_slope': self.policy_erosion_slope,
            'avg_first_failure': self.avg_first_failure,
            'max_drift': self.max_drift,
            'avg_drift': self.avg_drift
        }


class TrajectoryAdapter:
    """
    Adapter for running trajectory-level evaluations.

    In production, this would call scalable-safeguards-eval-pipeline.
    Here we simulate results for demonstration.
    """

    def __init__(self, trajectory_count: int = 30):
        self.trajectory_count = trajectory_count

    def run(self, model: str) -> TrajectoryResult:
        """
        Run trajectory evaluation on a model.

        Args:
            model: Model identifier

        Returns:
            TrajectoryResult with evaluation metrics
        """
        base_erosion = self._get_base_erosion(model)

        violations = 0
        failure_turns = []
        drift_scores = []

        for _ in range(self.trajectory_count):
            # Simulate trajectory
            trajectory_drift = random.uniform(0, base_erosion * 2)
            drift_scores.append(trajectory_drift)

            if trajectory_drift > 0.5:
                violations += 1
                failure_turns.append(random.randint(2, 8))

        # Compute erosion slope from simulated compliance curve
        compliance_curve = [1.0 - (base_erosion * i * 0.15) for i in range(10)]
        if len(compliance_curve) >= 2:
            erosion_slope = (compliance_curve[0] - compliance_curve[-1]) / len(compliance_curve)
        else:
            erosion_slope = 0.0

        return TrajectoryResult(
            model=model,
            total_trajectories=self.trajectory_count,
            policy_violations=violations,
            policy_erosion_slope=erosion_slope,
            avg_first_failure=sum(failure_turns) / len(failure_turns) if failure_turns else None,
            max_drift=max(drift_scores) if drift_scores else 0.0,
            avg_drift=sum(drift_scores) / len(drift_scores) if drift_scores else 0.0
        )

    def _get_base_erosion(self, model: str) -> float:
        """Get base erosion rate for model (simulated)."""
        if 'v1' in model or 'baseline' in model:
            return 0.35 + random.uniform(-0.05, 0.05)
        elif 'v2' in model or 'candidate' in model:
            return 0.45 + random.uniform(-0.05, 0.05)
        else:
            return 0.40 + random.uniform(-0.08, 0.08)

    def get_metrics(self, result: TrajectoryResult) -> dict:
        """Extract metrics for regression comparison."""
        return {
            'policy_erosion_slope': result.policy_erosion_slope,
            'avg_first_failure': result.avg_first_failure,
            'max_drift': result.max_drift,
            'avg_drift': result.avg_drift,
            'violation_rate': result.policy_violations / result.total_trajectories
        }
