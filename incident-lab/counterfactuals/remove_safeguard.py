"""
Remove Safeguard Counterfactual

Answers: "What if we had removed safeguard X? Would the incident have been worse?"

This counterfactual validates that existing safeguards are load-bearing.
If removing a safeguard has no effect, it may be redundant or misconfigured.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from .engine import CounterfactualResult, CounterfactualOutcome


@dataclass
class RemoveSafeguardCounterfactual:
    """
    Analyzes what would happen if a safeguard were removed.

    Use cases:
    1. Validate safeguards are actually effective
    2. Identify redundant safeguards
    3. Understand which safeguard caught this incident
    """

    def name(self) -> str:
        return "remove_safeguard"

    def apply(self, incident: Dict, config: Dict) -> CounterfactualResult:
        """
        Apply removal counterfactual to incident.

        Config options:
            safeguard: str - Which safeguard to remove
                Options: "pre_action", "mid_trajectory", "post_action", "all"

        Returns:
            CounterfactualResult indicating if removal would have made things worse
        """
        safeguard_to_remove = config.get("safeguard", "mid_trajectory")

        # Extract incident details
        incident_id = incident.get("incident_id", "unknown")
        trajectory = incident.get("trajectory", [])
        root_cause = incident.get("root_cause", {})
        original_failure_turn = self._find_failure_turn(trajectory)
        original_severity = incident.get("severity", "unknown")

        # Analyze which safeguard caught this (or would have)
        detection_layer = root_cause.get("detection_layer", "unknown")
        safeguard_signals = self._extract_safeguard_signals(trajectory)

        # Determine counterfactual outcome
        outcome, reasoning, intervention_points = self._analyze_removal(
            safeguard_to_remove,
            detection_layer,
            safeguard_signals,
            trajectory,
        )

        # Estimate counterfactual failure turn
        cf_failure_turn = self._estimate_counterfactual_failure(
            outcome,
            original_failure_turn,
            safeguard_to_remove,
            safeguard_signals,
        )

        # Estimate confidence based on evidence
        confidence = self._estimate_confidence(
            safeguard_signals,
            detection_layer,
            safeguard_to_remove,
        )

        return CounterfactualResult(
            incident_id=incident_id,
            counterfactual_type=self.name(),
            counterfactual_config=config,
            outcome=outcome,
            confidence=confidence,
            original_failure_turn=original_failure_turn,
            counterfactual_failure_turn=cf_failure_turn,
            original_severity=original_severity,
            counterfactual_severity=self._escalate_severity(original_severity) if outcome == CounterfactualOutcome.MADE_WORSE else original_severity,
            intervention_points=intervention_points,
            reasoning=reasoning,
        )

    def _find_failure_turn(self, trajectory: List[Dict]) -> int:
        """Find the turn where failure occurred."""
        for i, turn in enumerate(trajectory):
            if turn.get("outcome") == "UNSAFE" or turn.get("violation"):
                return i + 1
        return len(trajectory)

    def _extract_safeguard_signals(self, trajectory: List[Dict]) -> Dict[str, List[Dict]]:
        """Extract safeguard signals from trajectory."""
        signals = {
            "pre_action": [],
            "mid_trajectory": [],
            "post_action": [],
        }

        for turn in trajectory:
            safeguards = turn.get("safeguards", {})

            if "pre_action" in safeguards:
                signals["pre_action"].append({
                    "turn": turn.get("turn", 0),
                    "signal": safeguards["pre_action"],
                })

            if "mid_trajectory" in safeguards:
                signals["mid_trajectory"].append({
                    "turn": turn.get("turn", 0),
                    "signal": safeguards["mid_trajectory"],
                })

            if "post_action" in safeguards:
                signals["post_action"].append({
                    "turn": turn.get("turn", 0),
                    "signal": safeguards["post_action"],
                })

        return signals

    def _analyze_removal(
        self,
        safeguard_to_remove: str,
        detection_layer: str,
        safeguard_signals: Dict[str, List[Dict]],
        trajectory: List[Dict],
    ) -> tuple:
        """Analyze what happens if safeguard is removed."""


        # Case 1: Removing the safeguard that caught (or should have caught) this
        if safeguard_to_remove == detection_layer:
            # Check if another safeguard would have caught it
            other_layers = [k for k in safeguard_signals.keys() if k != safeguard_to_remove]

            for layer in other_layers:
                signals = safeguard_signals.get(layer, [])
                high_signals = [s for s in signals if self._is_high_signal(s)]
                if high_signals:
                    return (
                        CounterfactualOutcome.DETECTED_EARLIER if layer == "pre_action" else CounterfactualOutcome.NO_EFFECT,
                        f"Removing {safeguard_to_remove} would be caught by {layer} backup",
                        [{"turn": s["turn"], "action": f"{layer} would intervene"} for s in high_signals[:3]],
                    )

            # No backup - incident would be worse
            return (
                CounterfactualOutcome.MADE_WORSE,
                f"Removing {safeguard_to_remove} would remove the only detection layer for this failure mode",
                [{"turn": t.get("turn", 0), "action": "No safeguard to intervene"} for t in trajectory[:3]],
            )

        # Case 2: Removing a safeguard that didn't catch this incident
        removed_signals = safeguard_signals.get(safeguard_to_remove, [])

        if not removed_signals:
            return (
                CounterfactualOutcome.NO_EFFECT,
                f"Safeguard {safeguard_to_remove} was not active during this incident",
                [],
            )

        # Check if removed safeguard provided any useful signals
        useful_signals = [s for s in removed_signals if self._is_useful_signal(s)]

        if useful_signals:
            return (
                CounterfactualOutcome.MITIGATED,
                f"Removing {safeguard_to_remove} would lose early warning signals",
                [{"turn": s["turn"], "action": f"Lost signal: {s['signal']}"} for s in useful_signals[:3]],
            )

        return (
            CounterfactualOutcome.NO_EFFECT,
            f"Safeguard {safeguard_to_remove} did not contribute meaningful signals to this incident",
            [],
        )

    def _is_high_signal(self, signal_data: Dict) -> bool:
        """Check if signal indicates high confidence detection."""
        signal = signal_data.get("signal", {})
        if isinstance(signal, dict):
            confidence = signal.get("confidence", 0)
            return confidence > 0.7
        return False

    def _is_useful_signal(self, signal_data: Dict) -> bool:
        """Check if signal provided useful information."""
        signal = signal_data.get("signal", {})
        if isinstance(signal, dict):
            confidence = signal.get("confidence", 0)
            return confidence > 0.3
        return False

    def _estimate_counterfactual_failure(
        self,
        outcome: CounterfactualOutcome,
        original_failure_turn: int,
        safeguard_to_remove: str,
        safeguard_signals: Dict[str, List[Dict]],
    ) -> Optional[int]:
        """Estimate when failure would occur in counterfactual."""

        if outcome == CounterfactualOutcome.MADE_WORSE:
            # Failure would occur earlier without safeguard
            earliest_signal = None
            for signals in safeguard_signals.values():
                for s in signals:
                    if earliest_signal is None or s["turn"] < earliest_signal:
                        earliest_signal = s["turn"]
            return max(1, (earliest_signal or original_failure_turn) - 1)

        return original_failure_turn

    def _estimate_confidence(
        self,
        safeguard_signals: Dict[str, List[Dict]],
        detection_layer: str,
        safeguard_to_remove: str,
    ) -> float:
        """Estimate confidence in counterfactual analysis."""

        # Higher confidence if we have clear signal data
        total_signals = sum(len(s) for s in safeguard_signals.values())

        if total_signals == 0:
            return 0.3  # Low confidence without signal data

        if safeguard_to_remove == detection_layer:
            return 0.85  # High confidence - direct relationship

        return 0.6  # Moderate confidence

    def _escalate_severity(self, severity: str) -> str:
        """Escalate severity level."""
        escalation = {
            "low": "medium",
            "medium": "high",
            "high": "critical",
            "critical": "critical",
        }
        return escalation.get(severity, severity)
