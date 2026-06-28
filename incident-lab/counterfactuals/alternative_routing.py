"""
Alternative Routing Counterfactual

Answers: "What if we had routed this through a different safeguard path?"

This counterfactual explores architectural alternatives:
- Different safeguard ordering
- Human-in-the-loop insertion points
- Fallback to more conservative model
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum
from .engine import CounterfactualResult, CounterfactualOutcome


class RoutingAlternative(Enum):
    """Available routing alternatives."""
    HUMAN_IN_LOOP = "human_in_loop"         # Add human review
    CONSERVATIVE_MODEL = "conservative_model"  # Fall back to safer model
    DOUBLE_CHECK = "double_check"            # Run through safeguards twice
    REORDER_SAFEGUARDS = "reorder_safeguards"  # Change safeguard order
    CAPABILITY_RESTRICTION = "capability_restriction"  # Restrict tool access


@dataclass
class AlternativeRoutingCounterfactual:
    """
    Analyzes what would happen with different request routing.

    Use cases:
    1. Identify if human review would have caught this
    2. Evaluate capability restriction as mitigation
    3. Design fallback policies for high-risk requests
    """

    def name(self) -> str:
        return "alternative_routing"

    def apply(self, incident: Dict, config: Dict) -> CounterfactualResult:
        """
        Apply alternative routing counterfactual.

        Config options:
            routing: str - Which alternative routing to analyze
                Options: "human_in_loop", "conservative_model", "double_check",
                        "reorder_safeguards", "capability_restriction"
                Default: "human_in_loop"
            insertion_turn: int - At which turn to apply the alternative
                Default: 1 (from the start)
        """
        routing = config.get("routing", "human_in_loop")
        insertion_turn = config.get("insertion_turn", 1)

        # Extract incident details
        incident_id = incident.get("incident_id", "unknown")
        trajectory = incident.get("trajectory", [])
        root_cause = incident.get("root_cause", {})
        original_failure_turn = self._find_failure_turn(trajectory)
        original_severity = incident.get("severity", "unknown")

        # Analyze the alternative routing
        if routing == "human_in_loop":
            result = self._analyze_human_in_loop(
                trajectory, root_cause, original_failure_turn, insertion_turn
            )
        elif routing == "conservative_model":
            result = self._analyze_conservative_model(
                trajectory, root_cause, original_failure_turn
            )
        elif routing == "double_check":
            result = self._analyze_double_check(
                trajectory, original_failure_turn
            )
        elif routing == "reorder_safeguards":
            result = self._analyze_reorder(
                trajectory, root_cause, original_failure_turn
            )
        elif routing == "capability_restriction":
            result = self._analyze_capability_restriction(
                trajectory, root_cause, original_failure_turn
            )
        else:
            result = (
                CounterfactualOutcome.INCONCLUSIVE,
                f"Unknown routing alternative: {routing}",
                [],
                original_failure_turn,
                0.3,
            )

        outcome, reasoning, intervention_points, cf_failure_turn, confidence = result

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
            intervention_points=intervention_points,
            reasoning=reasoning,
        )

    def _find_failure_turn(self, trajectory: List[Dict]) -> int:
        """Find the turn where failure occurred."""
        for i, turn in enumerate(trajectory):
            if turn.get("outcome") == "UNSAFE" or turn.get("violation"):
                return i + 1
        return len(trajectory)

    def _analyze_human_in_loop(
        self,
        trajectory: List[Dict],
        root_cause: Dict,
        original_failure_turn: int,
        insertion_turn: int,
    ) -> tuple:
        """Analyze if human review would have caught this."""

        # Find the first turn where drift/suspicion was detectable
        warning_turns = []
        for turn in trajectory:
            turn_num = turn.get("turn", 0)

            # Check for elevated signals that human might notice
            safeguards = turn.get("safeguards", {})
            for layer, signal in safeguards.items():
                if isinstance(signal, dict):
                    score = signal.get("confidence", signal.get("drift_score", 0))
                    if score > 0.3:  # Humans might notice moderate signals
                        warning_turns.append({
                            "turn": turn_num,
                            "layer": layer,
                            "score": score,
                        })

        # Determine outcome
        if warning_turns:
            first_warning = warning_turns[0]["turn"]

            if first_warning < original_failure_turn:
                # Human could have intervened
                return (
                    CounterfactualOutcome.PREVENTED,
                    f"Human reviewer at turn {insertion_turn} would likely notice warning signals at turn {first_warning}",
                    [
                        {"turn": w["turn"], "action": f"Human review flag: {w['layer']} score {w['score']:.2f}"}
                        for w in warning_turns[:3]
                    ],
                    None,
                    0.75,  # Moderate-high confidence
                )

        # Check if this is a coordinated misuse (humans are good at these)
        if root_cause.get("category") == "Coordinated Misuse":
            return (
                CounterfactualOutcome.PREVENTED,
                "Humans excel at detecting coordinated misuse patterns across turns",
                [{"turn": original_failure_turn, "action": "Human would notice capability accumulation"}],
                None,
                0.8,
            )

        # Human might not catch it either
        return (
            CounterfactualOutcome.MITIGATED,
            "Human review might have flagged concerns but outcome uncertain",
            [{"turn": insertion_turn, "action": "Human review point"}],
            original_failure_turn,
            0.5,
        )

    def _analyze_conservative_model(
        self,
        trajectory: List[Dict],
        root_cause: Dict,
        original_failure_turn: int,
    ) -> tuple:
        """Analyze if a more conservative model would have prevented this."""

        # Conservative models are better at:
        # - Refusing edge cases
        # - Lower capability = lower misuse potential

        failure_category = root_cause.get("category", "")

        # Coordinated misuse requires capability
        if "Coordinated" in failure_category or "Tool" in failure_category:
            return (
                CounterfactualOutcome.PREVENTED,
                "Conservative model with restricted capabilities would not enable this attack",
                [{"turn": 1, "action": "Capability restricted from start"}],
                None,
                0.85,
            )

        # Policy erosion might still happen
        if "Erosion" in failure_category:
            return (
                CounterfactualOutcome.MITIGATED,
                "Conservative model might still experience erosion but slower",
                [{"turn": original_failure_turn + 2, "action": "Delayed failure"}],
                original_failure_turn + 2,
                0.6,
            )

        return (
            CounterfactualOutcome.NO_EFFECT,
            "This failure mode is not capability-dependent",
            [],
            original_failure_turn,
            0.5,
        )

    def _analyze_double_check(
        self,
        trajectory: List[Dict],
        original_failure_turn: int,
    ) -> tuple:
        """Analyze if running safeguards twice would help."""

        # Double-check is useful when:
        # - First pass had near-misses
        # - Stochastic signals might catch on retry

        near_miss_count = 0
        for turn in trajectory:
            safeguards = turn.get("safeguards", {})
            for layer, signal in safeguards.items():
                if isinstance(signal, dict):
                    score = signal.get("confidence", 0)
                    threshold = signal.get("threshold", 0.5)
                    if 0.4 <= score < threshold:  # Near miss
                        near_miss_count += 1

        if near_miss_count >= 2:
            return (
                CounterfactualOutcome.DETECTED_EARLIER,
                f"Double-check would likely catch {near_miss_count} near-miss signals",
                [{"turn": 1, "action": f"Second pass catches {near_miss_count} signals"}],
                max(1, original_failure_turn - 1),
                0.65,
            )

        return (
            CounterfactualOutcome.NO_EFFECT,
            "No near-miss signals that second pass would catch",
            [],
            original_failure_turn,
            0.7,
        )

    def _analyze_reorder(
        self,
        trajectory: List[Dict],
        root_cause: Dict,
        original_failure_turn: int,
    ) -> tuple:
        """Analyze if different safeguard ordering would help."""

        detection_layer = root_cause.get("detection_layer", "")

        # If failure was in mid-trajectory, pre-action might have caught it
        if detection_layer == "mid_trajectory":
            return (
                CounterfactualOutcome.DETECTED_EARLIER,
                "Moving intent analysis to pre-action would catch earlier",
                [{"turn": 1, "action": "Pre-action catches intent before trajectory builds"}],
                1,
                0.6,
            )

        return (
            CounterfactualOutcome.NO_EFFECT,
            "Safeguard ordering would not significantly change outcome",
            [],
            original_failure_turn,
            0.5,
        )

    def _analyze_capability_restriction(
        self,
        trajectory: List[Dict],
        root_cause: Dict,
        original_failure_turn: int,
    ) -> tuple:
        """Analyze if restricting capabilities would have helped."""

        # Find tool/capability usage
        tools_used = set()
        for turn in trajectory:
            action = turn.get("action", "")
            if "tool" in action.lower() or "execute" in action.lower():
                tools_used.add(action)

        if tools_used:
            return (
                CounterfactualOutcome.PREVENTED,
                f"Restricting tool access would prevent {len(tools_used)} tool-dependent actions",
                [{"turn": 1, "action": f"Block tool: {t}"} for t in list(tools_used)[:3]],
                None,
                0.9,
            )

        return (
            CounterfactualOutcome.NO_EFFECT,
            "Incident did not depend on tool capabilities",
            [],
            original_failure_turn,
            0.7,
        )
