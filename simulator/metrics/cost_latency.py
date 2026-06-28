"""
Cost and Latency Profiling for Safeguards.

Purpose: Quantify operational cost of safety measures.

Key insight: Safety isn't free. Every safeguard adds latency and token cost.
Production deployment requires explicit tradeoff analysis.
"""

import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class CostCategory(Enum):
    """Categories of safeguard costs."""
    CLASSIFIER_CALL = "classifier_call"     # Intent/harm classifier
    LLM_JUDGE = "llm_judge"                 # LLM-based evaluation
    EMBEDDING_LOOKUP = "embedding_lookup"   # Vector similarity
    RULE_CHECK = "rule_check"               # Regex/rule evaluation
    HUMAN_REVIEW = "human_review"           # Escalation to human


@dataclass
class CostRecord:
    """A single cost measurement."""
    category: CostCategory
    latency_ms: float
    tokens_input: int
    tokens_output: int
    cost_usd: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)


@dataclass
class LatencyProfile:
    """Latency statistics for a safeguard."""
    safeguard_name: str
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    std_ms: float
    sample_count: int


@dataclass
class CostProfile:
    """Cost statistics for a safeguard."""
    safeguard_name: str
    mean_tokens: float
    mean_cost_usd: float
    total_tokens: int
    total_cost_usd: float
    sample_count: int


class CostLatencyProfiler:
    """
    Profile cost and latency of safeguard operations.

    Philosophy: "Safety" that makes the product unusable isn't safety.
    Quantify tradeoffs to make informed deployment decisions.
    """

    # Cost per token (approximate, varies by provider)
    COST_PER_INPUT_TOKEN = 0.00001   # $0.01 per 1K tokens
    COST_PER_OUTPUT_TOKEN = 0.00003  # $0.03 per 1K tokens

    def __init__(self):
        self.records: List[CostRecord] = []
        self.budgets: Dict[str, Dict] = {}

    def record_cost(
        self,
        category: CostCategory,
        latency_ms: float,
        tokens_input: int = 0,
        tokens_output: int = 0,
        cost_usd: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> CostRecord:
        """Record a single cost measurement."""
        if cost_usd is None:
            cost_usd = (
                tokens_input * self.COST_PER_INPUT_TOKEN +
                tokens_output * self.COST_PER_OUTPUT_TOKEN
            )

        record = CostRecord(
            category=category,
            latency_ms=latency_ms,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost_usd,
            metadata=metadata or {}
        )

        self.records.append(record)
        return record

    def set_budget(
        self,
        safeguard_name: str,
        max_p95_latency_ms: float,
        max_tokens_per_call: int,
        max_cost_per_call_usd: float
    ):
        """Set operational budget for a safeguard."""
        self.budgets[safeguard_name] = {
            "max_p95_latency_ms": max_p95_latency_ms,
            "max_tokens_per_call": max_tokens_per_call,
            "max_cost_per_call_usd": max_cost_per_call_usd
        }

    def get_latency_profile(
        self,
        category: Optional[CostCategory] = None
    ) -> LatencyProfile:
        """Compute latency profile for a category."""
        if category:
            records = [r for r in self.records if r.category == category]
            name = category.value
        else:
            records = self.records
            name = "all"

        if not records:
            return LatencyProfile(
                safeguard_name=name,
                p50_ms=0, p95_ms=0, p99_ms=0,
                mean_ms=0, std_ms=0, sample_count=0
            )

        latencies = sorted([r.latency_ms for r in records])
        n = len(latencies)

        return LatencyProfile(
            safeguard_name=name,
            p50_ms=latencies[n // 2],
            p95_ms=latencies[int(n * 0.95)] if n >= 20 else latencies[-1],
            p99_ms=latencies[int(n * 0.99)] if n >= 100 else latencies[-1],
            mean_ms=statistics.mean(latencies),
            std_ms=statistics.stdev(latencies) if n > 1 else 0,
            sample_count=n
        )

    def get_cost_profile(
        self,
        category: Optional[CostCategory] = None
    ) -> CostProfile:
        """Compute cost profile for a category."""
        if category:
            records = [r for r in self.records if r.category == category]
            name = category.value
        else:
            records = self.records
            name = "all"

        if not records:
            return CostProfile(
                safeguard_name=name,
                mean_tokens=0, mean_cost_usd=0,
                total_tokens=0, total_cost_usd=0,
                sample_count=0
            )

        total_tokens = sum(r.tokens_input + r.tokens_output for r in records)
        total_cost = sum(r.cost_usd for r in records)
        n = len(records)

        return CostProfile(
            safeguard_name=name,
            mean_tokens=total_tokens / n,
            mean_cost_usd=total_cost / n,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            sample_count=n
        )

    def check_budget_compliance(
        self,
        safeguard_name: str,
        category: CostCategory
    ) -> Dict:
        """Check if safeguard meets budget constraints."""
        if safeguard_name not in self.budgets:
            return {"error": f"No budget defined for {safeguard_name}"}

        budget = self.budgets[safeguard_name]
        latency_profile = self.get_latency_profile(category)
        cost_profile = self.get_cost_profile(category)

        latency_ok = latency_profile.p95_ms <= budget["max_p95_latency_ms"]
        tokens_ok = cost_profile.mean_tokens <= budget["max_tokens_per_call"]
        cost_ok = cost_profile.mean_cost_usd <= budget["max_cost_per_call_usd"]

        return {
            "safeguard": safeguard_name,
            "budget": budget,
            "actual": {
                "p95_latency_ms": latency_profile.p95_ms,
                "mean_tokens": cost_profile.mean_tokens,
                "mean_cost_usd": cost_profile.mean_cost_usd
            },
            "compliance": {
                "latency": latency_ok,
                "tokens": tokens_ok,
                "cost": cost_ok,
                "overall": latency_ok and tokens_ok and cost_ok
            },
            "violations": [
                v for v in [
                    None if latency_ok else f"P95 latency {latency_profile.p95_ms:.0f}ms exceeds {budget['max_p95_latency_ms']}ms",
                    None if tokens_ok else f"Mean tokens {cost_profile.mean_tokens:.0f} exceeds {budget['max_tokens_per_call']}",
                    None if cost_ok else f"Mean cost ${cost_profile.mean_cost_usd:.4f} exceeds ${budget['max_cost_per_call_usd']}"
                ] if v
            ]
        }

    def get_full_report(self) -> Dict:
        """Generate comprehensive cost/latency report."""
        report = {
            "summary": {
                "total_records": len(self.records),
                "total_cost_usd": sum(r.cost_usd for r in self.records),
                "total_tokens": sum(r.tokens_input + r.tokens_output for r in self.records)
            },
            "by_category": {},
            "budget_compliance": {}
        }

        for category in CostCategory:
            latency = self.get_latency_profile(category)
            cost = self.get_cost_profile(category)

            if latency.sample_count > 0:
                report["by_category"][category.value] = {
                    "latency": {
                        "p50_ms": latency.p50_ms,
                        "p95_ms": latency.p95_ms,
                        "mean_ms": latency.mean_ms
                    },
                    "cost": {
                        "mean_tokens": cost.mean_tokens,
                        "mean_cost_usd": cost.mean_cost_usd,
                        "total_cost_usd": cost.total_cost_usd
                    },
                    "sample_count": latency.sample_count
                }

        # Check all budgets
        for safeguard_name in self.budgets:
            for category in CostCategory:
                records = [r for r in self.records if r.category == category]
                if records:
                    compliance = self.check_budget_compliance(safeguard_name, category)
                    if "error" not in compliance:
                        report["budget_compliance"][f"{safeguard_name}_{category.value}"] = compliance

        return report

    def estimate_conversation_cost(
        self,
        n_turns: int,
        safeguards_per_turn: List[CostCategory]
    ) -> Dict:
        """Estimate total cost for a conversation."""
        total_latency = 0
        total_tokens = 0
        total_cost = 0

        for category in safeguards_per_turn:
            cost_profile = self.get_cost_profile(category)
            latency_profile = self.get_latency_profile(category)

            total_latency += latency_profile.mean_ms * n_turns
            total_tokens += cost_profile.mean_tokens * n_turns
            total_cost += cost_profile.mean_cost_usd * n_turns

        return {
            "n_turns": n_turns,
            "safeguards_per_turn": [c.value for c in safeguards_per_turn],
            "estimated_total_latency_ms": total_latency,
            "estimated_total_tokens": total_tokens,
            "estimated_total_cost_usd": total_cost
        }


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    import random

    profiler = CostLatencyProfiler()

    # Set budgets
    profiler.set_budget(
        "intent_classifier",
        max_p95_latency_ms=200,
        max_tokens_per_call=500,
        max_cost_per_call_usd=0.01
    )

    profiler.set_budget(
        "llm_judge",
        max_p95_latency_ms=2000,
        max_tokens_per_call=2000,
        max_cost_per_call_usd=0.05
    )

    # Simulate measurements
    for _ in range(100):
        # Classifier calls
        profiler.record_cost(
            category=CostCategory.CLASSIFIER_CALL,
            latency_ms=random.gauss(50, 15),
            tokens_input=random.randint(100, 300),
            tokens_output=random.randint(10, 50)
        )

        # LLM judge calls
        profiler.record_cost(
            category=CostCategory.LLM_JUDGE,
            latency_ms=random.gauss(800, 200),
            tokens_input=random.randint(500, 1500),
            tokens_output=random.randint(100, 500)
        )

        # Rule checks (cheap)
        profiler.record_cost(
            category=CostCategory.RULE_CHECK,
            latency_ms=random.gauss(5, 2),
            tokens_input=0,
            tokens_output=0,
            cost_usd=0
        )

    # Generate report
    report = profiler.get_full_report()

    print("=== Cost/Latency Report ===")
    print(f"\nTotal Records: {report['summary']['total_records']}")
    print(f"Total Cost: ${report['summary']['total_cost_usd']:.4f}")

    print("\n=== By Category ===")
    for cat, stats in report["by_category"].items():
        print(f"\n{cat}:")
        print(f"  P95 Latency: {stats['latency']['p95_ms']:.0f}ms")
        print(f"  Mean Tokens: {stats['cost']['mean_tokens']:.0f}")
        print(f"  Mean Cost: ${stats['cost']['mean_cost_usd']:.4f}")

    # Check budget compliance
    print("\n=== Budget Compliance ===")
    compliance = profiler.check_budget_compliance("intent_classifier", CostCategory.CLASSIFIER_CALL)
    print(f"Intent Classifier: {'PASS' if compliance['compliance']['overall'] else 'FAIL'}")

    compliance = profiler.check_budget_compliance("llm_judge", CostCategory.LLM_JUDGE)
    print(f"LLM Judge: {'PASS' if compliance['compliance']['overall'] else 'FAIL'}")

    # Estimate conversation cost
    print("\n=== Conversation Cost Estimate ===")
    estimate = profiler.estimate_conversation_cost(
        n_turns=10,
        safeguards_per_turn=[CostCategory.CLASSIFIER_CALL, CostCategory.RULE_CHECK]
    )
    print(f"10-turn conversation: ${estimate['estimated_total_cost_usd']:.4f}")
