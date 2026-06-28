"""
Counterfactual Replay Engine

Core infrastructure for running what-if analyses on incidents.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Any
from enum import Enum
from datetime import datetime
import json


class CounterfactualOutcome(Enum):
    """Possible outcomes of counterfactual analysis."""
    PREVENTED = "prevented"           # Incident would not have occurred
    MITIGATED = "mitigated"           # Incident severity reduced
    DETECTED_EARLIER = "detected_earlier"  # Would have caught it sooner
    NO_EFFECT = "no_effect"           # Counterfactual made no difference
    MADE_WORSE = "made_worse"         # Counterfactual would have worsened outcome
    INCONCLUSIVE = "inconclusive"     # Cannot determine


@dataclass
class CounterfactualResult:
    """Result of a single counterfactual analysis."""

    incident_id: str
    counterfactual_type: str
    counterfactual_config: Dict[str, Any]

    # Outcome
    outcome: CounterfactualOutcome
    confidence: float  # 0.0 to 1.0

    # Comparison
    original_failure_turn: int
    counterfactual_failure_turn: Optional[int]  # None if prevented
    original_severity: str
    counterfactual_severity: Optional[str]

    # Evidence
    intervention_points: List[Dict[str, Any]]
    reasoning: str

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "incident_id": self.incident_id,
            "counterfactual_type": self.counterfactual_type,
            "counterfactual_config": self.counterfactual_config,
            "outcome": self.outcome.value,
            "confidence": self.confidence,
            "original_failure_turn": self.original_failure_turn,
            "counterfactual_failure_turn": self.counterfactual_failure_turn,
            "original_severity": self.original_severity,
            "counterfactual_severity": self.counterfactual_severity,
            "intervention_points": self.intervention_points,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "trace_id": self.trace_id,
        }

    def would_have_helped(self) -> bool:
        """Returns True if counterfactual would have improved outcome."""
        return self.outcome in [
            CounterfactualOutcome.PREVENTED,
            CounterfactualOutcome.MITIGATED,
            CounterfactualOutcome.DETECTED_EARLIER,
        ]


class Counterfactual(Protocol):
    """Protocol for counterfactual implementations."""

    def name(self) -> str:
        """Human-readable name of this counterfactual."""
        ...

    def apply(self, incident: Dict, config: Dict) -> CounterfactualResult:
        """Apply counterfactual to incident and return result."""
        ...


@dataclass
class CounterfactualEngine:
    """
    Engine for running counterfactual analyses on incidents.

    Usage:
        engine = CounterfactualEngine()
        engine.register(RemoveSafeguardCounterfactual())
        engine.register(StricterPolicyCounterfactual())

        results = engine.analyze(incident, [
            {"type": "remove_safeguard", "config": {"safeguard": "pre_action"}},
            {"type": "stricter_policy", "config": {"threshold_delta": -0.1}},
        ])
    """

    counterfactuals: Dict[str, Counterfactual] = field(default_factory=dict)

    def register(self, counterfactual: Counterfactual) -> None:
        """Register a counterfactual implementation."""
        self.counterfactuals[counterfactual.name()] = counterfactual

    def analyze(
        self,
        incident: Dict,
        counterfactual_specs: List[Dict],
    ) -> List[CounterfactualResult]:
        """
        Run multiple counterfactual analyses on an incident.

        Args:
            incident: The incident data (from incidents/*.json)
            counterfactual_specs: List of {"type": str, "config": dict}

        Returns:
            List of CounterfactualResult objects
        """
        results = []

        for spec in counterfactual_specs:
            cf_type = spec["type"]
            cf_config = spec.get("config", {})

            if cf_type not in self.counterfactuals:
                raise ValueError(f"Unknown counterfactual type: {cf_type}")

            cf = self.counterfactuals[cf_type]
            result = cf.apply(incident, cf_config)
            results.append(result)

        return results

    def analyze_all(self, incident: Dict) -> List[CounterfactualResult]:
        """Run all registered counterfactuals with default configs."""
        results = []

        for name, cf in self.counterfactuals.items():
            try:
                result = cf.apply(incident, {})
                results.append(result)
            except Exception as e:
                # Log but continue with other counterfactuals
                print(f"Warning: {name} failed: {e}")

        return results

    def summarize(self, results: List[CounterfactualResult]) -> Dict:
        """
        Summarize multiple counterfactual results.

        Returns prioritized list of mitigations.
        """
        helpful = [r for r in results if r.would_have_helped()]
        unhelpful = [r for r in results if not r.would_have_helped()]

        # Sort helpful by confidence and impact
        def impact_score(r: CounterfactualResult) -> float:
            outcome_scores = {
                CounterfactualOutcome.PREVENTED: 1.0,
                CounterfactualOutcome.MITIGATED: 0.7,
                CounterfactualOutcome.DETECTED_EARLIER: 0.5,
            }
            return r.confidence * outcome_scores.get(r.outcome, 0)

        helpful.sort(key=impact_score, reverse=True)

        return {
            "incident_id": results[0].incident_id if results else None,
            "counterfactuals_evaluated": len(results),
            "would_have_helped": len(helpful),
            "no_effect": len(unhelpful),
            "prioritized_mitigations": [
                {
                    "counterfactual": r.counterfactual_type,
                    "outcome": r.outcome.value,
                    "confidence": r.confidence,
                    "reasoning": r.reasoning,
                }
                for r in helpful
            ],
            "ineffective_mitigations": [
                {
                    "counterfactual": r.counterfactual_type,
                    "outcome": r.outcome.value,
                    "reasoning": r.reasoning,
                }
                for r in unhelpful
            ],
        }


def generate_counterfactual_report(
    incident_id: str,
    results: List[CounterfactualResult],
) -> str:
    """Generate human-readable counterfactual analysis report."""

    lines = [
        f"# Counterfactual Analysis: {incident_id}",
        "",
        f"**Generated**: {datetime.utcnow().isoformat()}",
        "",
        "---",
        "",
        "## Summary",
        "",
    ]

    helpful = [r for r in results if r.would_have_helped()]

    if helpful:
        lines.append(f"**{len(helpful)} of {len(results)}** counterfactuals would have improved outcome.")
        lines.append("")
        lines.append("### Recommended Mitigations (Priority Order)")
        lines.append("")

        for i, r in enumerate(helpful, 1):
            lines.append(f"**{i}. {r.counterfactual_type}** ({r.outcome.value}, {r.confidence:.0%} confidence)")
            lines.append(f"   - {r.reasoning}")
            if r.counterfactual_failure_turn:
                delta = r.counterfactual_failure_turn - r.original_failure_turn
                lines.append(f"   - Would have delayed failure by {delta} turns")
            else:
                lines.append("   - Would have **prevented** the incident")
            lines.append("")
    else:
        lines.append("**No counterfactuals** would have prevented this incident.")
        lines.append("")
        lines.append("This suggests a novel failure mode requiring new safeguard design.")

    lines.extend([
        "---",
        "",
        "## Detailed Analysis",
        "",
    ])

    for r in results:
        status = "✅" if r.would_have_helped() else "❌"
        lines.extend([
            f"### {status} {r.counterfactual_type}",
            "",
            f"**Outcome**: {r.outcome.value}",
            f"**Confidence**: {r.confidence:.0%}",
            "",
            "**Configuration**:",
            "```json",
            json.dumps(r.counterfactual_config, indent=2),
            "```",
            "",
            f"**Reasoning**: {r.reasoning}",
            "",
            "**Intervention Points**:",
        ])

        for ip in r.intervention_points:
            lines.append(f"- Turn {ip.get('turn', '?')}: {ip.get('action', 'unknown')}")

        lines.append("")

    return "\n".join(lines)
