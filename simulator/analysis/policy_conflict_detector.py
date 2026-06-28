"""
Policy Conflict Detector

Detects conflicts, redundancies, and gaps between safeguard policies.

Key Questions:
1. Does policy A override policy B in unexpected ways?
2. Are there scenarios where multiple policies fire but disagree?
3. Are there coverage gaps where no policy fires?
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class ConflictType(Enum):
    """Types of policy conflicts."""
    OVERRIDE = "override"           # Policy A overrides Policy B
    CONTRADICTION = "contradiction" # Policies disagree on action
    REDUNDANCY = "redundancy"       # Multiple policies do same thing
    GAP = "gap"                     # No policy covers scenario
    ORDERING = "ordering"           # Result depends on evaluation order


class ConflictSeverity(Enum):
    """Severity of detected conflicts."""
    CRITICAL = "critical"   # Could cause safety bypass
    HIGH = "high"           # Unexpected behavior likely
    MEDIUM = "medium"       # Suboptimal but not dangerous
    LOW = "low"             # Minor inefficiency


@dataclass
class PolicyConflict:
    """A detected conflict between policies."""
    conflict_type: ConflictType
    severity: ConflictSeverity
    policies_involved: List[str]
    scenario: str
    description: str
    recommendation: str


@dataclass
class PolicyRule:
    """A single policy rule."""
    id: str
    name: str
    layer: str  # pre_action, mid_trajectory, post_action
    condition: str  # Condition expression
    action: str  # block, warn, allow, escalate
    priority: int


@dataclass
class PolicyConflictDetector:
    """
    Detects conflicts between safeguard policies.

    Usage:
        detector = PolicyConflictDetector()
        conflicts = detector.analyze([
            PolicyRule(id="r1", name="block_injection", layer="pre_action",
                      condition="injection_score > 0.8", action="block", priority=1),
            PolicyRule(id="r2", name="allow_research", layer="pre_action",
                      condition="topic == 'security_research'", action="allow", priority=2),
        ])

        for conflict in conflicts:
            print(f"{conflict.severity}: {conflict.description}")
    """

    def analyze(self, policies: List[PolicyRule]) -> List[PolicyConflict]:
        """
        Analyze policies for conflicts.

        Args:
            policies: List of policy rules to analyze

        Returns:
            List of detected conflicts
        """
        conflicts = []

        # Check for override conflicts
        conflicts.extend(self._check_overrides(policies))

        # Check for contradictions
        conflicts.extend(self._check_contradictions(policies))

        # Check for redundancies
        conflicts.extend(self._check_redundancies(policies))

        # Check for ordering dependencies
        conflicts.extend(self._check_ordering(policies))

        # Sort by severity
        severity_order = {
            ConflictSeverity.CRITICAL: 0,
            ConflictSeverity.HIGH: 1,
            ConflictSeverity.MEDIUM: 2,
            ConflictSeverity.LOW: 3,
        }
        conflicts.sort(key=lambda c: severity_order[c.severity])

        return conflicts

    def _check_overrides(self, policies: List[PolicyRule]) -> List[PolicyConflict]:
        """Check for policies that override each other."""
        conflicts = []

        # Group by layer
        by_layer = self._group_by_layer(policies)

        for layer, layer_policies in by_layer.items():
            # Sort by priority
            sorted_policies = sorted(layer_policies, key=lambda p: p.priority)

            for i, policy_a in enumerate(sorted_policies):
                for policy_b in sorted_policies[i+1:]:
                    # Check if conditions could overlap
                    overlap = self._conditions_overlap(
                        policy_a.condition, policy_b.condition
                    )

                    if overlap and policy_a.action != policy_b.action:
                        # Higher priority wins - is this intentional?
                        severity = (
                            ConflictSeverity.CRITICAL
                            if policy_a.action == "allow" and policy_b.action == "block"
                            else ConflictSeverity.HIGH
                        )

                        conflicts.append(PolicyConflict(
                            conflict_type=ConflictType.OVERRIDE,
                            severity=severity,
                            policies_involved=[policy_a.id, policy_b.id],
                            scenario=f"When both {policy_a.condition} AND {policy_b.condition}",
                            description=(
                                f"Policy '{policy_a.name}' (priority {policy_a.priority}, action={policy_a.action}) "
                                f"overrides '{policy_b.name}' (priority {policy_b.priority}, action={policy_b.action})"
                            ),
                            recommendation=(
                                f"Verify override is intentional. If {policy_a.action} should not override {policy_b.action}, "
                                f"adjust priorities or add exclusion condition."
                            ),
                        ))

        return conflicts

    def _check_contradictions(self, policies: List[PolicyRule]) -> List[PolicyConflict]:
        """Check for policies that contradict each other."""
        conflicts = []

        # Cross-layer contradictions (e.g., pre allows, mid blocks)
        by_layer = self._group_by_layer(policies)

        layers = ["pre_action", "mid_trajectory", "post_action"]
        for i, layer_a in enumerate(layers):
            for layer_b in layers[i+1:]:
                policies_a = by_layer.get(layer_a, [])
                policies_b = by_layer.get(layer_b, [])

                for pa in policies_a:
                    for pb in policies_b:
                        if self._conditions_overlap(pa.condition, pb.condition):
                            if pa.action == "allow" and pb.action == "block":
                                conflicts.append(PolicyConflict(
                                    conflict_type=ConflictType.CONTRADICTION,
                                    severity=ConflictSeverity.HIGH,
                                    policies_involved=[pa.id, pb.id],
                                    scenario=f"When {pa.condition} triggers",
                                    description=(
                                        f"{layer_a} policy '{pa.name}' allows, "
                                        f"but {layer_b} policy '{pb.name}' blocks"
                                    ),
                                    recommendation=(
                                        "Cross-layer contradiction detected. "
                                        "Later layers blocking what earlier layers allowed "
                                        "may indicate policy drift or inconsistent design."
                                    ),
                                ))

        return conflicts

    def _check_redundancies(self, policies: List[PolicyRule]) -> List[PolicyConflict]:
        """Check for redundant policies."""
        conflicts = []

        by_layer = self._group_by_layer(policies)

        for layer, layer_policies in by_layer.items():
            for i, pa in enumerate(layer_policies):
                for pb in layer_policies[i+1:]:
                    if pa.action == pb.action:
                        if self._condition_subsumes(pa.condition, pb.condition):
                            conflicts.append(PolicyConflict(
                                conflict_type=ConflictType.REDUNDANCY,
                                severity=ConflictSeverity.LOW,
                                policies_involved=[pa.id, pb.id],
                                scenario=f"When {pb.condition}",
                                description=(
                                    f"Policy '{pb.name}' is redundant with '{pa.name}' "
                                    f"(both {pa.action} on overlapping conditions)"
                                ),
                                recommendation=(
                                    "Consider consolidating into single policy "
                                    "to reduce complexity and maintenance burden."
                                ),
                            ))

        return conflicts

    def _check_ordering(self, policies: List[PolicyRule]) -> List[PolicyConflict]:
        """Check for order-dependent policy evaluation."""
        conflicts = []

        by_layer = self._group_by_layer(policies)

        for layer, layer_policies in by_layer.items():
            # Find policies with same priority
            by_priority: Dict[int, List[PolicyRule]] = {}
            for p in layer_policies:
                if p.priority not in by_priority:
                    by_priority[p.priority] = []
                by_priority[p.priority].append(p)

            for priority, same_priority in by_priority.items():
                if len(same_priority) > 1:
                    # Multiple policies at same priority with overlapping conditions
                    for i, pa in enumerate(same_priority):
                        for pb in same_priority[i+1:]:
                            if self._conditions_overlap(pa.condition, pb.condition):
                                if pa.action != pb.action:
                                    conflicts.append(PolicyConflict(
                                        conflict_type=ConflictType.ORDERING,
                                        severity=ConflictSeverity.MEDIUM,
                                        policies_involved=[pa.id, pb.id],
                                        scenario=f"When both conditions match at priority {priority}",
                                        description=(
                                            f"Policies '{pa.name}' and '{pb.name}' have same priority "
                                            f"but different actions ({pa.action} vs {pb.action}). "
                                            f"Result depends on evaluation order."
                                        ),
                                        recommendation=(
                                            "Assign different priorities or add mutual exclusion "
                                            "to ensure deterministic behavior."
                                        ),
                                    ))

        return conflicts

    def _group_by_layer(self, policies: List[PolicyRule]) -> Dict[str, List[PolicyRule]]:
        """Group policies by layer."""
        result: Dict[str, List[PolicyRule]] = {}
        for p in policies:
            if p.layer not in result:
                result[p.layer] = []
            result[p.layer].append(p)
        return result

    def _conditions_overlap(self, cond_a: str, cond_b: str) -> bool:
        """
        Check if two conditions could both be true simultaneously.

        This is a simplified heuristic. Production would use SMT solver.
        """
        # Simple heuristic: if they share variables, assume potential overlap
        vars_a = set(cond_a.replace("(", " ").replace(")", " ").replace(">", " ").replace("<", " ").replace("=", " ").split())
        vars_b = set(cond_b.replace("(", " ").replace(")", " ").replace(">", " ").replace("<", " ").replace("=", " ").split())

        # Remove common operators and literals
        operators = {"and", "or", "not", "true", "false", "0", "1"}
        vars_a -= operators
        vars_b -= operators

        # If they share any variables, consider potential overlap
        return bool(vars_a & vars_b)

    def _condition_subsumes(self, cond_a: str, cond_b: str) -> bool:
        """
        Check if condition A subsumes condition B (A is more general).

        Simplified heuristic.
        """
        # If A's variables are subset of B's, A might be more general
        vars_a = set(cond_a.split())
        vars_b = set(cond_b.split())
        return vars_a.issubset(vars_b) and len(vars_a) < len(vars_b)

    def generate_report(self, conflicts: List[PolicyConflict]) -> str:
        """Generate human-readable conflict report."""

        lines = [
            "# Policy Conflict Analysis Report",
            "",
            f"**Total conflicts detected**: {len(conflicts)}",
            "",
        ]

        # Summary by severity
        by_severity = {}
        for c in conflicts:
            if c.severity not in by_severity:
                by_severity[c.severity] = []
            by_severity[c.severity].append(c)

        lines.append("## Summary by Severity")
        lines.append("")
        for severity in ConflictSeverity:
            count = len(by_severity.get(severity, []))
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            lines.append(f"- {emoji.get(severity.value, '')} {severity.value.upper()}: {count}")
        lines.append("")

        # Details
        lines.append("## Conflict Details")
        lines.append("")

        for i, conflict in enumerate(conflicts, 1):
            lines.extend([
                f"### {i}. [{conflict.severity.value.upper()}] {conflict.conflict_type.value}",
                "",
                f"**Policies**: {', '.join(conflict.policies_involved)}",
                "",
                f"**Scenario**: {conflict.scenario}",
                "",
                f"**Issue**: {conflict.description}",
                "",
                f"**Recommendation**: {conflict.recommendation}",
                "",
                "---",
                "",
            ])

        return "\n".join(lines)
