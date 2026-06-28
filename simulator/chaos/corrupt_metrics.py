"""
Corrupt Metrics Chaos Experiment

Simulates corrupted or missing metrics from safeguard components.

Question: If we can't trust our metrics, do we fail open or fail closed?
"""

from dataclasses import dataclass
from typing import Dict, Callable
import random
from .engine import ChaosResult, DegradationLevel


@dataclass
class CorruptMetricsChaos:
    """
    Chaos experiment that corrupts metric values.

    Config options:
        corruption_type: str - "noise", "zero", "extreme", "missing"
        corruption_probability: float - Probability of corruption (default 0.5)
    """

    def name(self) -> str:
        return "corrupt_metrics"

    def inject(self, config: Dict) -> Callable:
        """Return wrapper that corrupts metrics."""

        corruption_type = config.get("corruption_type", "noise")
        corruption_prob = config.get("corruption_probability", 0.5)

        def chaos_wrapper(original_fn: Callable) -> Callable:
            def wrapped(*args, **kwargs):
                result = original_fn(*args, **kwargs)

                if random.random() < corruption_prob:
                    result["chaos_triggered"] = 1

                    # Corrupt latency metric as example
                    original_latency = result.get("latency_ms", 100)

                    if corruption_type == "noise":
                        # Add random noise
                        result["latency_ms"] = original_latency + random.gauss(0, 100)

                    elif corruption_type == "zero":
                        # Zero out metric
                        result["latency_ms"] = 0

                    elif corruption_type == "extreme":
                        # Extreme value
                        result["latency_ms"] = 999999

                    elif corruption_type == "missing":
                        # Remove metric entirely
                        if "latency_ms" in result:
                            del result["latency_ms"]
                            result["latency_ms_missing"] = True

                    result["metric_corrupted"] = True

                return result
            return wrapped
        return chaos_wrapper

    def analyze(
        self,
        original_results: Dict,
        chaos_results: Dict,
        config: Dict,
    ) -> ChaosResult:
        """Analyze impact of corrupted metrics."""

        corruption_type = config.get("corruption_type", "noise")

        # Calculate impact on decisions
        # If blocking changed due to metrics, that's a problem
        blocks_changed = chaos_results["blocked"] != original_results["blocked"]
        passes_changed = chaos_results["passed"] != original_results["passed"]

        delta = {
            "blocks_changed": blocks_changed,
            "passes_changed": passes_changed,
            "corruption_type": corruption_type,
        }

        # Determine if system is sensitive to metric corruption
        if blocks_changed:
            # Decision logic depends on potentially corrupt metrics
            degradation = DegradationLevel.CATASTROPHIC
            safety_maintained = False
            root_cause = "Blocking decisions are sensitive to metric values"
            recommendation = "Decision logic should be robust to metric noise. Add validation."
        elif passes_changed:
            degradation = DegradationLevel.PARTIAL
            safety_maintained = True
            root_cause = "Pass/warn decisions are affected by metric corruption"
            recommendation = "Add metric validation and fallback to conservative defaults"
        else:
            degradation = DegradationLevel.GRACEFUL
            safety_maintained = True
            root_cause = "Decision logic is robust to metric corruption"
            recommendation = "Good design. Consider adding metric health monitoring."

        return ChaosResult(
            experiment_name=self.name(),
            injection_type=f"corrupt_metrics_{corruption_type}",
            injection_config=config,
            degradation_level=degradation,
            safety_maintained=safety_maintained,
            functionality_maintained=not blocks_changed,
            original_behavior=original_results,
            chaos_behavior=chaos_results,
            delta=delta,
            root_cause=root_cause,
            recommendation=recommendation,
            confidence=0.7,
        )


@dataclass
class MetricValidationChaos:
    """
    Test that metric validation catches corruption.

    This is the defensive version: verify that safeguards
    catch and handle corrupted inputs.
    """

    def name(self) -> str:
        return "metric_validation"

    def inject(self, config: Dict) -> Callable:
        """Inject obviously invalid metrics to test validation."""

        def chaos_wrapper(original_fn: Callable) -> Callable:
            def wrapped(*args, **kwargs):
                result = original_fn(*args, **kwargs)

                # Inject invalid values
                result["chaos_triggered"] = 1
                result["latency_ms"] = -1  # Invalid: negative latency
                result["blocked"] = 100  # Invalid: > scenarios run
                result["confidence"] = 1.5  # Invalid: > 1.0

                return result
            return wrapped
        return chaos_wrapper

    def analyze(
        self,
        original_results: Dict,
        chaos_results: Dict,
        config: Dict,
    ) -> ChaosResult:
        """Check if validation caught invalid values."""

        # In a real implementation, we'd check if the pipeline
        # rejected or corrected the invalid values

        has_negative = chaos_results.get("latency_ms", 0) < 0
        has_overflow = chaos_results.get("blocked", 0) > chaos_results.get("scenarios_run", 100)
        has_invalid_prob = chaos_results.get("confidence", 0) > 1.0

        invalid_accepted = has_negative or has_overflow or has_invalid_prob

        if invalid_accepted:
            degradation = DegradationLevel.PARTIAL
            safety_maintained = True  # Invalid metrics don't affect safety logic
            root_cause = "Invalid metric values were not rejected"
            recommendation = "Add input validation: latency >= 0, counts <= total, probabilities in [0,1]"
        else:
            degradation = DegradationLevel.GRACEFUL
            safety_maintained = True
            root_cause = "Metric validation is working"
            recommendation = "Good validation. Consider adding bounds checks to config."

        return ChaosResult(
            experiment_name=self.name(),
            injection_type="metric_validation",
            injection_config=config,
            degradation_level=degradation,
            safety_maintained=safety_maintained,
            functionality_maintained=True,
            original_behavior=original_results,
            chaos_behavior=chaos_results,
            delta={"invalid_values_accepted": invalid_accepted},
            root_cause=root_cause,
            recommendation=recommendation,
            confidence=0.85,
        )
