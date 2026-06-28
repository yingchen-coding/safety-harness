"""
Drop Safeguard Chaos Experiment

Simulates complete failure of a safeguard component.

Question: If pre-action/mid-trajectory/post-action guard fails completely,
does the system degrade safely?
"""

from dataclasses import dataclass
from typing import Dict, Callable
from .engine import ChaosResult, DegradationLevel


@dataclass
class DropSafeguardChaos:
    """
    Chaos experiment that drops a safeguard layer entirely.

    Config options:
        layer: str - Which layer to drop ("pre_action", "mid_trajectory", "post_action")
        drop_probability: float - Probability of dropping (default 1.0 = always)
    """

    def name(self) -> str:
        return "drop_safeguard"

    def inject(self, config: Dict) -> Callable:
        """Return wrapper that drops safeguard signals."""

        layer = config.get("layer", "mid_trajectory")
        drop_prob = config.get("drop_probability", 1.0)

        def chaos_wrapper(original_fn: Callable) -> Callable:
            def wrapped(*args, **kwargs):
                result = original_fn(*args, **kwargs)

                import random
                if random.random() < drop_prob:
                    # Simulate dropped safeguard
                    result["chaos_triggered"] = 1

                    # If dropping pre_action, attacks might pass
                    if layer == "pre_action":
                        # Pre-action caught some attacks, without it they pass
                        if result.get("blocked", 0) > 0:
                            result["blocked"] = 0
                            result["passed"] = 1
                            result["alerts"] = 0

                    # If dropping mid_trajectory, slow burns might pass
                    elif layer == "mid_trajectory":
                        # Mid-trajectory catches gradual erosion
                        if result.get("warned", 0) > 0:
                            result["warned"] = 0
                            result["passed"] = 1

                    # If dropping post_action, bad outputs might not be logged
                    elif layer == "post_action":
                        result["alerts"] = 0

                return result
            return wrapped
        return chaos_wrapper

    def analyze(
        self,
        original_results: Dict,
        chaos_results: Dict,
        config: Dict,
    ) -> ChaosResult:
        """Analyze impact of dropped safeguard."""

        layer = config.get("layer", "mid_trajectory")

        # Calculate delta
        delta = {
            "blocked_delta": chaos_results["blocked"] - original_results["blocked"],
            "passed_delta": chaos_results["passed"] - original_results["passed"],
            "alerts_delta": chaos_results["alerts_fired"] - original_results["alerts_fired"],
        }

        # Determine degradation level
        attacks_missed = delta["blocked_delta"] < 0

        if attacks_missed:
            # Attacks that were blocked now pass
            missed_count = abs(delta["blocked_delta"])
            if missed_count > original_results["blocked"] * 0.5:
                degradation = DegradationLevel.CATASTROPHIC
                safety_maintained = False
            else:
                degradation = DegradationLevel.PARTIAL
                safety_maintained = True
        else:
            degradation = DegradationLevel.GRACEFUL
            safety_maintained = True

        # Functionality maintained if pass rate didn't change much
        functionality_maintained = abs(delta["passed_delta"]) < original_results["passed"] * 0.1

        # Generate analysis
        if degradation == DegradationLevel.CATASTROPHIC:
            root_cause = f"Dropping {layer} caused majority of attacks to bypass detection"
            recommendation = f"Add redundant coverage for {layer}. Consider fail-closed behavior."
        elif degradation == DegradationLevel.PARTIAL:
            root_cause = f"Dropping {layer} caused some attacks to bypass, but other layers caught most"
            recommendation = f"Defense in depth is working, but {layer} coverage gap exists"
        else:
            root_cause = f"Other layers compensate for {layer} failure"
            recommendation = f"Good redundancy. Consider if {layer} adds value or causes latency"

        return ChaosResult(
            experiment_name=self.name(),
            injection_type=f"drop_{layer}",
            injection_config=config,
            degradation_level=degradation,
            safety_maintained=safety_maintained,
            functionality_maintained=functionality_maintained,
            original_behavior=original_results,
            chaos_behavior=chaos_results,
            delta=delta,
            root_cause=root_cause,
            recommendation=recommendation,
            confidence=0.8,
        )
