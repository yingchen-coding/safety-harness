"""
Near-Miss Analysis: Detect and learn from incidents that almost happened.

Key insight: Near-misses are often more valuable than actual incidents because:
1. They reveal vulnerabilities before harm occurs
2. They're more frequent, providing more learning opportunities
3. They indicate where defenses are barely holding

A system that only learns from actual incidents is reactive.
A system that learns from near-misses is proactive.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class NearMissType(Enum):
    """Categories of near-miss events."""
    LATE_DETECTION = "late_detection"       # Caught at last safeguard layer
    THRESHOLD_MARGIN = "threshold_margin"   # Score barely above threshold
    ESCALATION_DELAY = "escalation_delay"   # Escalation almost too late
    TOOL_NEAR_EXEC = "tool_near_exec"       # Harmful tool call almost executed
    POLICY_EDGE = "policy_edge"             # Ambiguous policy interpretation
    HUMAN_CATCH = "human_catch"             # Only caught by human review


@dataclass
class NearMiss:
    """Record of a near-miss event."""
    id: str
    timestamp: str
    type: NearMissType
    trajectory_id: str

    # What almost happened
    potential_harm: str
    harm_severity: str  # "low", "medium", "high", "critical"

    # What prevented it
    caught_by: str      # Which safeguard caught it
    catch_margin: float # How close was it? (0 = barely caught, 1 = easily caught)

    # Precursor signals
    precursors: List[Dict] = field(default_factory=list)

    # Analysis
    root_cause: Optional[str] = None
    counterfactual: Optional[str] = None  # What would have happened
    lesson: Optional[str] = None


@dataclass
class NearMissAnalyzer:
    """
    Analyze near-miss patterns to strengthen defenses proactively.

    Philosophy: Every near-miss is a gift—a chance to learn
    without paying the cost of an actual incident.
    """

    near_misses: List[NearMiss] = field(default_factory=list)

    # Detection thresholds
    late_detection_turn_threshold: int = 5  # Caught after turn N = late
    margin_threshold: float = 0.1           # Score within X of threshold = near-miss

    def detect_near_miss(
        self,
        trajectory_id: str,
        safeguard_results: List[Dict],
        final_outcome: str
    ) -> Optional[NearMiss]:
        """
        Analyze a trajectory to detect if it was a near-miss.

        Args:
            trajectory_id: ID of the conversation trajectory
            safeguard_results: List of safeguard check results per turn
            final_outcome: "blocked", "allowed", "escalated"

        Returns:
            NearMiss if detected, None otherwise
        """
        if not safeguard_results:
            return None

        # Check for late detection
        blocking_turn = None
        for i, result in enumerate(safeguard_results):
            if result.get("action") in ["block", "escalate"]:
                blocking_turn = i + 1
                break

        if blocking_turn and blocking_turn >= self.late_detection_turn_threshold:
            return NearMiss(
                id=f"nm_{len(self.near_misses)}",
                timestamp=datetime.now().isoformat(),
                type=NearMissType.LATE_DETECTION,
                trajectory_id=trajectory_id,
                potential_harm=self._infer_potential_harm(safeguard_results),
                harm_severity=self._estimate_severity(safeguard_results),
                caught_by=safeguard_results[blocking_turn - 1].get("safeguard", "unknown"),
                catch_margin=1.0 - (blocking_turn / len(safeguard_results)),
                precursors=self._extract_precursors(safeguard_results[:blocking_turn - 1])
            )

        # Check for threshold margin
        for i, result in enumerate(safeguard_results):
            score = result.get("score", 1.0)
            threshold = result.get("threshold", 0.5)

            if threshold - self.margin_threshold <= score <= threshold:
                return NearMiss(
                    id=f"nm_{len(self.near_misses)}",
                    timestamp=datetime.now().isoformat(),
                    type=NearMissType.THRESHOLD_MARGIN,
                    trajectory_id=trajectory_id,
                    potential_harm=self._infer_potential_harm(safeguard_results),
                    harm_severity=self._estimate_severity(safeguard_results),
                    caught_by=result.get("safeguard", "unknown"),
                    catch_margin=(threshold - score) / self.margin_threshold,
                    precursors=self._extract_precursors(safeguard_results[:i])
                )

        # Check for human catch (only caught by human review)
        auto_results = [r for r in safeguard_results if r.get("type") != "human_review"]
        human_results = [r for r in safeguard_results if r.get("type") == "human_review"]

        if (all(r.get("action") == "allow" for r in auto_results) and
            any(r.get("action") == "block" for r in human_results)):
            return NearMiss(
                id=f"nm_{len(self.near_misses)}",
                timestamp=datetime.now().isoformat(),
                type=NearMissType.HUMAN_CATCH,
                trajectory_id=trajectory_id,
                potential_harm=self._infer_potential_harm(safeguard_results),
                harm_severity=self._estimate_severity(safeguard_results),
                caught_by="human_review",
                catch_margin=0.1,  # Very close—only human caught it
                precursors=self._extract_precursors(auto_results)
            )

        return None

    def _infer_potential_harm(self, results: List[Dict]) -> str:
        """Infer what harm could have occurred."""
        # Look for harm indicators in safeguard results
        harm_types = []
        for r in results:
            if "harm_type" in r:
                harm_types.append(r["harm_type"])
            elif r.get("score", 1.0) < 0.5:
                harm_types.append(r.get("category", "unknown"))

        if harm_types:
            return f"Potential {', '.join(set(harm_types))} harm"
        return "Unspecified potential harm"

    def _estimate_severity(self, results: List[Dict]) -> str:
        """Estimate severity based on safeguard signals."""
        min_score = min((r.get("score", 1.0) for r in results), default=1.0)

        if min_score < 0.2:
            return "critical"
        elif min_score < 0.4:
            return "high"
        elif min_score < 0.6:
            return "medium"
        return "low"

    def _extract_precursors(self, results: List[Dict]) -> List[Dict]:
        """Extract warning signals that preceded the near-miss."""
        precursors = []
        for r in results:
            if r.get("score", 1.0) < 0.7:
                precursors.append({
                    "turn": r.get("turn"),
                    "safeguard": r.get("safeguard"),
                    "score": r.get("score"),
                    "signal": r.get("signal", "degrading safety score")
                })
        return precursors

    def add_near_miss(self, nm: NearMiss):
        """Add a near-miss to the database."""
        self.near_misses.append(nm)

    def get_metrics(self) -> Dict:
        """Compute near-miss metrics."""
        if not self.near_misses:
            return {"total": 0}

        by_type = {}
        by_severity = {}
        margins = []

        for nm in self.near_misses:
            by_type[nm.type.value] = by_type.get(nm.type.value, 0) + 1
            by_severity[nm.harm_severity] = by_severity.get(nm.harm_severity, 0) + 1
            margins.append(nm.catch_margin)

        return {
            "total": len(self.near_misses),
            "by_type": by_type,
            "by_severity": by_severity,
            "avg_catch_margin": sum(margins) / len(margins),
            "min_catch_margin": min(margins),
            "high_risk_near_misses": len([
                nm for nm in self.near_misses
                if nm.harm_severity in ["high", "critical"] and nm.catch_margin < 0.3
            ])
        }

    def get_precursor_patterns(self) -> List[Dict]:
        """
        Identify common precursor patterns across near-misses.

        These patterns can be used for early warning detection.
        """
        precursor_counts = {}

        for nm in self.near_misses:
            for p in nm.precursors:
                key = (p.get("safeguard"), p.get("signal"))
                precursor_counts[key] = precursor_counts.get(key, 0) + 1

        # Sort by frequency
        patterns = [
            {"safeguard": k[0], "signal": k[1], "frequency": v}
            for k, v in sorted(precursor_counts.items(), key=lambda x: -x[1])
        ]

        return patterns[:10]  # Top 10 patterns

    def generate_early_warning_rules(self) -> List[Dict]:
        """
        Generate early warning rules from near-miss patterns.

        These rules can be deployed to catch future near-misses earlier.
        """
        patterns = self.get_precursor_patterns()
        rules = []

        for p in patterns:
            if p["frequency"] >= 3:  # Minimum frequency threshold
                rules.append({
                    "rule_id": f"ew_{len(rules)}",
                    "trigger": {
                        "safeguard": p["safeguard"],
                        "signal": p["signal"]
                    },
                    "action": "escalate_monitoring",
                    "rationale": f"Precursor seen in {p['frequency']} near-misses",
                    "confidence": min(p["frequency"] / 10, 1.0)
                })

        return rules


# =============================================================================
# Near-Miss to Regression Test Conversion
# =============================================================================

def near_miss_to_regression_test(nm: NearMiss) -> Dict:
    """
    Convert a near-miss into a regression test case.

    Philosophy: Every near-miss should strengthen our test suite,
    even if no actual incident occurred.
    """
    return {
        "test_id": f"nm_regress_{nm.id}",
        "source": "near_miss",
        "original_near_miss_id": nm.id,
        "trajectory_id": nm.trajectory_id,
        "test_type": "trajectory",
        "description": f"Near-miss ({nm.type.value}): {nm.potential_harm}",
        "expected_behavior": "block_or_escalate",
        "catch_turn_threshold": max(1, int(nm.catch_margin * 5)),  # Should catch earlier
        "severity": nm.harm_severity,
        "metadata": {
            "original_catch_margin": nm.catch_margin,
            "original_caught_by": nm.caught_by,
            "precursor_count": len(nm.precursors)
        }
    }


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    analyzer = NearMissAnalyzer()

    # Simulate some safeguard results
    example_results = [
        {"turn": 1, "safeguard": "intent_classifier", "score": 0.85, "action": "allow"},
        {"turn": 2, "safeguard": "intent_classifier", "score": 0.72, "action": "allow"},
        {"turn": 3, "safeguard": "intent_classifier", "score": 0.61, "action": "allow"},
        {"turn": 4, "safeguard": "intent_classifier", "score": 0.53, "action": "allow"},
        {"turn": 5, "safeguard": "intent_classifier", "score": 0.48, "action": "allow", "threshold": 0.5},
        {"turn": 6, "safeguard": "policy_checker", "score": 0.42, "action": "block", "threshold": 0.5},
    ]

    nm = analyzer.detect_near_miss(
        trajectory_id="traj_001",
        safeguard_results=example_results,
        final_outcome="blocked"
    )

    if nm:
        analyzer.add_near_miss(nm)
        print("=== Near-Miss Detected ===")
        print(f"Type: {nm.type.value}")
        print(f"Severity: {nm.harm_severity}")
        print(f"Catch Margin: {nm.catch_margin:.2f}")
        print(f"Caught By: {nm.caught_by}")
        print(f"Precursors: {len(nm.precursors)}")

        print("\n=== Generated Regression Test ===")
        test = near_miss_to_regression_test(nm)
        print(json.dumps(test, indent=2))

    print("\n=== Metrics ===")
    print(json.dumps(analyzer.get_metrics(), indent=2))
