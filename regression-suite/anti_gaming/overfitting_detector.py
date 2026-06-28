"""
Overfitting Detector

Detects when models or safeguards are overfitting to the evaluation suite.

Key Signals:
1. Eval-train gap: Performance on held-out vs. known test cases
2. Temporal pattern: Suspiciously consistent improvement only on known tests
3. Generalization failure: Good on benchmark, bad on novel scenarios
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import statistics


class OverfittingRisk(Enum):
    """Risk levels for overfitting detection."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class OverfittingSignal:
    """A detected overfitting signal."""
    signal_type: str
    risk_level: OverfittingRisk
    evidence: Dict
    recommendation: str
    confidence: float


@dataclass
class OverfittingDetector:
    """
    Detects overfitting to evaluation suites.

    Design philosophy:
    - Assume teams will optimize for metrics (this is rational behavior)
    - Detect when optimization becomes gaming
    - Flag patterns that indicate memorization rather than generalization

    Usage:
        detector = OverfittingDetector()
        signals = detector.analyze(
            known_test_results={"test_1": 0.95, "test_2": 0.92},
            holdout_results={"holdout_1": 0.65, "holdout_2": 0.70},
            historical_results=[...],
        )
    """

    # Thresholds for detection
    eval_train_gap_threshold: float = 0.15  # Max acceptable gap
    temporal_consistency_threshold: float = 0.95  # Suspiciously consistent
    generalization_ratio_threshold: float = 0.7  # Holdout should be >= 70% of known

    def analyze(
        self,
        known_test_results: Dict[str, float],
        holdout_results: Dict[str, float],
        historical_results: Optional[List[Dict[str, float]]] = None,
        novel_scenario_results: Optional[Dict[str, float]] = None,
    ) -> List[OverfittingSignal]:
        """
        Analyze results for overfitting signals.

        Args:
            known_test_results: Results on the published regression suite
            holdout_results: Results on unpublished test cases
            historical_results: Previous runs for temporal analysis
            novel_scenario_results: Results on newly created scenarios

        Returns:
            List of OverfittingSignal objects
        """
        signals = []

        # Check 1: Eval-train gap
        gap_signal = self._check_eval_train_gap(known_test_results, holdout_results)
        if gap_signal:
            signals.append(gap_signal)

        # Check 2: Temporal consistency
        if historical_results:
            temporal_signal = self._check_temporal_pattern(
                known_test_results, historical_results
            )
            if temporal_signal:
                signals.append(temporal_signal)

        # Check 3: Generalization failure
        if novel_scenario_results:
            gen_signal = self._check_generalization(
                known_test_results, novel_scenario_results
            )
            if gen_signal:
                signals.append(gen_signal)

        # Check 4: Per-test variance
        variance_signal = self._check_variance_pattern(known_test_results, holdout_results)
        if variance_signal:
            signals.append(variance_signal)

        return signals

    def _check_eval_train_gap(
        self,
        known_results: Dict[str, float],
        holdout_results: Dict[str, float],
    ) -> Optional[OverfittingSignal]:
        """Check for gap between known and holdout performance."""

        if not known_results or not holdout_results:
            return None

        known_avg = statistics.mean(known_results.values())
        holdout_avg = statistics.mean(holdout_results.values())

        gap = known_avg - holdout_avg

        if gap > self.eval_train_gap_threshold:
            risk = (
                OverfittingRisk.CRITICAL if gap > 0.3
                else OverfittingRisk.HIGH if gap > 0.2
                else OverfittingRisk.MEDIUM
            )

            return OverfittingSignal(
                signal_type="eval_train_gap",
                risk_level=risk,
                evidence={
                    "known_avg": round(known_avg, 3),
                    "holdout_avg": round(holdout_avg, 3),
                    "gap": round(gap, 3),
                    "threshold": self.eval_train_gap_threshold,
                },
                recommendation=(
                    f"Performance gap of {gap:.1%} between known tests ({known_avg:.1%}) "
                    f"and holdout ({holdout_avg:.1%}) suggests overfitting. "
                    "Consider refreshing benchmark with new scenarios."
                ),
                confidence=min(0.95, 0.5 + gap),
            )

        return None

    def _check_temporal_pattern(
        self,
        current_results: Dict[str, float],
        historical_results: List[Dict[str, float]],
    ) -> Optional[OverfittingSignal]:
        """Check for suspiciously consistent improvement patterns."""

        if len(historical_results) < 3:
            return None

        # Calculate improvement deltas per test
        improvements = []
        for test_name in current_results:
            if test_name in historical_results[-1]:
                delta = current_results[test_name] - historical_results[-1].get(test_name, 0)
                if delta > 0:
                    improvements.append(delta)

        if not improvements:
            return None

        # Check if improvements are suspiciously uniform
        if len(improvements) >= 3:
            cv = statistics.stdev(improvements) / statistics.mean(improvements) if statistics.mean(improvements) > 0 else 1

            if cv < 0.1:  # Very low coefficient of variation = suspicious
                return OverfittingSignal(
                    signal_type="temporal_consistency",
                    risk_level=OverfittingRisk.MEDIUM,
                    evidence={
                        "improvement_cv": round(cv, 3),
                        "improvements": [round(i, 3) for i in improvements[:5]],
                        "num_tests_improved": len(improvements),
                    },
                    recommendation=(
                        f"Improvements across {len(improvements)} tests are suspiciously uniform "
                        f"(CV={cv:.3f}). Natural improvement shows more variance. "
                        "Investigate if changes target specific test patterns."
                    ),
                    confidence=0.6,
                )

        return None

    def _check_generalization(
        self,
        known_results: Dict[str, float],
        novel_results: Dict[str, float],
    ) -> Optional[OverfittingSignal]:
        """Check if model generalizes to novel scenarios."""

        known_avg = statistics.mean(known_results.values())
        novel_avg = statistics.mean(novel_results.values())

        ratio = novel_avg / known_avg if known_avg > 0 else 0

        if ratio < self.generalization_ratio_threshold:
            risk = (
                OverfittingRisk.HIGH if ratio < 0.5
                else OverfittingRisk.MEDIUM
            )

            return OverfittingSignal(
                signal_type="generalization_failure",
                risk_level=risk,
                evidence={
                    "known_avg": round(known_avg, 3),
                    "novel_avg": round(novel_avg, 3),
                    "ratio": round(ratio, 3),
                    "threshold": self.generalization_ratio_threshold,
                },
                recommendation=(
                    f"Novel scenario performance ({novel_avg:.1%}) is only {ratio:.0%} "
                    f"of known test performance ({known_avg:.1%}). "
                    "This suggests overfitting to known patterns."
                ),
                confidence=0.75,
            )

        return None

    def _check_variance_pattern(
        self,
        known_results: Dict[str, float],
        holdout_results: Dict[str, float],
    ) -> Optional[OverfittingSignal]:
        """Check for variance patterns that suggest memorization."""

        if len(known_results) < 5 or len(holdout_results) < 5:
            return None

        known_var = statistics.variance(known_results.values())
        holdout_var = statistics.variance(holdout_results.values())

        # Suspiciously low variance on known tests vs holdout
        if known_var < holdout_var * 0.3 and known_var < 0.01:
            return OverfittingSignal(
                signal_type="variance_pattern",
                risk_level=OverfittingRisk.MEDIUM,
                evidence={
                    "known_variance": round(known_var, 5),
                    "holdout_variance": round(holdout_var, 5),
                    "ratio": round(known_var / holdout_var, 3) if holdout_var > 0 else 0,
                },
                recommendation=(
                    f"Known test variance ({known_var:.4f}) is much lower than "
                    f"holdout variance ({holdout_var:.4f}). This pattern suggests "
                    "specific optimization for known tests."
                ),
                confidence=0.55,
            )

        return None

    def get_risk_summary(self, signals: List[OverfittingSignal]) -> Dict:
        """Summarize overfitting risk from signals."""

        if not signals:
            return {
                "overall_risk": OverfittingRisk.NONE.value,
                "signal_count": 0,
                "recommendation": "No overfitting signals detected.",
                "action": "PROCEED",
            }

        # Aggregate risk levels
        risk_scores = {
            OverfittingRisk.NONE: 0,
            OverfittingRisk.LOW: 1,
            OverfittingRisk.MEDIUM: 2,
            OverfittingRisk.HIGH: 3,
            OverfittingRisk.CRITICAL: 4,
        }

        max_risk = max(signals, key=lambda s: risk_scores[s.risk_level])
        weighted_score = sum(risk_scores[s.risk_level] * s.confidence for s in signals)

        # Determine action
        if max_risk.risk_level == OverfittingRisk.CRITICAL:
            action = "BLOCK"
        elif max_risk.risk_level == OverfittingRisk.HIGH or weighted_score > 4:
            action = "WARN"
        else:
            action = "PROCEED"

        return {
            "overall_risk": max_risk.risk_level.value,
            "signal_count": len(signals),
            "weighted_score": round(weighted_score, 2),
            "signals": [s.signal_type for s in signals],
            "recommendation": max_risk.recommendation,
            "action": action,
        }
