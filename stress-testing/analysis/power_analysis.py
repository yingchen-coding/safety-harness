"""
Statistical Power Analysis for Red-Team Stress Tests
=====================================================

Prevents false confidence from under-powered red-teaming.

Key insight: Running "a few" stress tests is not enough.
This module computes required sample sizes and confidence intervals
to ensure statistically meaningful red-team conclusions.
"""

from dataclasses import dataclass
from typing import Dict, List
import math


@dataclass
class PowerAnalysisResult:
    """Results from power analysis computation."""

    n_rollouts: int
    ci_width_95: float
    coverage_estimate: float
    power_at_10pct_effect: float
    recommendation: str


def compute_ci_width(n: int, p: float = 0.5) -> float:
    """
    Compute 95% CI width for a proportion.

    Args:
        n: Sample size (number of rollouts)
        p: Estimated proportion (default 0.5 for max variance)

    Returns:
        Width of 95% confidence interval (one-sided)
    """
    if n <= 0:
        return float('inf')

    # Standard error of proportion
    se = math.sqrt(p * (1 - p) / n)

    # 95% CI uses z=1.96
    return 1.96 * se


def compute_power(n: int, effect_size: float = 0.10, alpha: float = 0.05) -> float:
    """
    Compute statistical power to detect a given effect size.

    Args:
        n: Sample size
        effect_size: Minimum detectable difference (e.g., 0.10 = 10%)
        alpha: Significance level

    Returns:
        Power (probability of detecting true effect)
    """
    if n <= 0:
        return 0.0

    # Simplified power calculation for proportion test
    # Using normal approximation
    p0 = 0.5  # Null hypothesis proportion
    p1 = p0 + effect_size  # Alternative hypothesis

    se0 = math.sqrt(p0 * (1 - p0) / n)
    se1 = math.sqrt(p1 * (1 - p1) / n)

    # Z-score for alpha
    z_alpha = 1.96 if alpha == 0.05 else 1.645

    # Critical value under null
    critical = p0 + z_alpha * se0

    # Power = P(reject H0 | H1 true)
    z_power = (critical - p1) / se1
    power = 1 - _norm_cdf(z_power)

    return min(power, 0.99)  # Cap at 99%


def _norm_cdf(z: float) -> float:
    """Standard normal CDF approximation."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def estimate_coverage(n: int, attack_space_size: int = 1000) -> float:
    """
    Estimate attack space coverage given sample size.

    Args:
        n: Number of rollouts
        attack_space_size: Estimated size of attack space

    Returns:
        Estimated coverage proportion
    """
    # Simple model: coverage follows 1 - (1 - 1/k)^n
    # where k is attack space size
    if attack_space_size <= 0:
        return 0.0

    coverage = 1 - math.pow(1 - 1/attack_space_size, n)
    return min(coverage, 1.0)


def generate_power_table() -> List[PowerAnalysisResult]:
    """
    Generate power analysis table for common sample sizes.

    Returns:
        List of PowerAnalysisResult for n=50, 100, 200, 500, 1000
    """
    sample_sizes = [50, 100, 200, 500, 1000]
    results = []

    for n in sample_sizes:
        ci_width = compute_ci_width(n)
        coverage = estimate_coverage(n)
        power = compute_power(n, effect_size=0.10)

        if power < 0.50:
            recommendation = "INSUFFICIENT - Increase sample size"
        elif power < 0.80:
            recommendation = "MARGINAL - Consider increasing sample size"
        else:
            recommendation = "ADEQUATE - Proceed with analysis"

        results.append(PowerAnalysisResult(
            n_rollouts=n,
            ci_width_95=ci_width,
            coverage_estimate=coverage,
            power_at_10pct_effect=power,
            recommendation=recommendation
        ))

    return results


def print_power_table():
    """Print formatted power analysis table."""
    results = generate_power_table()

    print("\n" + "=" * 80)
    print("STATISTICAL POWER ANALYSIS FOR RED-TEAM STRESS TESTS")
    print("=" * 80)
    print("\nKey insight: Red-teaming is a statistical problem, not just a checklist.\n")

    print(f"{'#Rollouts':<12} {'95% CI Width':<15} {'Coverage':<12} {'Power (10%)':<15} {'Status'}")
    print("-" * 80)

    for r in results:
        print(f"{r.n_rollouts:<12} {f'±{r.ci_width_95:.1%}':<15} {r.coverage_estimate:.1%}{'':>5} "
              f"{r.power_at_10pct_effect:.1%}{'':>8} {r.recommendation}")

    print("\n" + "-" * 80)
    print("INTERPRETATION GUIDE:")
    print("- 95% CI Width: Uncertainty in failure rate estimate (narrower = more precise)")
    print("- Coverage: Estimated proportion of attack space explored")
    print("- Power (10%): Probability of detecting a 10% regression in safety")
    print("=" * 80 + "\n")


def required_sample_size(
    target_ci_width: float = 0.05,
    target_power: float = 0.80,
    effect_size: float = 0.10
) -> Dict[str, int]:
    """
    Compute required sample size for target precision and power.

    Args:
        target_ci_width: Desired CI width (e.g., 0.05 for ±5%)
        target_power: Desired statistical power
        effect_size: Minimum effect size to detect

    Returns:
        Dict with required sample sizes for each criterion
    """
    # Binary search for CI width
    n_for_ci = 1
    while compute_ci_width(n_for_ci) > target_ci_width and n_for_ci < 10000:
        n_for_ci *= 2

    # Refine with binary search
    lo, hi = n_for_ci // 2, n_for_ci
    while lo < hi:
        mid = (lo + hi) // 2
        if compute_ci_width(mid) <= target_ci_width:
            hi = mid
        else:
            lo = mid + 1
    n_for_ci = lo

    # Binary search for power
    n_for_power = 1
    while compute_power(n_for_power, effect_size) < target_power and n_for_power < 10000:
        n_for_power *= 2

    lo, hi = n_for_power // 2, n_for_power
    while lo < hi:
        mid = (lo + hi) // 2
        if compute_power(mid, effect_size) >= target_power:
            hi = mid
        else:
            lo = mid + 1
    n_for_power = lo

    return {
        "for_ci_width": n_for_ci,
        "for_power": n_for_power,
        "recommended": max(n_for_ci, n_for_power)
    }


# Output format for downstream consumption
OUTPUT_SCHEMA = {
    "description": "Power analysis output for stress test budget planning",
    "fields": {
        "n_rollouts": "Number of stress test rollouts",
        "ci_width_95": "95% confidence interval width",
        "coverage_estimate": "Estimated attack space coverage",
        "power_at_10pct_effect": "Power to detect 10% regression",
        "recommendation": "Human-readable guidance"
    },
    "consumers": [
        "model-safety-regression-suite: Sample size requirements for release gating",
        "scalable-safeguards-eval-pipeline: Batch size configuration"
    ]
}


if __name__ == "__main__":
    print_power_table()

    print("\nSAMPLE SIZE RECOMMENDATIONS:")
    print("-" * 40)

    reqs = required_sample_size(target_ci_width=0.05, target_power=0.80)
    print(f"For ±5% CI width: {reqs['for_ci_width']} rollouts")
    print(f"For 80% power (10% effect): {reqs['for_power']} rollouts")
    print(f"RECOMMENDED MINIMUM: {reqs['recommended']} rollouts")
