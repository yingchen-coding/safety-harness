"""
Pre-action safeguards - Check before tool execution.
"""

import re

from .base import BaseSafeguard, SafeguardResult, SafeguardLevel
from agent.planner import Action
from agent.memory import Memory


class IntentClassifier(BaseSafeguard):
    """
    Classifies user intent before action execution.

    Detects:
    - Malicious intent indicators
    - High-risk action requests
    - Injection attempts
    """

    name = "intent_classifier"
    description = "Pre-action intent classification"

    # Suspicious patterns
    MALICIOUS_PATTERNS = [
        r"bypass\s+(safety|security|filter|moderation)",
        r"ignore\s+(previous|prior|safety|guidelines)",
        r"(hack|exploit|attack|breach)\s+",
        r"(disable|remove)\s+(safety|filter|restriction)",
        r"pretend\s+(you\s+are|to\s+be)",
    ]

    HIGH_RISK_KEYWORDS = [
        "password", "credential", "secret", "private",
        "hack", "exploit", "vulnerability", "bypass",
        "injection", "malware", "virus", "attack"
    ]

    def __init__(self, sensitivity: float = 0.5):
        super().__init__(sensitivity)
        self.compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.MALICIOUS_PATTERNS
        ]

    def check(self, action: Action, memory: Memory) -> SafeguardResult:
        """Check action intent before execution."""
        # Get context
        context = memory.get_conversation_context()
        action_text = f"{action.description} {action.parameters}"

        # Check for malicious patterns
        malicious_score = self._check_malicious_patterns(context + action_text)

        # Check for high-risk keywords
        risk_score = self._check_risk_keywords(context + action_text)

        # Check action risk level
        action_risk = action.risk_level

        # Combined score
        combined_score = 0.4 * malicious_score + 0.3 * risk_score + 0.3 * action_risk

        # Determine level
        soft_threshold = self.adjust_threshold(0.4)
        hard_threshold = self.adjust_threshold(0.7)

        if combined_score >= hard_threshold:
            level = SafeguardLevel.HARD_STOP
            reason = "High-risk intent detected"
        elif combined_score >= soft_threshold:
            level = SafeguardLevel.SOFT_STOP
            reason = "Potentially risky intent"
        elif combined_score >= 0.2:
            level = SafeguardLevel.WARN
            reason = "Minor risk indicators"
        else:
            level = SafeguardLevel.PASS
            reason = "Intent appears benign"

        return SafeguardResult(
            level=level,
            score=combined_score,
            reason=reason,
            details={
                "malicious_score": malicious_score,
                "risk_score": risk_score,
                "action_risk": action_risk,
                "intent": "benign" if combined_score < 0.3 else "suspicious"
            }
        )

    def _check_malicious_patterns(self, text: str) -> float:
        """Check for malicious patterns in text."""
        matches = sum(1 for p in self.compiled_patterns if p.search(text))
        return min(matches / 3, 1.0)

    def _check_risk_keywords(self, text: str) -> float:
        """Check for high-risk keywords."""
        text_lower = text.lower()
        matches = sum(1 for kw in self.HIGH_RISK_KEYWORDS if kw in text_lower)
        return min(matches / 5, 1.0)


class InjectionDetector(BaseSafeguard):
    """
    Detects prompt injection attempts before action execution.
    """

    name = "injection_detector"
    description = "Pre-action injection detection"

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"new\s+instructions?\s*:",
        r"system\s*prompt\s*:",
        r"---\s*end\s*(of)?\s*(text|input)",
        r"admin(istrator)?\s+override",
    ]

    def __init__(self, sensitivity: float = 0.5):
        super().__init__(sensitivity)
        self.compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS
        ]

    def check(self, action: Action, memory: Memory) -> SafeguardResult:
        """Check for injection attempts."""
        context = memory.get_conversation_context()

        matches = []
        for pattern in self.compiled_patterns:
            if pattern.search(context):
                matches.append(pattern.pattern)

        if matches:
            score = min(len(matches) / 2, 1.0)
            return SafeguardResult(
                level=SafeguardLevel.HARD_STOP,
                score=score,
                reason="Injection attempt detected",
                details={"patterns_matched": matches}
            )

        return SafeguardResult(
            level=SafeguardLevel.PASS,
            score=0.0,
            reason="No injection detected"
        )


def create_pre_action_hook(sensitivity: float = 0.5):
    """Create a pre-action hook combining multiple safeguards."""
    intent_classifier = IntentClassifier(sensitivity)
    injection_detector = InjectionDetector(sensitivity)

    def hook(action: Action, memory: Memory) -> dict:
        # Run both checks
        intent_result = intent_classifier.check(action, memory)
        injection_result = injection_detector.check(action, memory)

        # Take the more severe result
        if injection_result.level.value > intent_result.level.value:
            primary = injection_result
        else:
            primary = intent_result

        return primary.to_dict()

    return hook
