"""
Delay Alerting Chaos Experiment

Simulates delayed or dropped alerts from safeguard components.

Question: If alerts don't fire immediately, do incidents get worse?
"""

from dataclasses import dataclass
from typing import Dict, Callable
from .engine import ChaosResult, DegradationLevel


@dataclass
class DelayAlertingChaos:
    """
    Chaos experiment that delays or drops alerts.

    Config options:
        delay_ms: int - Alert delay in milliseconds (default 5000)
        drop_probability: float - Probability of dropping alert entirely (default 0.3)
    """

    def name(self) -> str:
        return "delay_alerting"

    def inject(self, config: Dict) -> Callable:
        """Return wrapper that delays/drops alerts."""

        delay_ms = config.get("delay_ms", 5000)
        drop_prob = config.get("drop_probability", 0.3)

        def chaos_wrapper(original_fn: Callable) -> Callable:
            def wrapped(*args, **kwargs):
                result = original_fn(*args, **kwargs)

                import random
                if result.get("alerts", 0) > 0:
                    result["chaos_triggered"] = 1

                    if random.random() < drop_prob:
                        # Alert dropped entirely
                        result["alerts"] = 0
                        result["alert_dropped"] = True
                    else:
                        # Alert delayed
                        result["latency_ms"] = result.get("latency_ms", 100) + delay_ms
                        result["alert_delayed"] = True

                return result
            return wrapped
        return chaos_wrapper

    def analyze(
        self,
        original_results: Dict,
        chaos_results: Dict,
        config: Dict,
    ) -> ChaosResult:
        """Analyze impact of delayed/dropped alerts."""

        config.get("delay_ms", 5000)
        config.get("drop_probability", 0.3)

        # Calculate delta
        original_alerts = original_results["alerts_fired"]
        chaos_alerts = chaos_results["alerts_fired"]
        alerts_lost = original_alerts - chaos_alerts

        original_latency = sum(original_results["latencies_ms"]) / len(original_results["latencies_ms"])
        chaos_latency = sum(chaos_results["latencies_ms"]) / len(chaos_results["latencies_ms"])
        latency_increase = chaos_latency - original_latency

        delta = {
            "alerts_lost": alerts_lost,
            "alerts_lost_pct": alerts_lost / original_alerts if original_alerts > 0 else 0,
            "latency_increase_ms": latency_increase,
        }

        # Determine degradation level
        # Safety is maintained if blocking still works (alerts are informational)
        blocks_unchanged = chaos_results["blocked"] == original_results["blocked"]
        safety_maintained = blocks_unchanged

        if alerts_lost > original_alerts * 0.5:
            degradation = DegradationLevel.PARTIAL
            root_cause = "Alert queue or transport is unreliable"
            recommendation = "Add persistent alert queue with at-least-once delivery"
        elif latency_increase > 10000:  # 10 second delay
            degradation = DegradationLevel.PARTIAL
            root_cause = "Alert latency exceeds incident response SLO"
            recommendation = "Add circuit breaker and fallback to synchronous alerting"
        else:
            degradation = DegradationLevel.GRACEFUL
            root_cause = "Alerts are best-effort, blocking is synchronous"
            recommendation = "Good separation of blocking (synchronous) from alerting (async)"

        return ChaosResult(
            experiment_name=self.name(),
            injection_type="delay_alerting",
            injection_config=config,
            degradation_level=degradation,
            safety_maintained=safety_maintained,
            functionality_maintained=latency_increase < 5000,
            original_behavior=original_results,
            chaos_behavior=chaos_results,
            delta=delta,
            root_cause=root_cause,
            recommendation=recommendation,
            confidence=0.75,
        )
