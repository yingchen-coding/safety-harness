"""
Adapter for safeguards-stress-tests suite.
"""

from dataclasses import dataclass
from typing import Optional
import random


@dataclass
class RedTeamResult:
    """Results from red-team evaluation."""
    model: str
    total_attacks: int
    successful_attacks: int
    attack_success_rate: float
    delayed_failure_rate: float
    avg_first_failure_turn: Optional[float]
    erosion_slope: float

    def to_dict(self) -> dict:
        return {
            'model': self.model,
            'total_attacks': self.total_attacks,
            'successful_attacks': self.successful_attacks,
            'attack_success_rate': self.attack_success_rate,
            'delayed_failure_rate': self.delayed_failure_rate,
            'avg_first_failure_turn': self.avg_first_failure_turn,
            'erosion_slope': self.erosion_slope
        }


class RedTeamAdapter:
    """
    Adapter for running red-team stress tests.

    In production, this would call safeguards-stress-tests.
    Here we simulate results for demonstration.
    """

    ATTACK_CATEGORIES = [
        'jailbreak', 'decomposition',
        'tool_hallucination', 'context_manipulation'
    ]

    def __init__(self, attack_count: int = 50):
        self.attack_count = attack_count

    def run(self, model: str) -> RedTeamResult:
        """
        Run red-team evaluation on a model.

        Args:
            model: Model identifier

        Returns:
            RedTeamResult with evaluation metrics
        """
        # Simulate evaluation results
        base_success_rate = self._get_base_rate(model)

        successful = 0
        delayed_failures = 0
        failure_turns = []
        compliance_by_turn = []

        for _ in range(self.attack_count):
            if random.random() < base_success_rate:
                successful += 1
                failure_turn = random.randint(1, 8)
                failure_turns.append(failure_turn)

                # Delayed failure = failure after turn 2
                if failure_turn > 2:
                    delayed_failures += 1

        # Simulate erosion curve
        for turn in range(1, 9):
            turn_compliance = 1.0 - (base_success_rate * (1 + turn * 0.1))
            compliance_by_turn.append(max(0, turn_compliance))

        # Compute erosion slope
        if len(compliance_by_turn) >= 2:
            erosion_slope = (compliance_by_turn[0] - compliance_by_turn[-1]) / len(compliance_by_turn)
        else:
            erosion_slope = 0.0

        return RedTeamResult(
            model=model,
            total_attacks=self.attack_count,
            successful_attacks=successful,
            attack_success_rate=successful / self.attack_count,
            delayed_failure_rate=delayed_failures / self.attack_count,
            avg_first_failure_turn=sum(failure_turns) / len(failure_turns) if failure_turns else None,
            erosion_slope=erosion_slope
        )

    def _get_base_rate(self, model: str) -> float:
        """Get base attack success rate for model (simulated)."""
        if 'v1' in model or 'baseline' in model:
            return 0.20 + random.uniform(-0.03, 0.03)
        elif 'v2' in model or 'candidate' in model:
            return 0.28 + random.uniform(-0.03, 0.03)
        else:
            return 0.25 + random.uniform(-0.05, 0.05)

    def get_metrics(self, result: RedTeamResult) -> dict:
        """Extract metrics for regression comparison."""
        return {
            'attack_success_rate': result.attack_success_rate,
            'delayed_failure_rate': result.delayed_failure_rate,
            'avg_first_failure_turn': result.avg_first_failure_turn,
            'erosion_slope': result.erosion_slope
        }
