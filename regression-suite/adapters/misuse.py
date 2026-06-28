"""
Adapter for agentic-misuse-benchmark suite.
"""

from dataclasses import dataclass
from typing import Optional
import random


@dataclass
class MisuseResult:
    """Results from misuse evaluation."""
    model: str
    total_scenarios: int
    violations: int
    hedging: int
    compliant: int
    violation_rate: float
    hedging_rate: float
    avg_detection_turn: Optional[float]

    def to_dict(self) -> dict:
        return {
            'model': self.model,
            'total_scenarios': self.total_scenarios,
            'violations': self.violations,
            'hedging': self.hedging,
            'compliant': self.compliant,
            'violation_rate': self.violation_rate,
            'hedging_rate': self.hedging_rate,
            'avg_detection_turn': self.avg_detection_turn
        }


class MisuseAdapter:
    """
    Adapter for running misuse benchmark evaluations.

    In production, this would call the actual agentic-misuse-benchmark.
    Here we simulate results for demonstration.
    """

    SCENARIOS = [
        'prompt_injection', 'policy_erosion',
        'intent_drift', 'coordinated_misuse'
    ]

    def __init__(self, scenario_count: int = 25):
        self.scenario_count = scenario_count

    def run(self, model: str) -> MisuseResult:
        """
        Run misuse evaluation on a model.

        Args:
            model: Model identifier

        Returns:
            MisuseResult with evaluation metrics
        """
        # Simulate evaluation results
        # In production: call agentic-misuse-benchmark

        # Base rates vary by "model version"
        base_violation_rate = self._get_base_rate(model)

        violations = 0
        hedging = 0
        detection_turns = []

        for _ in range(self.scenario_count):
            rand = random.random()
            if rand < base_violation_rate:
                violations += 1
                detection_turns.append(random.randint(2, 6))
            elif rand < base_violation_rate + 0.15:
                hedging += 1

        compliant = self.scenario_count - violations - hedging

        return MisuseResult(
            model=model,
            total_scenarios=self.scenario_count,
            violations=violations,
            hedging=hedging,
            compliant=compliant,
            violation_rate=violations / self.scenario_count,
            hedging_rate=hedging / self.scenario_count,
            avg_detection_turn=sum(detection_turns) / len(detection_turns) if detection_turns else None
        )

    def _get_base_rate(self, model: str) -> float:
        """Get base violation rate for model (simulated)."""
        # Simulate different models having different safety levels
        if 'v1' in model or 'baseline' in model:
            return 0.08 + random.uniform(-0.02, 0.02)
        elif 'v2' in model or 'candidate' in model:
            # Candidate might be slightly worse (regression scenario)
            return 0.12 + random.uniform(-0.02, 0.02)
        else:
            return 0.10 + random.uniform(-0.03, 0.03)

    def get_metrics(self, result: MisuseResult) -> dict:
        """Extract metrics for regression comparison."""
        return {
            'violation_rate': result.violation_rate,
            'hedging_rate': result.hedging_rate,
            'avg_detection_turn': result.avg_detection_turn
        }
