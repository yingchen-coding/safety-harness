"""
Regression Test Decay: Manage test relevance over time.

Key insight: Regression tests decay in value over time:
1. Attack patterns evolve, old tests become less representative
2. Model architecture changes make old failure modes irrelevant
3. Test suite bloat slows CI and causes alert fatigue

A healthy test suite actively retires stale tests while
ensuring critical coverage is maintained.
"""

import json
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class RetirementReason(Enum):
    """Reasons for retiring a regression test."""
    LOW_RELEVANCE = "low_relevance"         # Hasn't triggered in a long time
    SUPERSEDED = "superseded"               # Covered by newer, better test
    FALSE_POSITIVE_PRONE = "fp_prone"       # High FP rate, low signal
    ARCHITECTURE_OBSOLETE = "arch_obsolete" # Tests old model architecture
    COVERAGE_REDUNDANT = "redundant"        # Covered by other tests


@dataclass
class RegressionTest:
    """A regression test with decay tracking."""
    test_id: str
    created_at: str
    source: str  # "incident", "near_miss", "red_team", "manual"

    # Trigger history
    last_triggered: Optional[str] = None
    trigger_count: int = 0
    last_result: Optional[str] = None  # "pass", "fail", "skip"

    # Coverage metadata
    failure_mode: str = ""
    severity: str = "medium"
    coverage_tags: List[str] = field(default_factory=list)

    # Decay tracking
    relevance_score: float = 1.0
    retirement_reason: Optional[RetirementReason] = None
    retired_at: Optional[str] = None


class RegressionDecayManager:
    """
    Manage regression test lifecycle and decay.

    Philosophy: Tests are investments. Like all investments, they
    depreciate over time and must be actively managed.
    """

    def __init__(
        self,
        half_life_days: int = 90,
        retirement_threshold: float = 0.1,
        min_triggers_for_retirement: int = 5
    ):
        """
        Args:
            half_life_days: Days after which test relevance halves
            retirement_threshold: Retire tests below this relevance
            min_triggers_for_retirement: Minimum triggers before eligible for retirement
        """
        self.half_life = half_life_days
        self.retirement_threshold = retirement_threshold
        self.min_triggers = min_triggers_for_retirement
        self.tests: Dict[str, RegressionTest] = {}

    def add_test(self, test: RegressionTest):
        """Add a test to the registry."""
        self.tests[test.test_id] = test

    def compute_relevance(self, test: RegressionTest) -> float:
        """
        Compute current relevance score using exponential decay.

        Relevance = 0.5 ^ (days_since_trigger / half_life)

        Factors that boost relevance:
        - Recent triggers
        - High severity
        - From recent incidents

        Factors that reduce relevance:
        - Long time since last trigger
        - High false positive rate
        - Superseded by newer tests
        """
        if not test.last_triggered:
            # Never triggered - use creation date
            reference_date = test.created_at
        else:
            reference_date = test.last_triggered

        try:
            ref = datetime.fromisoformat(reference_date.replace('Z', '+00:00'))
            days_elapsed = (datetime.now(ref.tzinfo) - ref).days
        except Exception:
            days_elapsed = 0

        # Base decay
        base_relevance = math.pow(0.5, days_elapsed / self.half_life)

        # Severity multiplier
        severity_mult = {
            "critical": 1.5,
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8
        }.get(test.severity, 1.0)

        # Source multiplier (incident-derived tests decay slower)
        source_mult = {
            "incident": 1.3,
            "near_miss": 1.2,
            "red_team": 1.0,
            "manual": 0.9
        }.get(test.source, 1.0)

        # Trigger frequency bonus
        trigger_bonus = min(test.trigger_count / 10, 0.3)

        relevance = base_relevance * severity_mult * source_mult + trigger_bonus
        return min(relevance, 1.0)

    def update_relevance_scores(self):
        """Update relevance scores for all tests."""
        for test in self.tests.values():
            if not test.retired_at:
                test.relevance_score = self.compute_relevance(test)

    def get_retirement_candidates(self) -> List[RegressionTest]:
        """Get tests that are candidates for retirement."""
        self.update_relevance_scores()

        candidates = []
        for test in self.tests.values():
            if test.retired_at:
                continue

            # Check relevance threshold
            if test.relevance_score < self.retirement_threshold:
                if test.trigger_count >= self.min_triggers:
                    candidates.append(test)

        return sorted(candidates, key=lambda t: t.relevance_score)

    def retire_test(self, test_id: str, reason: RetirementReason):
        """Retire a test."""
        if test_id not in self.tests:
            return

        test = self.tests[test_id]
        test.retired_at = datetime.now().isoformat()
        test.retirement_reason = reason

    def should_retire(self, test: RegressionTest) -> tuple:
        """
        Determine if a test should be retired.

        Returns:
            (should_retire: bool, reason: Optional[RetirementReason])
        """
        if test.relevance_score < self.retirement_threshold:
            if test.trigger_count >= self.min_triggers:
                return True, RetirementReason.LOW_RELEVANCE

        return False, None

    def get_metrics(self) -> Dict:
        """Get decay management metrics."""
        active = [t for t in self.tests.values() if not t.retired_at]
        retired = [t for t in self.tests.values() if t.retired_at]

        relevance_scores = [t.relevance_score for t in active]

        return {
            "total_tests": len(self.tests),
            "active_tests": len(active),
            "retired_tests": len(retired),
            "avg_relevance": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0,
            "low_relevance_count": len([s for s in relevance_scores if s < 0.3]),
            "retirement_candidates": len(self.get_retirement_candidates()),
            "by_source": {
                source: len([t for t in active if t.source == source])
                for source in ["incident", "near_miss", "red_team", "manual"]
            },
            "by_severity": {
                sev: len([t for t in active if t.severity == sev])
                for sev in ["critical", "high", "medium", "low"]
            }
        }

    def get_coverage_health(self) -> Dict:
        """
        Assess coverage health across failure modes.

        Identifies gaps where tests have decayed.
        """
        active = [t for t in self.tests.values() if not t.retired_at]

        coverage_by_mode = {}
        for test in active:
            mode = test.failure_mode
            if mode not in coverage_by_mode:
                coverage_by_mode[mode] = {
                    "count": 0,
                    "avg_relevance": 0,
                    "max_relevance": 0
                }

            coverage_by_mode[mode]["count"] += 1
            coverage_by_mode[mode]["avg_relevance"] += test.relevance_score
            coverage_by_mode[mode]["max_relevance"] = max(
                coverage_by_mode[mode]["max_relevance"],
                test.relevance_score
            )

        # Compute averages
        for mode in coverage_by_mode:
            count = coverage_by_mode[mode]["count"]
            if count > 0:
                coverage_by_mode[mode]["avg_relevance"] /= count

        # Find weak coverage areas
        weak_areas = [
            mode for mode, stats in coverage_by_mode.items()
            if stats["avg_relevance"] < 0.3 or stats["count"] < 2
        ]

        return {
            "coverage_by_failure_mode": coverage_by_mode,
            "weak_coverage_areas": weak_areas,
            "recommendation": (
                f"Consider adding new tests for: {', '.join(weak_areas)}"
                if weak_areas else "Coverage health is good"
            )
        }

    def auto_retirement_policy(self) -> List[Dict]:
        """
        Execute automatic retirement policy.

        Returns list of retirement actions taken.
        """
        actions = []

        for test in self.get_retirement_candidates():
            should_retire, reason = self.should_retire(test)
            if should_retire and reason:
                self.retire_test(test.test_id, reason)
                actions.append({
                    "action": "retire",
                    "test_id": test.test_id,
                    "reason": reason.value,
                    "relevance_score": test.relevance_score,
                    "last_triggered": test.last_triggered
                })

        return actions

    def quarterly_revalidation(self, traffic_replay_fn=None) -> Dict:
        """
        Quarterly revalidation of retired tests.

        Some retired tests may become relevant again if:
        - Similar attack patterns resurface
        - Model changes reintroduce old vulnerabilities
        """
        retired = [t for t in self.tests.values() if t.retired_at]
        reactivated = []

        for test in retired:
            # Check if similar patterns have been seen recently
            # In production, this would use traffic_replay_fn
            if traffic_replay_fn:
                should_reactivate = traffic_replay_fn(test)
                if should_reactivate:
                    test.retired_at = None
                    test.retirement_reason = None
                    test.relevance_score = 0.5  # Reset to moderate relevance
                    reactivated.append(test.test_id)

        return {
            "reviewed": len(retired),
            "reactivated": reactivated,
            "recommendation": (
                f"Reactivated {len(reactivated)} tests based on recent traffic patterns"
                if reactivated else "No tests reactivated"
            )
        }


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    manager = RegressionDecayManager(
        half_life_days=90,
        retirement_threshold=0.1
    )

    # Add some example tests
    tests = [
        RegressionTest(
            test_id="inc_001",
            created_at="2024-01-01",
            source="incident",
            last_triggered="2024-06-01",
            trigger_count=15,
            failure_mode="prompt_injection",
            severity="high"
        ),
        RegressionTest(
            test_id="nm_002",
            created_at="2024-03-01",
            source="near_miss",
            last_triggered="2024-07-15",
            trigger_count=8,
            failure_mode="policy_erosion",
            severity="medium"
        ),
        RegressionTest(
            test_id="rt_003",
            created_at="2023-06-01",
            source="red_team",
            last_triggered="2023-09-01",
            trigger_count=20,
            failure_mode="tool_hallucination",
            severity="medium"
        ),
        RegressionTest(
            test_id="man_004",
            created_at="2023-01-01",
            source="manual",
            last_triggered="2023-03-01",
            trigger_count=5,
            failure_mode="direct_jailbreak",
            severity="low"
        ),
    ]

    for test in tests:
        manager.add_test(test)

    # Update relevance
    manager.update_relevance_scores()

    print("=== Test Relevance Scores ===")
    for test_id, test in manager.tests.items():
        print(f"{test_id}: relevance={test.relevance_score:.3f}")

    print("\n=== Metrics ===")
    print(json.dumps(manager.get_metrics(), indent=2))

    print("\n=== Coverage Health ===")
    print(json.dumps(manager.get_coverage_health(), indent=2))

    print("\n=== Retirement Candidates ===")
    candidates = manager.get_retirement_candidates()
    for c in candidates:
        print(f"  {c.test_id}: relevance={c.relevance_score:.3f}")

    print("\n=== Auto Retirement ===")
    actions = manager.auto_retirement_policy()
    print(json.dumps(actions, indent=2))
