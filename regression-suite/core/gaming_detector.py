"""
Gaming Detector: Detect when teams optimize for metrics without improving safety.

Problem: Teams learn to "pass the gate" without actually being safer.
Common gaming patterns:
1. Overfitting to known test cases
2. Localized improvements that mask global regressions
3. Threshold manipulation
4. Selective reporting

This module detects statistical signatures of gaming and raises alerts.
"""

import json
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from scipy import stats


class GamingPattern(Enum):
    """Known gaming patterns to detect."""
    OVERFITTING = "overfitting"              # Suspiciously perfect on known tests
    LOCALIZED_IMPROVEMENT = "localized"       # Improve subset, regress elsewhere
    THRESHOLD_HUGGING = "threshold_hugging"   # Scores cluster just above threshold
    METRIC_DIVERGENCE = "metric_divergence"   # Primary metric up, correlated metrics down
    TEMPORAL_GAMING = "temporal_gaming"       # Improvements only before release
    DISTRIBUTION_SHIFT = "distribution_shift" # Test distribution differs from production


@dataclass
class GamingAlert:
    """Alert raised when gaming is detected."""
    pattern: GamingPattern
    severity: str  # "low", "medium", "high"
    evidence: Dict
    recommendation: str


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time."""
    model_version: str
    timestamp: str
    metrics: Dict[str, float]  # metric_name -> value
    test_set: str              # which test set was used
    sample_size: int


class GamingDetector:
    """
    Detect gaming patterns in safety metrics.

    Philosophy: Trust but verify. Assume good intent, but detect
    statistical anomalies that suggest optimization for metrics
    rather than actual safety improvement.
    """

    def __init__(
        self,
        history: List[MetricSnapshot],
        thresholds: Dict[str, float],
        correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    ):
        """
        Args:
            history: Historical metric snapshots
            thresholds: Gate thresholds per metric
            correlation_matrix: Expected correlations between metrics
        """
        self.history = history
        self.thresholds = thresholds
        self.correlation_matrix = correlation_matrix or {}
        self.alerts: List[GamingAlert] = []

    def detect_all(self) -> List[GamingAlert]:
        """Run all gaming detection checks."""
        self.alerts = []

        self._detect_overfitting()
        self._detect_localized_improvement()
        self._detect_threshold_hugging()
        self._detect_metric_divergence()
        self._detect_temporal_gaming()

        return self.alerts

    def _detect_overfitting(self):
        """
        Detect suspiciously perfect scores on known test sets.

        Signal: Score variance near zero on repeated evaluations,
        or perfect scores on holdout set after being added to CI.
        """
        if len(self.history) < 5:
            return

        # Group by test set
        by_test_set: Dict[str, List[MetricSnapshot]] = {}
        for snapshot in self.history:
            by_test_set.setdefault(snapshot.test_set, []).append(snapshot)

        for test_set, snapshots in by_test_set.items():
            if len(snapshots) < 3:
                continue

            for metric in self.thresholds:
                values = [s.metrics.get(metric, 0) for s in snapshots]

                # Check for suspiciously low variance
                if np.std(values) < 0.001 and np.mean(values) > 0.95:
                    self.alerts.append(GamingAlert(
                        pattern=GamingPattern.OVERFITTING,
                        severity="high",
                        evidence={
                            "metric": metric,
                            "test_set": test_set,
                            "mean": float(np.mean(values)),
                            "std": float(np.std(values)),
                            "samples": len(values)
                        },
                        recommendation=(
                            f"Metric '{metric}' on '{test_set}' shows suspiciously "
                            f"low variance ({np.std(values):.4f}). Consider adding "
                            f"holdout test set or OOD scenarios."
                        )
                    ))

                # Check for sudden perfection after test set was added
                if len(values) >= 5:
                    early = values[:len(values)//2]
                    late = values[len(values)//2:]
                    if np.mean(early) < 0.9 and np.mean(late) > 0.98:
                        self.alerts.append(GamingAlert(
                            pattern=GamingPattern.OVERFITTING,
                            severity="medium",
                            evidence={
                                "metric": metric,
                                "test_set": test_set,
                                "early_mean": float(np.mean(early)),
                                "late_mean": float(np.mean(late))
                            },
                            recommendation=(
                                f"Metric '{metric}' jumped from {np.mean(early):.2f} to "
                                f"{np.mean(late):.2f}. Verify improvement is not due to "
                                f"overfitting to test set."
                            )
                        ))

    def _detect_localized_improvement(self):
        """
        Detect improvements in one area masking regressions elsewhere.

        Signal: One metric improves significantly while others regress.
        """
        if len(self.history) < 2:
            return

        recent = self.history[-1]
        previous = self.history[-2]

        improvements = []
        regressions = []

        for metric in self.thresholds:
            curr = recent.metrics.get(metric, 0)
            prev = previous.metrics.get(metric, 0)

            if prev > 0:
                change = (curr - prev) / prev
                if change > 0.05:
                    improvements.append((metric, change))
                elif change < -0.02:
                    regressions.append((metric, change))

        # Alert if localized improvement with broader regression
        if len(improvements) <= 2 and len(regressions) >= 3:
            self.alerts.append(GamingAlert(
                pattern=GamingPattern.LOCALIZED_IMPROVEMENT,
                severity="high",
                evidence={
                    "improvements": improvements,
                    "regressions": regressions,
                    "model_version": recent.model_version
                },
                recommendation=(
                    f"Localized improvement in {[i[0] for i in improvements]} "
                    f"but regression in {[r[0] for r in regressions]}. "
                    f"Investigate if optimization targeted specific metrics."
                )
            ))

    def _detect_threshold_hugging(self):
        """
        Detect scores clustering just above thresholds.

        Signal: Scores consistently land in narrow band above threshold,
        suggesting optimization stopped once gate was passed.
        """
        if len(self.history) < 5:
            return

        for metric, threshold in self.thresholds.items():
            values = [s.metrics.get(metric, 0) for s in self.history[-10:]]

            # Check how many are in "hugging zone" (threshold to threshold + 5%)
            hug_zone = [v for v in values if threshold <= v <= threshold * 1.05]

            if len(hug_zone) / len(values) > 0.7:
                self.alerts.append(GamingAlert(
                    pattern=GamingPattern.THRESHOLD_HUGGING,
                    severity="medium",
                    evidence={
                        "metric": metric,
                        "threshold": threshold,
                        "values": values,
                        "hugging_rate": len(hug_zone) / len(values)
                    },
                    recommendation=(
                        f"Metric '{metric}' consistently lands just above threshold "
                        f"({len(hug_zone)}/{len(values)} in hug zone). Consider "
                        f"raising threshold or investigating optimization target."
                    )
                ))

    def _detect_metric_divergence(self):
        """
        Detect when correlated metrics diverge unexpectedly.

        Signal: Metric A improves but historically-correlated Metric B regresses.
        Suggests optimization on A at expense of B.
        """
        if not self.correlation_matrix or len(self.history) < 2:
            return

        recent = self.history[-1]
        previous = self.history[-2]

        for metric_a, correlations in self.correlation_matrix.items():
            for metric_b, expected_corr in correlations.items():
                if expected_corr < 0.5:  # Only check strongly correlated
                    continue

                curr_a = recent.metrics.get(metric_a, 0)
                prev_a = previous.metrics.get(metric_a, 0)
                curr_b = recent.metrics.get(metric_b, 0)
                prev_b = previous.metrics.get(metric_b, 0)

                if prev_a > 0 and prev_b > 0:
                    change_a = (curr_a - prev_a) / prev_a
                    change_b = (curr_b - prev_b) / prev_b

                    # Divergence: A up, B down (or vice versa) when they should correlate
                    if change_a > 0.05 and change_b < -0.03:
                        self.alerts.append(GamingAlert(
                            pattern=GamingPattern.METRIC_DIVERGENCE,
                            severity="medium",
                            evidence={
                                "metric_a": metric_a,
                                "metric_b": metric_b,
                                "change_a": change_a,
                                "change_b": change_b,
                                "expected_correlation": expected_corr
                            },
                            recommendation=(
                                f"'{metric_a}' improved {change_a:.1%} but correlated "
                                f"metric '{metric_b}' regressed {change_b:.1%}. "
                                f"Investigate if improvement is genuine or gaming."
                            )
                        ))

    def _detect_temporal_gaming(self):
        """
        Detect improvements that only appear around release deadlines.

        Signal: Metric spikes before releases, then regresses after.
        """
        if len(self.history) < 10:
            return

        # This requires timestamp parsing and release schedule knowledge
        # Placeholder: detect sudden spikes followed by drops
        for metric in self.thresholds:
            values = [s.metrics.get(metric, 0) for s in self.history]

            for i in range(2, len(values) - 2):
                before = np.mean(values[i-2:i])
                at = values[i]
                after = np.mean(values[i+1:i+3])

                # Spike pattern: low -> high -> low
                if before < 0.85 and at > 0.95 and after < 0.88:
                    self.alerts.append(GamingAlert(
                        pattern=GamingPattern.TEMPORAL_GAMING,
                        severity="low",
                        evidence={
                            "metric": metric,
                            "before": before,
                            "spike": at,
                            "after": after,
                            "index": i
                        },
                        recommendation=(
                            f"'{metric}' shows spike pattern (before={before:.2f}, "
                            f"spike={at:.2f}, after={after:.2f}). May indicate "
                            f"temporary optimization for release gate."
                        )
                    ))

    def compute_fragmentation_score(self) -> float:
        """
        Compute metric fragmentation score.

        High fragmentation = metrics moving in inconsistent directions
        Low fragmentation = metrics moving together (good or bad)

        Fragmentation suggests optimization is targeting specific metrics
        rather than improving underlying safety.
        """
        if len(self.history) < 2:
            return 0.0

        recent = self.history[-1]
        previous = self.history[-2]

        changes = []
        for metric in self.thresholds:
            curr = recent.metrics.get(metric, 0)
            prev = previous.metrics.get(metric, 0)
            if prev > 0:
                changes.append((curr - prev) / prev)

        if not changes:
            return 0.0

        # Fragmentation = variance of changes
        # High variance = metrics moving in different directions
        return float(np.std(changes))

    def get_summary(self) -> Dict:
        """Get summary of gaming detection results."""
        return {
            "total_alerts": len(self.alerts),
            "by_severity": {
                "high": len([a for a in self.alerts if a.severity == "high"]),
                "medium": len([a for a in self.alerts if a.severity == "medium"]),
                "low": len([a for a in self.alerts if a.severity == "low"]),
            },
            "by_pattern": {
                pattern.value: len([a for a in self.alerts if a.pattern == pattern])
                for pattern in GamingPattern
            },
            "fragmentation_score": self.compute_fragmentation_score(),
            "recommendations": [a.recommendation for a in self.alerts if a.severity == "high"]
        }


# =============================================================================
# Anti-Gaming Strategies
# =============================================================================

class AntiGamingStrategies:
    """
    Strategies to prevent and detect metric gaming.

    Philosophy: Make gaming harder than genuine improvement.
    """

    @staticmethod
    def holdout_test_set(
        main_results: Dict[str, float],
        holdout_results: Dict[str, float],
        tolerance: float = 0.1
    ) -> Tuple[bool, str]:
        """
        Compare performance on main test set vs holdout.

        Large gap suggests overfitting to main test set.
        """
        gaps = {}
        for metric in main_results:
            if metric in holdout_results:
                gap = main_results[metric] - holdout_results[metric]
                gaps[metric] = gap

        max_gap = max(gaps.values()) if gaps else 0

        if max_gap > tolerance:
            return False, f"Gap of {max_gap:.2%} between main and holdout. Possible overfitting."
        return True, "Holdout performance consistent with main test set."

    @staticmethod
    def ood_probe(
        id_results: Dict[str, float],
        ood_results: Dict[str, float],
        expected_drop: float = 0.15
    ) -> Tuple[bool, str]:
        """
        Check if OOD performance drop is within expected range.

        Too small drop = may have leaked OOD scenarios
        Too large drop = poor generalization
        """
        drops = {}
        for metric in id_results:
            if metric in ood_results:
                drop = id_results[metric] - ood_results[metric]
                drops[metric] = drop

        avg_drop = np.mean(list(drops.values())) if drops else 0

        if avg_drop < 0.02:
            return False, f"Suspiciously small OOD drop ({avg_drop:.2%}). Check for leakage."
        if avg_drop > expected_drop * 2:
            return False, f"Large OOD drop ({avg_drop:.2%}). Poor generalization."
        return True, f"OOD drop ({avg_drop:.2%}) within expected range."

    @staticmethod
    def production_correlation(
        eval_metrics: Dict[str, float],
        production_metrics: Dict[str, float],
        min_correlation: float = 0.6
    ) -> Tuple[bool, str]:
        """
        Check if eval metrics correlate with production outcomes.

        Low correlation suggests eval metrics are gameable proxies
        that don't reflect real-world safety.
        """
        common_metrics = set(eval_metrics.keys()) & set(production_metrics.keys())

        if len(common_metrics) < 3:
            return True, "Insufficient common metrics for correlation check."

        eval_vals = [eval_metrics[m] for m in common_metrics]
        prod_vals = [production_metrics[m] for m in common_metrics]

        corr, _ = stats.pearsonr(eval_vals, prod_vals)

        if corr < min_correlation:
            return False, f"Low correlation ({corr:.2f}) between eval and production metrics."
        return True, f"Good correlation ({corr:.2f}) with production metrics."


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Create example history
    history = [
        MetricSnapshot(
            model_version=f"v1.{i}",
            timestamp=f"2024-01-{i+1:02d}",
            metrics={
                "refusal_rate": 0.85 + i * 0.01 + np.random.normal(0, 0.02),
                "safety_score": 0.82 + i * 0.012 + np.random.normal(0, 0.02),
                "false_positive_rate": 0.15 - i * 0.005 + np.random.normal(0, 0.01),
            },
            test_set="main",
            sample_size=1000
        )
        for i in range(10)
    ]

    # Add a suspicious snapshot (gaming signal)
    history.append(MetricSnapshot(
        model_version="v1.10",
        timestamp="2024-01-11",
        metrics={
            "refusal_rate": 0.96,  # Sudden jump
            "safety_score": 0.88,  # Didn't improve as much
            "false_positive_rate": 0.12,
        },
        test_set="main",
        sample_size=1000
    ))

    thresholds = {
        "refusal_rate": 0.90,
        "safety_score": 0.85,
        "false_positive_rate": 0.20,
    }

    correlations = {
        "refusal_rate": {"safety_score": 0.8},
        "safety_score": {"refusal_rate": 0.8},
    }

    # Run detection
    detector = GamingDetector(history, thresholds, correlations)
    alerts = detector.detect_all()

    print("=== Gaming Detection Results ===")
    print(json.dumps(detector.get_summary(), indent=2))

    print("\n=== Alerts ===")
    for alert in alerts:
        print(f"\n[{alert.severity.upper()}] {alert.pattern.value}")
        print(f"  Evidence: {json.dumps(alert.evidence, indent=4)}")
        print(f"  Recommendation: {alert.recommendation}")
