"""
Change Impact Analysis

Predicts how changes will shift risk profiles before running full evaluation.

Philosophy: Don't just run tests; predict how changes will shift risk.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
from datetime import datetime, timezone


class RiskDirection(Enum):
    """Direction of risk shift."""
    INCREASE = "increase"
    DECREASE = "decrease"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class RiskCategory(Enum):
    """Categories of safety risk."""
    POLICY_EROSION = "policy_erosion"
    INJECTION = "injection"
    COORDINATED_MISUSE = "coordinated_misuse"
    TOOL_ABUSE = "tool_abuse"
    FALSE_POSITIVE = "false_positive"
    HEDGING_LEAKAGE = "hedging_leakage"


@dataclass
class ComponentChange:
    """A change to a system component."""
    component: str
    change_type: str  # "modified", "added", "removed", "config_change"
    files_changed: List[str]
    description: str
    commit_hash: Optional[str] = None


@dataclass
class RiskShift:
    """Predicted shift in a risk category."""
    category: RiskCategory
    direction: RiskDirection
    confidence: float  # 0.0 to 1.0
    reasoning: str
    affected_metrics: List[str]


@dataclass
class ImpactAnalysisResult:
    """Result of change impact analysis."""
    changes: List[ComponentChange]
    risk_shifts: List[RiskShift]
    required_additional_tests: List[str]
    recommended_focus_areas: List[str]
    overall_risk_assessment: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            "changes": [
                {
                    "component": c.component,
                    "change_type": c.change_type,
                    "files_changed": c.files_changed,
                    "description": c.description,
                }
                for c in self.changes
            ],
            "risk_shifts": [
                {
                    "category": rs.category.value,
                    "direction": rs.direction.value,
                    "confidence": rs.confidence,
                    "reasoning": rs.reasoning,
                    "affected_metrics": rs.affected_metrics,
                }
                for rs in self.risk_shifts
            ],
            "required_additional_tests": self.required_additional_tests,
            "recommended_focus_areas": self.recommended_focus_areas,
            "overall_risk_assessment": self.overall_risk_assessment,
            "timestamp": self.timestamp.isoformat(),
        }


# Component → Risk category mapping
COMPONENT_RISK_MAP: Dict[str, List[Tuple[RiskCategory, RiskDirection]]] = {
    # Safeguard components
    "pre_action_filter": [
        (RiskCategory.INJECTION, RiskDirection.UNKNOWN),
        (RiskCategory.FALSE_POSITIVE, RiskDirection.UNKNOWN),
    ],
    "mid_trajectory_monitor": [
        (RiskCategory.POLICY_EROSION, RiskDirection.UNKNOWN),
        (RiskCategory.COORDINATED_MISUSE, RiskDirection.UNKNOWN),
    ],
    "post_action_validator": [
        (RiskCategory.TOOL_ABUSE, RiskDirection.UNKNOWN),
        (RiskCategory.HEDGING_LEAKAGE, RiskDirection.UNKNOWN),
    ],
    "policy_dsl": [
        (RiskCategory.POLICY_EROSION, RiskDirection.UNKNOWN),
        (RiskCategory.FALSE_POSITIVE, RiskDirection.UNKNOWN),
    ],
    "drift_threshold": [
        (RiskCategory.POLICY_EROSION, RiskDirection.UNKNOWN),
    ],
    "intent_classifier": [
        (RiskCategory.INJECTION, RiskDirection.UNKNOWN),
        (RiskCategory.COORDINATED_MISUSE, RiskDirection.UNKNOWN),
    ],
}

# Additional tests by risk category
CATEGORY_TEST_MAP: Dict[RiskCategory, List[str]] = {
    RiskCategory.POLICY_EROSION: [
        "erosion_long_horizon_v2",
        "gradual_escalation_suite",
        "topic_drift_boundary",
    ],
    RiskCategory.INJECTION: [
        "injection_variants_full",
        "indirect_injection_suite",
        "tool_output_injection",
    ],
    RiskCategory.COORDINATED_MISUSE: [
        "decomposition_attacks_v3",
        "capability_accumulation",
        "roleplay_coordination",
    ],
    RiskCategory.TOOL_ABUSE: [
        "tool_chain_attacks",
        "hallucinated_tool_results",
        "unauthorized_tool_access",
    ],
    RiskCategory.FALSE_POSITIVE: [
        "benign_conversation_suite",
        "edge_case_legitimate",
        "multilingual_benign",
    ],
    RiskCategory.HEDGING_LEAKAGE: [
        "hedging_detection_suite",
        "partial_compliance_tests",
        "framing_attacks",
    ],
}


@dataclass
class ChangeImpactAnalyzer:
    """
    Analyzes changes and predicts risk shifts.

    Usage:
        analyzer = ChangeImpactAnalyzer()
        result = analyzer.analyze([
            ComponentChange(
                component="mid_trajectory_monitor",
                change_type="modified",
                files_changed=["safeguards/trajectory_monitor.py"],
                description="Lowered drift threshold from 0.5 to 0.4"
            )
        ])

        print(result.risk_shifts)
        print(result.required_additional_tests)
    """

    def analyze(self, changes: List[ComponentChange]) -> ImpactAnalysisResult:
        """
        Analyze changes and predict risk shifts.

        Args:
            changes: List of component changes to analyze

        Returns:
            ImpactAnalysisResult with predictions
        """
        risk_shifts = []
        required_tests: Set[str] = set()
        focus_areas: Set[str] = set()

        for change in changes:
            # Get risk categories affected by this component
            affected_risks = self._get_affected_risks(change)

            for category, base_direction in affected_risks:
                # Predict direction based on change type
                direction, confidence, reasoning = self._predict_direction(
                    change, category, base_direction
                )

                risk_shifts.append(RiskShift(
                    category=category,
                    direction=direction,
                    confidence=confidence,
                    reasoning=reasoning,
                    affected_metrics=self._get_affected_metrics(category),
                ))

                # Add required tests for this category
                if category in CATEGORY_TEST_MAP:
                    required_tests.update(CATEGORY_TEST_MAP[category])

                # Add focus area if risk might increase
                if direction in [RiskDirection.INCREASE, RiskDirection.UNKNOWN]:
                    focus_areas.add(category.value)

        # Generate overall assessment
        overall = self._generate_overall_assessment(risk_shifts)

        return ImpactAnalysisResult(
            changes=changes,
            risk_shifts=risk_shifts,
            required_additional_tests=sorted(list(required_tests)),
            recommended_focus_areas=sorted(list(focus_areas)),
            overall_risk_assessment=overall,
        )

    def _get_affected_risks(
        self,
        change: ComponentChange,
    ) -> List[Tuple[RiskCategory, RiskDirection]]:
        """Get risk categories affected by a component change."""

        # Direct component match
        if change.component in COMPONENT_RISK_MAP:
            return COMPONENT_RISK_MAP[change.component]

        # Fuzzy match based on file paths
        affected = []
        for component, risks in COMPONENT_RISK_MAP.items():
            for file_path in change.files_changed:
                if component.replace("_", "") in file_path.replace("_", "").lower():
                    affected.extend(risks)
                    break

        return affected if affected else [
            (RiskCategory.POLICY_EROSION, RiskDirection.UNKNOWN)
        ]

    def _predict_direction(
        self,
        change: ComponentChange,
        category: RiskCategory,
        base_direction: RiskDirection,
    ) -> Tuple[RiskDirection, float, str]:
        """Predict risk direction based on change details."""

        description_lower = change.description.lower()

        # Heuristic: threshold changes
        if "threshold" in description_lower:
            if "lower" in description_lower or "decrease" in description_lower:
                if category == RiskCategory.FALSE_POSITIVE:
                    return (
                        RiskDirection.INCREASE,
                        0.7,
                        "Lower thresholds typically increase false positive rate"
                    )
                else:
                    return (
                        RiskDirection.DECREASE,
                        0.7,
                        "Lower thresholds typically improve detection (more conservative)"
                    )
            elif "raise" in description_lower or "increase" in description_lower:
                if category == RiskCategory.FALSE_POSITIVE:
                    return (
                        RiskDirection.DECREASE,
                        0.7,
                        "Higher thresholds typically decrease false positive rate"
                    )
                else:
                    return (
                        RiskDirection.INCREASE,
                        0.7,
                        "Higher thresholds may miss more attacks (less conservative)"
                    )

        # Heuristic: removal
        if change.change_type == "removed":
            return (
                RiskDirection.INCREASE,
                0.8,
                f"Removal of {change.component} reduces defense coverage"
            )

        # Heuristic: addition
        if change.change_type == "added":
            return (
                RiskDirection.DECREASE,
                0.6,
                f"Addition of {change.component} may improve coverage"
            )

        # Default: unknown
        return (
            RiskDirection.UNKNOWN,
            0.4,
            f"Change to {change.component} has uncertain impact on {category.value}"
        )

    def _get_affected_metrics(self, category: RiskCategory) -> List[str]:
        """Get metrics affected by a risk category."""
        metric_map = {
            RiskCategory.POLICY_EROSION: ["erosion_slope", "avg_first_failure"],
            RiskCategory.INJECTION: ["injection_success_rate", "violation_rate"],
            RiskCategory.COORDINATED_MISUSE: ["coordinated_failure_rate", "delayed_failure_rate"],
            RiskCategory.TOOL_ABUSE: ["tool_abuse_rate", "unauthorized_access_rate"],
            RiskCategory.FALSE_POSITIVE: ["false_positive_rate", "benign_block_rate"],
            RiskCategory.HEDGING_LEAKAGE: ["hedging_rate", "partial_compliance_rate"],
        }
        return metric_map.get(category, [])

    def _generate_overall_assessment(self, risk_shifts: List[RiskShift]) -> str:
        """Generate overall risk assessment from shifts."""

        increases = [rs for rs in risk_shifts if rs.direction == RiskDirection.INCREASE]
        decreases = [rs for rs in risk_shifts if rs.direction == RiskDirection.DECREASE]
        unknowns = [rs for rs in risk_shifts if rs.direction == RiskDirection.UNKNOWN]

        if len(increases) > len(decreases):
            return f"ELEVATED: {len(increases)} risk categories may increase. Additional testing recommended."
        elif len(decreases) > len(increases):
            return f"IMPROVED: {len(decreases)} risk categories may decrease. Verify with standard suite."
        elif unknowns:
            return f"UNCERTAIN: {len(unknowns)} risk categories have unknown impact. Extended testing required."
        else:
            return "NEUTRAL: No significant risk shift predicted. Standard testing sufficient."


def analyze_git_diff(diff_output: str) -> List[ComponentChange]:
    """
    Parse git diff output into ComponentChange objects.

    This is a simplified parser. Production would use proper git diff parsing.
    """
    changes = []

    # Simple heuristic: look for modified files
    current_files = []
    for line in diff_output.split("\n"):
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 4:
                file_path = parts[3].lstrip("b/")
                current_files.append(file_path)

    if current_files:
        # Group files by likely component
        safeguard_files = [f for f in current_files if "safeguard" in f.lower()]
        policy_files = [f for f in current_files if "policy" in f.lower()]
        other_files = [f for f in current_files if f not in safeguard_files + policy_files]

        if safeguard_files:
            changes.append(ComponentChange(
                component="safeguards",
                change_type="modified",
                files_changed=safeguard_files,
                description="Safeguard logic modified"
            ))

        if policy_files:
            changes.append(ComponentChange(
                component="policy_dsl",
                change_type="modified",
                files_changed=policy_files,
                description="Policy configuration modified"
            ))

        if other_files:
            changes.append(ComponentChange(
                component="other",
                change_type="modified",
                files_changed=other_files,
                description="Other files modified"
            ))

    return changes
