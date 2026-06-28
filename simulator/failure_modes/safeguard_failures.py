"""
Safeguard Failure Modes: Model how safeguards themselves can fail.

Key insight: Safeguards are not magic. They can:
1. False positive (block legitimate requests)
2. False negative (miss harmful requests)
3. Cascade (one failure triggers others)
4. Loop (escalation creates infinite loops)
5. Degrade (performance decays over time)

This module explicitly models these failure modes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime


class FailureMode(Enum):
    """Types of safeguard failures."""
    FALSE_POSITIVE = "false_positive"       # Blocked legitimate request
    FALSE_NEGATIVE = "false_negative"       # Missed harmful request
    CASCADE = "cascade"                     # Failure triggered other failures
    ESCALATION_LOOP = "escalation_loop"     # Infinite escalation cycle
    TIMEOUT = "timeout"                     # Safeguard too slow
    DEGRADATION = "degradation"             # Performance decay
    INCONSISTENCY = "inconsistency"         # Different results on same input
    ADVERSARIAL_BYPASS = "adversarial_bypass"  # Deliberately evaded


@dataclass
class SafeguardFailure:
    """A single safeguard failure instance."""
    failure_id: str
    failure_mode: FailureMode
    safeguard_name: str
    severity: int  # 1-5

    # Context
    input_hash: str
    expected_output: str
    actual_output: str

    # Impact
    user_impact: str
    safety_impact: str

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)


class SafeguardFailureAnalyzer:
    """
    Analyze and model safeguard failure modes.

    Philosophy: If you only test that safeguards work,
    you miss how they fail. Failure mode analysis is essential.
    """

    def __init__(self):
        self.failures: List[SafeguardFailure] = []
        self.safeguard_stats: Dict[str, Dict] = {}

    def record_failure(
        self,
        failure_mode: FailureMode,
        safeguard_name: str,
        severity: int,
        input_hash: str,
        expected_output: str,
        actual_output: str,
        user_impact: str = "",
        safety_impact: str = "",
        metadata: Optional[Dict] = None
    ) -> SafeguardFailure:
        """Record a safeguard failure."""
        failure = SafeguardFailure(
            failure_id=f"fail_{len(self.failures):04d}",
            failure_mode=failure_mode,
            safeguard_name=safeguard_name,
            severity=severity,
            input_hash=input_hash,
            expected_output=expected_output,
            actual_output=actual_output,
            user_impact=user_impact,
            safety_impact=safety_impact,
            metadata=metadata or {}
        )

        self.failures.append(failure)
        self._update_stats(failure)
        return failure

    def _update_stats(self, failure: SafeguardFailure):
        """Update aggregate statistics."""
        name = failure.safeguard_name
        if name not in self.safeguard_stats:
            self.safeguard_stats[name] = {
                "total_failures": 0,
                "by_mode": {},
                "by_severity": {},
                "recent_failures": []
            }

        stats = self.safeguard_stats[name]
        stats["total_failures"] += 1

        mode = failure.failure_mode.value
        stats["by_mode"][mode] = stats["by_mode"].get(mode, 0) + 1

        sev = str(failure.severity)
        stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1

        # Keep last 10 failures
        stats["recent_failures"].append(failure.failure_id)
        stats["recent_failures"] = stats["recent_failures"][-10:]

    def detect_cascade(
        self,
        failures: List[SafeguardFailure],
        time_window_ms: float = 1000
    ) -> List[Dict]:
        """Detect cascading failures."""
        cascades = []

        # Sort by timestamp
        sorted_failures = sorted(failures, key=lambda f: f.timestamp)

        for i, f1 in enumerate(sorted_failures):
            cascade_chain = [f1]

            for f2 in sorted_failures[i+1:]:
                # Check if within time window
                t1 = datetime.fromisoformat(f1.timestamp)
                t2 = datetime.fromisoformat(f2.timestamp)
                delta_ms = (t2 - t1).total_seconds() * 1000

                if delta_ms <= time_window_ms:
                    cascade_chain.append(f2)
                else:
                    break

            if len(cascade_chain) > 1:
                cascades.append({
                    "trigger": cascade_chain[0].failure_id,
                    "chain": [f.failure_id for f in cascade_chain],
                    "length": len(cascade_chain),
                    "safeguards_affected": list(set(f.safeguard_name for f in cascade_chain))
                })

        return cascades

    def detect_escalation_loop(
        self,
        safeguard_name: str,
        max_escalations: int = 3
    ) -> Dict:
        """Detect potential escalation loops."""
        failures = [
            f for f in self.failures
            if f.safeguard_name == safeguard_name
        ]

        # Check for repeated escalations on same input
        by_input = {}
        for f in failures:
            if f.input_hash not in by_input:
                by_input[f.input_hash] = []
            by_input[f.input_hash].append(f)

        loops = []
        for input_hash, input_failures in by_input.items():
            if len(input_failures) > max_escalations:
                loops.append({
                    "input_hash": input_hash,
                    "escalation_count": len(input_failures),
                    "failure_ids": [f.failure_id for f in input_failures]
                })

        return {
            "safeguard": safeguard_name,
            "loops_detected": len(loops),
            "loops": loops,
            "recommendation": (
                "Review escalation logic to prevent infinite loops"
                if loops else "No escalation loops detected"
            )
        }

    def compute_failure_rates(self) -> Dict:
        """Compute failure rates by safeguard and mode."""
        rates = {}

        for safeguard, stats in self.safeguard_stats.items():
            total = stats["total_failures"]
            rates[safeguard] = {
                "total_failures": total,
                "by_mode": {
                    mode: count / total if total > 0 else 0
                    for mode, count in stats["by_mode"].items()
                },
                "dominant_failure_mode": (
                    max(stats["by_mode"].items(), key=lambda x: x[1])[0]
                    if stats["by_mode"] else None
                )
            }

        return rates

    def get_failure_taxonomy(self) -> Dict:
        """Get taxonomy of failure modes with examples."""
        taxonomy = {
            mode.value: {
                "description": self._get_mode_description(mode),
                "examples": [],
                "mitigation": self._get_mode_mitigation(mode),
                "count": 0
            }
            for mode in FailureMode
        }

        for failure in self.failures:
            mode = failure.failure_mode.value
            taxonomy[mode]["count"] += 1
            if len(taxonomy[mode]["examples"]) < 3:
                taxonomy[mode]["examples"].append({
                    "failure_id": failure.failure_id,
                    "safeguard": failure.safeguard_name,
                    "severity": failure.severity
                })

        return taxonomy

    def _get_mode_description(self, mode: FailureMode) -> str:
        """Get description of failure mode."""
        descriptions = {
            FailureMode.FALSE_POSITIVE: "Safeguard blocked a legitimate request",
            FailureMode.FALSE_NEGATIVE: "Safeguard missed a harmful request",
            FailureMode.CASCADE: "One safeguard failure triggered others",
            FailureMode.ESCALATION_LOOP: "Escalation created infinite loop",
            FailureMode.TIMEOUT: "Safeguard exceeded latency budget",
            FailureMode.DEGRADATION: "Safeguard performance decayed over time",
            FailureMode.INCONSISTENCY: "Same input produced different results",
            FailureMode.ADVERSARIAL_BYPASS: "Attacker deliberately evaded safeguard"
        }
        return descriptions.get(mode, "Unknown failure mode")

    def _get_mode_mitigation(self, mode: FailureMode) -> str:
        """Get mitigation strategy for failure mode."""
        mitigations = {
            FailureMode.FALSE_POSITIVE: "Add allowlist for common legitimate patterns",
            FailureMode.FALSE_NEGATIVE: "Increase classifier sensitivity, add red-team cases",
            FailureMode.CASCADE: "Add circuit breakers between safeguards",
            FailureMode.ESCALATION_LOOP: "Add loop detection with max escalation limit",
            FailureMode.TIMEOUT: "Add fallback policy for slow safeguards",
            FailureMode.DEGRADATION: "Monitor drift, retrain on schedule",
            FailureMode.INCONSISTENCY: "Reduce temperature, add determinism",
            FailureMode.ADVERSARIAL_BYPASS: "Red-team continuously, add adaptive defenses"
        }
        return mitigations.get(mode, "Review and analyze")

    def get_health_report(self) -> Dict:
        """Generate safeguard health report."""
        return {
            "total_failures": len(self.failures),
            "by_safeguard": self.compute_failure_rates(),
            "taxonomy": self.get_failure_taxonomy(),
            "cascades": self.detect_cascade(self.failures),
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations."""
        recs = []

        # Check for dominant failure modes
        for safeguard, stats in self.safeguard_stats.items():
            if stats["by_mode"]:
                dominant = max(stats["by_mode"].items(), key=lambda x: x[1])
                if dominant[1] > stats["total_failures"] * 0.5:
                    mode = FailureMode(dominant[0])
                    recs.append(
                        f"{safeguard}: Address {dominant[0]} failures ({dominant[1]} occurrences) - "
                        f"{self._get_mode_mitigation(mode)}"
                    )

        # Check for high-severity failures
        high_severity = [f for f in self.failures if f.severity >= 4]
        if high_severity:
            recs.append(
                f"URGENT: {len(high_severity)} high-severity failures require immediate review"
            )

        return recs


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    import hashlib

    analyzer = SafeguardFailureAnalyzer()

    # Simulate various failures
    failures_data = [
        (FailureMode.FALSE_POSITIVE, "intent_classifier", 2, "legitimate_query"),
        (FailureMode.FALSE_POSITIVE, "intent_classifier", 2, "legitimate_query_2"),
        (FailureMode.FALSE_NEGATIVE, "intent_classifier", 4, "harmful_query"),
        (FailureMode.FALSE_NEGATIVE, "output_filter", 3, "subtle_harm"),
        (FailureMode.CASCADE, "intent_classifier", 3, "cascade_trigger"),
        (FailureMode.CASCADE, "output_filter", 3, "cascade_trigger"),
        (FailureMode.ESCALATION_LOOP, "escalation_handler", 2, "loop_input"),
        (FailureMode.ESCALATION_LOOP, "escalation_handler", 2, "loop_input"),
        (FailureMode.ESCALATION_LOOP, "escalation_handler", 2, "loop_input"),
        (FailureMode.ESCALATION_LOOP, "escalation_handler", 2, "loop_input"),
        (FailureMode.TIMEOUT, "llm_judge", 2, "slow_query"),
        (FailureMode.ADVERSARIAL_BYPASS, "intent_classifier", 5, "adversarial_input"),
    ]

    for mode, safeguard, severity, input_str in failures_data:
        analyzer.record_failure(
            failure_mode=mode,
            safeguard_name=safeguard,
            severity=severity,
            input_hash=hashlib.md5(input_str.encode()).hexdigest()[:8],
            expected_output="block" if "harmful" in input_str else "allow",
            actual_output="allow" if mode == FailureMode.FALSE_NEGATIVE else "block",
            user_impact="Request blocked incorrectly" if mode == FailureMode.FALSE_POSITIVE else "",
            safety_impact="Harmful content passed" if mode == FailureMode.FALSE_NEGATIVE else ""
        )

    # Generate report
    report = analyzer.get_health_report()

    print("=== Safeguard Health Report ===")
    print(f"\nTotal Failures: {report['total_failures']}")

    print("\n=== By Safeguard ===")
    for safeguard, rates in report["by_safeguard"].items():
        print(f"\n{safeguard}:")
        print(f"  Total: {rates['total_failures']}")
        print(f"  Dominant mode: {rates['dominant_failure_mode']}")

    print("\n=== Failure Taxonomy ===")
    for mode, info in report["taxonomy"].items():
        if info["count"] > 0:
            print(f"\n{mode}: {info['count']} occurrences")
            print(f"  Description: {info['description']}")
            print(f"  Mitigation: {info['mitigation']}")

    # Check for escalation loops
    loop_check = analyzer.detect_escalation_loop("escalation_handler", max_escalations=3)
    print("\n=== Escalation Loops ===")
    print(f"Loops detected: {loop_check['loops_detected']}")
    print(f"Recommendation: {loop_check['recommendation']}")

    print("\n=== Recommendations ===")
    for rec in report["recommendations"]:
        print(f"- {rec}")
