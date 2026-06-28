"""
Stricter Policy Counterfactual

Answers: "If we had lowered the threshold / been more aggressive, would we have caught this?"

This counterfactual helps calibrate safeguard sensitivity.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from .engine import CounterfactualResult, CounterfactualOutcome


@dataclass
class StricterPolicyCounterfactual:
    """
    Analyzes what would happen with stricter safeguard thresholds.

    Use cases:
    1. Determine if threshold tuning would have prevented incident
    2. Quantify false positive tradeoff of stricter policy
    3. Identify optimal threshold for this failure class
    """

    def name(self) -> str:
        return "stricter_policy"

    def apply(self, incident: Dict, config: Dict) -> CounterfactualResult:
        """
        Apply stricter policy counterfactual.

        Config options:
            threshold_delta: float - How much to lower thresholds (negative = stricter)
                Default: -0.1 (10% stricter)
            target_layer: str - Which layer to make stricter
                Options: "pre_action", "mid_trajectory", "post_action", "all"
                Default: "all"
        """
        threshold_delta = config.get("threshold_delta", -0.1)
        target_layer = config.get("target_layer", "all")

        # Extract incident details
        incident_id = incident.get("incident_id", "unknown")
        trajectory = incident.get("trajectory", [])
        original_failure_turn = self._find_failure_turn(trajectory)
        original_severity = incident.get("severity", "unknown")

        # Find near-miss signals that would have triggered with stricter threshold
        near_misses = self._find_near_misses(trajectory, threshold_delta, target_layer)

        # Determine outcome
        outcome, reasoning, cf_failure_turn = self._analyze_stricter_policy(
            near_misses,
            original_failure_turn,
            threshold_delta,
            target_layer,
        )

        # Calculate confidence
        confidence = self._estimate_confidence(near_misses, threshold_delta)

        return CounterfactualResult(
            incident_id=incident_id,
            counterfactual_type=self.name(),
            counterfactual_config=config,
            outcome=outcome,
            confidence=confidence,
            original_failure_turn=original_failure_turn,
            counterfactual_failure_turn=cf_failure_turn,
            original_severity=original_severity,
            counterfactual_severity=original_severity if outcome != CounterfactualOutcome.PREVENTED else None,
            intervention_points=[
                {
                    "turn": nm["turn"],
                    "action": f"Would trigger at {nm['adjusted_score']:.2f} (was {nm['original_score']:.2f})",
                    "layer": nm["layer"],
                }
                for nm in near_misses
            ],
            reasoning=reasoning,
        )

    def _find_failure_turn(self, trajectory: List[Dict]) -> int:
        """Find the turn where failure occurred."""
        for i, turn in enumerate(trajectory):
            if turn.get("outcome") == "UNSAFE" or turn.get("violation"):
                return i + 1
        return len(trajectory)

    def _find_near_misses(
        self,
        trajectory: List[Dict],
        threshold_delta: float,
        target_layer: str,
    ) -> List[Dict]:
        """Find signals that would have triggered with stricter threshold."""
        near_misses = []

        for turn in trajectory:
            turn_num = turn.get("turn", 0)
            safeguards = turn.get("safeguards", {})

            layers_to_check = (
                safeguards.keys() if target_layer == "all"
                else [target_layer] if target_layer in safeguards
                else []
            )

            for layer in layers_to_check:
                signal = safeguards.get(layer, {})

                if not isinstance(signal, dict):
                    continue

                original_score = signal.get("confidence", signal.get("score", signal.get("drift_score", 0)))
                threshold = signal.get("threshold", 0.5)
                triggered = signal.get("triggered", False)

                # If it didn't trigger originally, check if stricter threshold would catch it
                if not triggered:
                    adjusted_threshold = threshold + threshold_delta  # delta is negative for stricter

                    if original_score >= adjusted_threshold:
                        near_misses.append({
                            "turn": turn_num,
                            "layer": layer,
                            "original_score": original_score,
                            "original_threshold": threshold,
                            "adjusted_threshold": adjusted_threshold,
                            "adjusted_score": original_score,  # Score doesn't change, threshold does
                            "margin": original_score - adjusted_threshold,
                        })

        return sorted(near_misses, key=lambda x: x["turn"])

    def _analyze_stricter_policy(
        self,
        near_misses: List[Dict],
        original_failure_turn: int,
        threshold_delta: float,
        target_layer: str,
    ) -> tuple:
        """Analyze impact of stricter policy."""

        if not near_misses:
            return (
                CounterfactualOutcome.NO_EFFECT,
                f"No signals were close enough to trigger even with {abs(threshold_delta)*100:.0f}% stricter threshold",
                original_failure_turn,
            )

        earliest_catch = near_misses[0]

        if earliest_catch["turn"] < original_failure_turn:
            turns_saved = original_failure_turn - earliest_catch["turn"]

            if turns_saved >= 2:
                return (
                    CounterfactualOutcome.PREVENTED,
                    f"Stricter {target_layer} threshold would have caught this {turns_saved} turns earlier at turn {earliest_catch['turn']}",
                    None,
                )
            else:
                return (
                    CounterfactualOutcome.DETECTED_EARLIER,
                    f"Stricter threshold would have detected drift {turns_saved} turn(s) earlier",
                    earliest_catch["turn"],
                )

        return (
            CounterfactualOutcome.MITIGATED,
            f"Stricter threshold would have flagged {len(near_misses)} additional warning signals",
            original_failure_turn,
        )

    def _estimate_confidence(self, near_misses: List[Dict], threshold_delta: float) -> float:
        """Estimate confidence in the analysis."""

        if not near_misses:
            return 0.4  # Low confidence - no clear signal

        # Higher confidence if signals were close to threshold
        avg_margin = sum(nm["margin"] for nm in near_misses) / len(near_misses)

        # Small margin = high confidence (signal was almost caught)
        if avg_margin < 0.05:
            return 0.9
        elif avg_margin < 0.1:
            return 0.75
        elif avg_margin < 0.2:
            return 0.6
        else:
            return 0.5


@dataclass
class ThresholdSweepAnalysis:
    """
    Sweep across threshold values to find optimal tradeoff.

    Generates a curve showing:
    - Threshold value
    - Would this incident be caught?
    - Estimated false positive rate at this threshold
    """

    def sweep(
        self,
        incident: Dict,
        threshold_range: List[float] = None,
    ) -> List[Dict]:
        """
        Sweep across thresholds and return analysis.

        Returns list of {threshold, would_catch, estimated_fpr}
        """
        if threshold_range is None:
            threshold_range = [x / 100 for x in range(10, 91, 5)]

        cf = StricterPolicyCounterfactual()
        results = []

        baseline_threshold = 0.5  # Assumed default

        for threshold in threshold_range:
            delta = threshold - baseline_threshold
            result = cf.apply(incident, {"threshold_delta": delta})

            results.append({
                "threshold": threshold,
                "would_catch": result.would_have_helped(),
                "outcome": result.outcome.value,
                "catch_turn": result.counterfactual_failure_turn,
                "estimated_fpr": self._estimate_fpr(threshold),
            })

        return results

    def _estimate_fpr(self, threshold: float) -> float:
        """
        Estimate false positive rate at given threshold.

        This is a heuristic based on typical safeguard behavior.
        Real systems should use empirical data.
        """
        # Lower threshold = more triggers = higher FPR
        # This is a simplified model
        if threshold <= 0.2:
            return 0.25
        elif threshold <= 0.3:
            return 0.15
        elif threshold <= 0.4:
            return 0.08
        elif threshold <= 0.5:
            return 0.05
        elif threshold <= 0.6:
            return 0.03
        elif threshold <= 0.7:
            return 0.02
        else:
            return 0.01

    def find_optimal_threshold(self, results: List[Dict], max_fpr: float = 0.05) -> Optional[float]:
        """Find lowest threshold that catches incident within FPR budget."""

        catching = [r for r in results if r["would_catch"] and r["estimated_fpr"] <= max_fpr]

        if not catching:
            return None

        # Return lowest threshold that catches while staying within FPR budget
        return min(r["threshold"] for r in catching)
