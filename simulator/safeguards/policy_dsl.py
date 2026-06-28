"""
Policy DSL - Declarative Safety Rules
=====================================

This module provides a lightweight rule engine for defining safety policies
declaratively. Policies are loaded from YAML, not hard-coded.

Design Philosophy:
- Separation of policy definition from enforcement
- Policies can be updated without code changes
- Human-readable rule format
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import operator

from .api import Decision, GuardContext, GuardDecision


@dataclass
class PolicyRule:
    """A single policy rule."""
    name: str
    condition: str
    action: Decision
    reason: str
    priority: int = 0


class PolicyEngine:
    """
    Evaluates declarative policy rules against context.

    Example policy.yaml:
    ```yaml
    rules:
      - name: high_drift_block
        when: drift_score > 0.5
        action: HARD_STOP
        reason: "Trajectory drift beyond threshold"
        priority: 10

      - name: risky_tool_confirm
        when: tool_risk == "high" and uncertainty < 0.6
        action: SOFT_STOP
        reason: "High-risk tool with low confidence"
        priority: 5
    ```
    """

    def __init__(self):
        self.rules: List[PolicyRule] = []

    def load_from_yaml(self, path: str) -> None:
        """Load policy rules from YAML file.

        PyYAML is imported lazily so the engine itself stays stdlib-only — yaml is only
        required if you actually load policy from a YAML file (load_from_dict needs nothing).
        """
        import yaml

        with open(path, 'r') as f:
            config = yaml.safe_load(f)

        self.rules = []
        for rule_config in config.get('rules', []):
            self.rules.append(PolicyRule(
                name=rule_config['name'],
                condition=rule_config['when'],
                action=Decision[rule_config['action']],
                reason=rule_config['reason'],
                priority=rule_config.get('priority', 0)
            ))

        # Sort by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def load_from_dict(self, rules: List[Dict]) -> None:
        """Load policy rules from dictionary."""
        self.rules = []
        for rule_config in rules:
            self.rules.append(PolicyRule(
                name=rule_config['name'],
                condition=rule_config['when'],
                action=Decision[rule_config['action']],
                reason=rule_config['reason'],
                priority=rule_config.get('priority', 0)
            ))
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def evaluate(self, ctx: GuardContext, features: Dict[str, Any]) -> GuardDecision:
        """
        Evaluate all rules against current context and features.

        Args:
            ctx: Guard context with conversation state
            features: Computed features (drift_score, tool_risk, etc.)

        Returns:
            GuardDecision from highest-priority matching rule
        """
        # Build evaluation namespace
        namespace = {
            'drift_score': ctx.cumulative_drift,
            'violation_count': ctx.violation_count,
            'step': ctx.step,
            **features
        }

        # Evaluate rules in priority order
        for rule in self.rules:
            if self._evaluate_condition(rule.condition, namespace):
                return GuardDecision(
                    decision=rule.action,
                    confidence=0.9,
                    reason=rule.reason,
                    features={'matched_rule': rule.name, **namespace}
                )

        # No rule matched - proceed
        return GuardDecision(
            decision=Decision.PROCEED,
            confidence=1.0,
            reason="No policy rule triggered",
            features=namespace
        )

    def _evaluate_condition(self, condition: str, namespace: Dict[str, Any]) -> bool:
        """
        Evaluate a condition string against namespace.

        Supports:
        - Comparisons: >, <, >=, <=, ==, !=
        - Logical: and, or, not
        - String equality: == "value"
        """
        # Safe evaluation with limited operators
        ops = {
            '>': operator.gt,
            '<': operator.lt,
            '>=': operator.ge,
            '<=': operator.le,
            '==': operator.eq,
            '!=': operator.ne,
        }

        try:
            # Parse simple conditions like "drift_score > 0.5".
            # For production, use a proper expression parser.
            #
            # Logical operators are split on word boundaries (" or " / " and ") so they do NOT
            # corrupt identifiers that merely contain the substrings "or"/"and" — e.g. the
            # feature name "drift_score" contains "or". OR has the lowest precedence, then AND,
            # then a leaf comparison.
            condition = condition.strip()

            if " or " in condition:
                return any(
                    self._evaluate_condition(c, namespace)
                    for c in condition.split(" or ")
                )

            if " and " in condition:
                return all(
                    self._evaluate_condition(c, namespace)
                    for c in condition.split(" and ")
                )

            # Leaf comparison: "left op right"
            parts = condition.split()
            if len(parts) == 3:
                left, op, right = parts
                if op not in ops:
                    return False
                left_val = namespace.get(left, self._parse_value(left, namespace))
                right_val = self._parse_value(right, namespace)
                try:
                    return bool(ops[op](left_val, right_val))
                except TypeError:
                    # Mismatched types (e.g. comparing a string to a number) never match.
                    return False

            return False

        except Exception:
            # Fail safe - don't match if condition parsing fails
            return False

    def _parse_value(self, value: str, namespace: Dict[str, Any]) -> Any:
        """Parse a value string to appropriate type."""
        # Remove quotes for string literals
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]

        # Try numeric
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Check namespace
        if value in namespace:
            return namespace[value]

        return value


# Default policy rules
DEFAULT_POLICY = [
    {
        "name": "high_drift_block",
        "when": "drift_score > 0.5",
        "action": "HARD_STOP",
        "reason": "Trajectory drift beyond safety threshold",
        "priority": 10
    },
    {
        "name": "moderate_drift_warn",
        "when": "drift_score > 0.3",
        "action": "SOFT_STOP",
        "reason": "Trajectory drift approaching threshold - requesting clarification",
        "priority": 5
    },
    {
        "name": "violation_block",
        "when": "violation_count > 0",
        "action": "HARD_STOP",
        "reason": "Policy violation detected",
        "priority": 15
    },
    {
        "name": "high_risk_tool",
        "when": "tool_risk == 'high'",
        "action": "SOFT_STOP",
        "reason": "High-risk tool usage requires confirmation",
        "priority": 8
    }
]
