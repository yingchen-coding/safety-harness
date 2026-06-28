"""
Power Analysis for Stress Testing: Size experiments to detect real effects.

Key insight: Delayed failures are rare events. Underpowered experiments
lead to false negatives and overconfident conclusions.

This module provides:
1. Sample size calculation for safety regression detection
2. Effect size estimation
3. Confidence interval computation
4. A/B test power analysis
"""

import math
from dataclasses import dataclass
from typing import Optional, Dict
from scipy import stats as scipy_stats


@dataclass
class PowerAnalysisResult:
    """Result of power analysis calculation."""
    required_n: int
    effect_size: float
    power: float
    alpha: float
    test_type: str
    notes: str = ""


@dataclass
class ExperimentResult:
    """Result of an experiment with statistical analysis."""
    n_control: int
    n_treatment: int
    rate_control: float
    rate_treatment: float
    effect_size: float
    ci_lower: float
    ci_upper: float
    p_value: float
    is_significant: bool
    achieved_power: float


class PowerAnalyzer:
    """
    Power analysis for safety stress testing.

    Philosophy: "We didn't see a difference" is only meaningful
    if you had enough power to detect one.
    """

    def __init__(self, default_alpha: float = 0.05, default_power: float = 0.8):
        self.default_alpha = default_alpha
        self.default_power = default_power

    def calculate_sample_size(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        alpha: Optional[float] = None,
        power: Optional[float] = None,
        one_sided: bool = False
    ) -> PowerAnalysisResult:
        """
        Calculate required sample size to detect a given effect.

        Args:
            baseline_rate: Expected failure rate in control condition
            minimum_detectable_effect: Smallest meaningful difference to detect
            alpha: Significance level (default 0.05)
            power: Desired power (default 0.8)
            one_sided: Use one-sided test (default False)

        Returns:
            PowerAnalysisResult with required sample size
        """
        alpha = alpha or self.default_alpha
        power = power or self.default_power

        # Treatment rate
        treatment_rate = baseline_rate + minimum_detectable_effect

        # Cohen's h for proportions
        effect_size = self._cohens_h(baseline_rate, treatment_rate)

        # Z-values
        z_alpha = scipy_stats.norm.ppf(1 - alpha / (1 if one_sided else 2))
        z_beta = scipy_stats.norm.ppf(power)

        # Sample size per group (formula for two-proportion z-test)
        p_pooled = (baseline_rate + treatment_rate) / 2
        numerator = (z_alpha + z_beta) ** 2 * 2 * p_pooled * (1 - p_pooled)
        denominator = minimum_detectable_effect ** 2

        n_per_group = math.ceil(numerator / denominator)

        return PowerAnalysisResult(
            required_n=n_per_group,
            effect_size=effect_size,
            power=power,
            alpha=alpha,
            test_type="one-sided" if one_sided else "two-sided",
            notes=f"N per group to detect {minimum_detectable_effect:.1%} change from {baseline_rate:.1%} baseline"
        )

    def calculate_power(
        self,
        n: int,
        baseline_rate: float,
        expected_effect: float,
        alpha: Optional[float] = None
    ) -> float:
        """
        Calculate achieved power for a given sample size.

        Args:
            n: Sample size per group
            baseline_rate: Expected failure rate in control
            expected_effect: Expected difference to detect
            alpha: Significance level

        Returns:
            Achieved power (0-1)
        """
        alpha = alpha or self.default_alpha

        treatment_rate = baseline_rate + expected_effect
        p_pooled = (baseline_rate + treatment_rate) / 2

        # Standard error
        se = math.sqrt(2 * p_pooled * (1 - p_pooled) / n)

        # Z-value for alpha
        z_alpha = scipy_stats.norm.ppf(1 - alpha / 2)

        # Z-value for observed effect
        z_effect = abs(expected_effect) / se

        # Power
        power = scipy_stats.norm.cdf(z_effect - z_alpha)

        return power

    def _cohens_h(self, p1: float, p2: float) -> float:
        """Compute Cohen's h effect size for proportions."""
        phi1 = 2 * math.asin(math.sqrt(p1))
        phi2 = 2 * math.asin(math.sqrt(p2))
        return abs(phi1 - phi2)

    def analyze_experiment(
        self,
        n_control: int,
        n_treatment: int,
        failures_control: int,
        failures_treatment: int,
        alpha: Optional[float] = None
    ) -> ExperimentResult:
        """
        Analyze results of a stress test experiment.

        Args:
            n_control: Sample size in control condition
            n_treatment: Sample size in treatment condition
            failures_control: Number of failures in control
            failures_treatment: Number of failures in treatment
            alpha: Significance level

        Returns:
            ExperimentResult with statistical analysis
        """
        alpha = alpha or self.default_alpha

        rate_control = failures_control / n_control
        rate_treatment = failures_treatment / n_treatment
        effect = rate_treatment - rate_control

        # Two-proportion z-test
        p_pooled = (failures_control + failures_treatment) / (n_control + n_treatment)
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))

        if se > 0:
            z_stat = effect / se
            p_value = 2 * (1 - scipy_stats.norm.cdf(abs(z_stat)))
        else:
            z_stat = 0
            p_value = 1.0

        # Confidence interval
        z_crit = scipy_stats.norm.ppf(1 - alpha / 2)
        ci_lower = effect - z_crit * se
        ci_upper = effect + z_crit * se

        # Achieved power
        achieved_power = self.calculate_power(
            n=min(n_control, n_treatment),
            baseline_rate=rate_control,
            expected_effect=effect if effect != 0 else 0.05,
            alpha=alpha
        )

        return ExperimentResult(
            n_control=n_control,
            n_treatment=n_treatment,
            rate_control=rate_control,
            rate_treatment=rate_treatment,
            effect_size=effect,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            p_value=p_value,
            is_significant=p_value < alpha,
            achieved_power=achieved_power
        )

    def interpret_result(self, result: ExperimentResult) -> Dict:
        """Generate human-readable interpretation of experiment result."""
        interpretation = {
            "summary": "",
            "effect_direction": "",
            "statistical_significance": "",
            "practical_significance": "",
            "power_assessment": "",
            "recommendations": []
        }

        # Effect direction
        if result.effect_size > 0:
            interpretation["effect_direction"] = "Treatment INCREASED failure rate"
        elif result.effect_size < 0:
            interpretation["effect_direction"] = "Treatment DECREASED failure rate"
        else:
            interpretation["effect_direction"] = "No difference observed"

        # Statistical significance
        if result.is_significant:
            interpretation["statistical_significance"] = (
                f"Result IS statistically significant (p={result.p_value:.4f})"
            )
        else:
            interpretation["statistical_significance"] = (
                f"Result is NOT statistically significant (p={result.p_value:.4f})"
            )

        # Practical significance
        if abs(result.effect_size) >= 0.10:
            interpretation["practical_significance"] = "Large practical effect"
        elif abs(result.effect_size) >= 0.05:
            interpretation["practical_significance"] = "Moderate practical effect"
        else:
            interpretation["practical_significance"] = "Small practical effect"

        # Power assessment
        if result.achieved_power >= 0.8:
            interpretation["power_assessment"] = "Well-powered experiment"
        elif result.achieved_power >= 0.5:
            interpretation["power_assessment"] = "Moderately powered experiment"
        else:
            interpretation["power_assessment"] = "UNDERPOWERED experiment - results may be unreliable"

        # Recommendations
        if not result.is_significant and result.achieved_power < 0.8:
            interpretation["recommendations"].append(
                "Consider increasing sample size to achieve 80% power"
            )
            needed_n = self.calculate_sample_size(
                baseline_rate=result.rate_control,
                minimum_detectable_effect=0.05
            ).required_n
            interpretation["recommendations"].append(
                f"Estimated N needed: {needed_n} per group"
            )

        if result.is_significant:
            interpretation["recommendations"].append(
                "Result is significant - consider investigating root cause"
            )

        # Summary
        interpretation["summary"] = (
            f"{interpretation['effect_direction']}. "
            f"{interpretation['statistical_significance']}. "
            f"{interpretation['power_assessment']}."
        )

        return interpretation

    def get_sample_size_table(
        self,
        baseline_rates: list = [0.05, 0.10, 0.20, 0.30],
        effects: list = [0.03, 0.05, 0.10, 0.15]
    ) -> Dict:
        """Generate reference table of sample sizes for common scenarios."""
        table = []

        for baseline in baseline_rates:
            for effect in effects:
                if baseline + effect <= 1.0:  # Valid rate
                    result = self.calculate_sample_size(
                        baseline_rate=baseline,
                        minimum_detectable_effect=effect
                    )
                    table.append({
                        "baseline_rate": baseline,
                        "minimum_effect": effect,
                        "treatment_rate": baseline + effect,
                        "required_n_per_group": result.required_n,
                        "total_n": result.required_n * 2
                    })

        return {
            "parameters": {
                "alpha": self.default_alpha,
                "power": self.default_power
            },
            "table": table
        }


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    analyzer = PowerAnalyzer(default_alpha=0.05, default_power=0.8)

    print("=== Sample Size Calculation ===")
    result = analyzer.calculate_sample_size(
        baseline_rate=0.10,
        minimum_detectable_effect=0.05
    )
    print("Baseline: 10%, MDE: 5%")
    print(f"Required N per group: {result.required_n}")
    print(f"Notes: {result.notes}")

    print("\n=== Sample Size Reference Table ===")
    table = analyzer.get_sample_size_table()
    print(f"Parameters: alpha={table['parameters']['alpha']}, power={table['parameters']['power']}")
    print("\nBaseline | Effect | N per group | Total N")
    print("-" * 50)
    for row in table["table"][:10]:  # First 10 rows
        print(f"{row['baseline_rate']:.0%}     | {row['minimum_effect']:.0%}   | {row['required_n_per_group']:>11} | {row['total_n']:>7}")

    print("\n=== Experiment Analysis ===")
    exp_result = analyzer.analyze_experiment(
        n_control=200,
        n_treatment=200,
        failures_control=20,
        failures_treatment=35
    )
    print(f"Control: {exp_result.rate_control:.1%} ({exp_result.n_control} samples)")
    print(f"Treatment: {exp_result.rate_treatment:.1%} ({exp_result.n_treatment} samples)")
    print(f"Effect: {exp_result.effect_size:.1%}")
    print(f"95% CI: [{exp_result.ci_lower:.1%}, {exp_result.ci_upper:.1%}]")
    print(f"p-value: {exp_result.p_value:.4f}")
    print(f"Significant: {exp_result.is_significant}")
    print(f"Achieved Power: {exp_result.achieved_power:.1%}")

    print("\n=== Interpretation ===")
    interp = analyzer.interpret_result(exp_result)
    print(f"Summary: {interp['summary']}")
    for rec in interp["recommendations"]:
        print(f"  - {rec}")
