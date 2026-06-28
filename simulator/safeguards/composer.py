"""
Safeguard Strategy Composer
===========================

Composes multiple safeguard layers into unified defense strategies.

This module enables:
- Explicit Pre + Mid + Post safeguard combinations
- Strategy-level ablation experiments
- Quantitative comparison of defense configurations
"""

from dataclasses import dataclass
from typing import Dict, List, Callable
from enum import Enum


class SafeguardLayer(Enum):
    """Safeguard placement in the agent loop."""

    PRE_ACTION = "pre_action"
    MID_TRAJECTORY = "mid_trajectory"
    POST_ACTION = "post_action"


class SafeguardAction(Enum):
    """Actions a safeguard can take."""

    ALLOW = "allow"
    SOFT_STOP = "soft_stop"
    HARD_STOP = "hard_stop"
    LOG_ONLY = "log_only"


@dataclass
class SafeguardResult:
    """Result from a single safeguard check."""

    layer: SafeguardLayer
    action: SafeguardAction
    confidence: float
    reason: str
    metadata: Dict


@dataclass
class ComposedResult:
    """Result from composed safeguard strategy."""

    final_action: SafeguardAction
    layer_results: List[SafeguardResult]
    strategy_name: str
    execution_time_ms: float


class SafeguardComposer:
    """
    Composes multiple safeguard layers into a unified strategy.

    Supports:
    - Sequential execution (Pre → Mid → Post)
    - Parallel execution with aggregation
    - Custom composition rules
    """

    def __init__(self, name: str):
        self.name = name
        self.layers: Dict[SafeguardLayer, List[Callable]] = {
            SafeguardLayer.PRE_ACTION: [],
            SafeguardLayer.MID_TRAJECTORY: [],
            SafeguardLayer.POST_ACTION: []
        }
        self.aggregation_rule = "most_restrictive"

    def add_safeguard(self, layer: SafeguardLayer, safeguard: Callable):
        """Add a safeguard to a specific layer."""
        self.layers[layer].append(safeguard)

    def set_aggregation_rule(self, rule: str):
        """
        Set how multiple layer results are combined.

        Options:
        - most_restrictive: Any HARD_STOP wins
        - majority_vote: Majority action wins
        - weighted: Confidence-weighted aggregation
        """
        self.aggregation_rule = rule

    def execute(self, context: Dict) -> ComposedResult:
        """
        Execute composed strategy on given context.

        Args:
            context: Agent state including request, history, tool calls

        Returns:
            ComposedResult with final action and per-layer details
        """
        import time
        start = time.time()

        results = []

        # Execute layers in order
        for layer in [SafeguardLayer.PRE_ACTION,
                      SafeguardLayer.MID_TRAJECTORY,
                      SafeguardLayer.POST_ACTION]:

            for safeguard in self.layers[layer]:
                result = safeguard(context)
                results.append(SafeguardResult(
                    layer=layer,
                    action=result.get("action", SafeguardAction.ALLOW),
                    confidence=result.get("confidence", 1.0),
                    reason=result.get("reason", ""),
                    metadata=result.get("metadata", {})
                ))

        # Aggregate results
        final_action = self._aggregate(results)

        execution_time = (time.time() - start) * 1000

        return ComposedResult(
            final_action=final_action,
            layer_results=results,
            strategy_name=self.name,
            execution_time_ms=execution_time
        )

    def _aggregate(self, results: List[SafeguardResult]) -> SafeguardAction:
        """Aggregate layer results into final action."""

        if self.aggregation_rule == "most_restrictive":
            # Priority: HARD_STOP > SOFT_STOP > LOG_ONLY > ALLOW
            priority = {
                SafeguardAction.HARD_STOP: 4,
                SafeguardAction.SOFT_STOP: 3,
                SafeguardAction.LOG_ONLY: 2,
                SafeguardAction.ALLOW: 1
            }
            return max(results, key=lambda r: priority[r.action]).action

        elif self.aggregation_rule == "majority_vote":
            from collections import Counter
            actions = [r.action for r in results]
            return Counter(actions).most_common(1)[0][0]

        elif self.aggregation_rule == "weighted":
            # Confidence-weighted aggregation
            scores = {}
            for r in results:
                if r.action not in scores:
                    scores[r.action] = 0
                scores[r.action] += r.confidence
            return max(scores.items(), key=lambda x: x[1])[0]

        return SafeguardAction.ALLOW


# Predefined strategy compositions
STRATEGIES = {
    "none": {
        "description": "No safeguards (baseline)",
        "layers": {
            "pre_action": False,
            "mid_trajectory": False,
            "post_action": False
        }
    },
    "pre_only": {
        "description": "Pre-action checks only",
        "layers": {
            "pre_action": True,
            "mid_trajectory": False,
            "post_action": False
        }
    },
    "mid_only": {
        "description": "Mid-trajectory monitoring only",
        "layers": {
            "pre_action": False,
            "mid_trajectory": True,
            "post_action": False
        }
    },
    "post_only": {
        "description": "Post-action audit only",
        "layers": {
            "pre_action": False,
            "mid_trajectory": False,
            "post_action": True
        }
    },
    "pre_mid": {
        "description": "Pre-action + mid-trajectory",
        "layers": {
            "pre_action": True,
            "mid_trajectory": True,
            "post_action": False
        }
    },
    "full_stack": {
        "description": "All three layers (recommended)",
        "layers": {
            "pre_action": True,
            "mid_trajectory": True,
            "post_action": True
        }
    }
}


def create_strategy(strategy_name: str) -> SafeguardComposer:
    """Create a composer from predefined strategy."""

    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    config = STRATEGIES[strategy_name]
    composer = SafeguardComposer(strategy_name)

    # In real implementation, load actual safeguard implementations
    # Here we use placeholders
    if config["layers"]["pre_action"]:
        composer.add_safeguard(SafeguardLayer.PRE_ACTION, _placeholder_pre)
    if config["layers"]["mid_trajectory"]:
        composer.add_safeguard(SafeguardLayer.MID_TRAJECTORY, _placeholder_mid)
    if config["layers"]["post_action"]:
        composer.add_safeguard(SafeguardLayer.POST_ACTION, _placeholder_post)

    return composer


def _placeholder_pre(context: Dict) -> Dict:
    """Placeholder pre-action safeguard."""
    return {"action": SafeguardAction.ALLOW, "confidence": 0.9, "reason": "Pre-check passed"}


def _placeholder_mid(context: Dict) -> Dict:
    """Placeholder mid-trajectory safeguard."""
    return {"action": SafeguardAction.ALLOW, "confidence": 0.85, "reason": "Drift within threshold"}


def _placeholder_post(context: Dict) -> Dict:
    """Placeholder post-action safeguard."""
    return {"action": SafeguardAction.ALLOW, "confidence": 0.95, "reason": "Output validated"}


if __name__ == "__main__":
    # Example usage
    print("Available strategies:")
    for name, config in STRATEGIES.items():
        layers = [k for k, v in config["layers"].items() if v]
        print(f"  {name}: {config['description']} ({', '.join(layers) or 'none'})")

    # Create and execute strategy
    strategy = create_strategy("full_stack")
    result = strategy.execute({"request": "test", "history": []})

    print(f"\nExecuted strategy: {result.strategy_name}")
    print(f"Final action: {result.final_action}")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")
