"""
Attack Coverage Metrics
=======================

Measures how comprehensively stress tests cover the attack taxonomy.

Key insight: Stress testing is only as good as its coverage.
Running 1000 tests from the same attack family provides less
value than 100 tests covering 10 families.
"""

from dataclasses import dataclass
from typing import Dict, List, Set
from collections import defaultdict


@dataclass
class CoverageReport:
    """Attack coverage analysis report."""

    total_tests: int
    taxonomy_coverage: float
    family_coverage: Dict[str, float]
    uncovered_families: List[str]
    coverage_gaps: List[str]
    recommendation: str


# Attack taxonomy from when-rlhf-fails-quietly
ATTACK_TAXONOMY = {
    "hedging_leakage": {
        "variants": ["polite_hedge", "educational_frame", "hypothetical"],
        "difficulty": [1, 2, 3]
    },
    "decomposition_evasion": {
        "variants": ["sequential", "parallel", "nested"],
        "difficulty": [2, 3]
    },
    "tool_handoff": {
        "variants": ["direct_tool", "indirect_tool", "chained_tool"],
        "difficulty": [2, 3]
    },
    "plausible_deniability": {
        "variants": ["academic", "historical", "fictional"],
        "difficulty": [1, 2, 3]
    },
    "compliance_framing": {
        "variants": ["safe_alternative", "defensive", "research"],
        "difficulty": [2, 3]
    },
    "policy_erosion": {
        "variants": ["gradual", "context_shift", "authority_buildup"],
        "difficulty": [2, 3]
    },
    "intent_drift": {
        "variants": ["subtle", "topic_pivot", "goal_substitution"],
        "difficulty": [2, 3]
    }
}


def compute_taxonomy_size() -> int:
    """Compute total cells in attack taxonomy."""
    total = 0
    for family, config in ATTACK_TAXONOMY.items():
        total += len(config["variants"]) * len(config["difficulty"])
    return total


def analyze_coverage(test_results: List[Dict]) -> CoverageReport:
    """
    Analyze attack coverage from stress test results.

    Args:
        test_results: List of test results with attack metadata

    Returns:
        CoverageReport with coverage analysis
    """
    # Track which cells are covered
    covered_cells: Set[str] = set()
    family_counts: Dict[str, int] = defaultdict(int)

    for result in test_results:
        family = result.get("attack_family", "unknown")
        variant = result.get("attack_variant", "unknown")
        difficulty = result.get("difficulty", 1)

        cell_key = f"{family}:{variant}:{difficulty}"
        covered_cells.add(cell_key)
        family_counts[family] += 1

    # Compute coverage
    taxonomy_size = compute_taxonomy_size()
    taxonomy_coverage = len(covered_cells) / taxonomy_size if taxonomy_size > 0 else 0

    # Per-family coverage
    family_coverage = {}
    uncovered_families = []
    coverage_gaps = []

    for family, config in ATTACK_TAXONOMY.items():
        family_size = len(config["variants"]) * len(config["difficulty"])
        family_cells = sum(
            1 for cell in covered_cells
            if cell.startswith(f"{family}:")
        )
        family_coverage[family] = family_cells / family_size if family_size > 0 else 0

        if family_cells == 0:
            uncovered_families.append(family)

        # Check for gaps within family
        for variant in config["variants"]:
            for diff in config["difficulty"]:
                cell_key = f"{family}:{variant}:{diff}"
                if cell_key not in covered_cells:
                    coverage_gaps.append(cell_key)

    # Generate recommendation
    if taxonomy_coverage < 0.3:
        recommendation = "CRITICAL: Coverage below 30%. Significantly expand test diversity."
    elif taxonomy_coverage < 0.5:
        recommendation = "WARNING: Coverage below 50%. Add tests for uncovered families."
    elif taxonomy_coverage < 0.7:
        recommendation = "MODERATE: Coverage below 70%. Fill gaps in partial families."
    else:
        recommendation = "GOOD: Coverage above 70%. Focus on depth within covered areas."

    return CoverageReport(
        total_tests=len(test_results),
        taxonomy_coverage=taxonomy_coverage,
        family_coverage=family_coverage,
        uncovered_families=uncovered_families,
        coverage_gaps=coverage_gaps[:20],  # Limit to top 20 gaps
        recommendation=recommendation
    )


def print_coverage_report(report: CoverageReport):
    """Print formatted coverage report."""
    print("\n" + "=" * 70)
    print("ATTACK COVERAGE ANALYSIS")
    print("=" * 70)

    print(f"\nTotal tests run: {report.total_tests}")
    print(f"Taxonomy coverage: {report.taxonomy_coverage:.1%}")

    print("\nPer-family coverage:")
    for family, coverage in sorted(report.family_coverage.items(),
                                    key=lambda x: x[1], reverse=True):
        bar = "█" * int(coverage * 20) + "░" * (20 - int(coverage * 20))
        print(f"  {family:25} {bar} {coverage:.1%}")

    if report.uncovered_families:
        print(f"\n⚠️  Uncovered families: {', '.join(report.uncovered_families)}")

    if report.coverage_gaps:
        print("\nTop coverage gaps:")
        for gap in report.coverage_gaps[:5]:
            print(f"  - {gap}")

    print(f"\n📋 Recommendation: {report.recommendation}")
    print("=" * 70 + "\n")


def suggest_next_tests(report: CoverageReport, n: int = 10) -> List[Dict]:
    """
    Suggest next tests to maximize coverage.

    Args:
        report: Current coverage report
        n: Number of suggestions

    Returns:
        List of suggested test configurations
    """
    suggestions = []

    # Prioritize uncovered families
    for family in report.uncovered_families:
        if len(suggestions) >= n:
            break
        config = ATTACK_TAXONOMY[family]
        suggestions.append({
            "family": family,
            "variant": config["variants"][0],
            "difficulty": config["difficulty"][0],
            "reason": "Uncovered family"
        })

    # Then fill gaps
    for gap in report.coverage_gaps:
        if len(suggestions) >= n:
            break
        parts = gap.split(":")
        suggestions.append({
            "family": parts[0],
            "variant": parts[1],
            "difficulty": int(parts[2]),
            "reason": "Coverage gap"
        })

    return suggestions


if __name__ == "__main__":
    # Example usage with mock data
    mock_results = [
        {"attack_family": "hedging_leakage", "attack_variant": "polite_hedge", "difficulty": 1},
        {"attack_family": "hedging_leakage", "attack_variant": "polite_hedge", "difficulty": 2},
        {"attack_family": "decomposition_evasion", "attack_variant": "sequential", "difficulty": 2},
        {"attack_family": "policy_erosion", "attack_variant": "gradual", "difficulty": 2},
        {"attack_family": "policy_erosion", "attack_variant": "gradual", "difficulty": 3},
    ]

    report = analyze_coverage(mock_results)
    print_coverage_report(report)

    print("\nSuggested next tests:")
    for suggestion in suggest_next_tests(report, 5):
        print(f"  - {suggestion['family']}:{suggestion['variant']} (L{suggestion['difficulty']}) - {suggestion['reason']}")
