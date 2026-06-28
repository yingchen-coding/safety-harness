"""
Statistical significance testing for safety regression detection.

Provides bootstrap confidence intervals, permutation tests, and power analysis
to distinguish real regressions from random noise.
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class StatisticalResult:
    """Result of statistical significance testing."""
    delta: float
    ci_lower: float
    ci_upper: float
    p_value: float
    is_significant: bool
    effect_size: float
    power: float
    samples_for_power_80: int

    def to_dict(self) -> dict:
        return {
            'delta': round(self.delta, 4),
            'ci_lower': round(self.ci_lower, 4),
            'ci_upper': round(self.ci_upper, 4),
            'p_value': round(self.p_value, 4),
            'is_significant': self.is_significant,
            'effect_size': round(self.effect_size, 4),
            'power': round(self.power, 4),
            'samples_for_power_80': self.samples_for_power_80
        }


class StatisticalAnalyzer:
    """
    Statistical analysis for regression detection.

    Uses non-parametric methods suitable for safety metrics which
    may not follow normal distributions.
    """

    def __init__(
        self,
        confidence_level: float = 0.95,
        n_bootstrap: int = 10000,
        n_permutations: int = 10000,
        random_seed: int = 42
    ):
        self.confidence_level = confidence_level
        self.n_bootstrap = n_bootstrap
        self.n_permutations = n_permutations
        self.rng = np.random.default_rng(random_seed)

    def bootstrap_ci(
        self,
        baseline_samples: np.ndarray,
        candidate_samples: np.ndarray
    ) -> tuple[float, float, float]:
        """
        Compute bootstrap confidence interval for the difference in means.

        Args:
            baseline_samples: Array of baseline metric values
            candidate_samples: Array of candidate metric values

        Returns:
            Tuple of (delta, ci_lower, ci_upper)
        """
        baseline_samples = np.asarray(baseline_samples)
        candidate_samples = np.asarray(candidate_samples)

        observed_delta = candidate_samples.mean() - baseline_samples.mean()

        bootstrap_deltas = []
        for _ in range(self.n_bootstrap):
            baseline_boot = self.rng.choice(
                baseline_samples, size=len(baseline_samples), replace=True
            )
            candidate_boot = self.rng.choice(
                candidate_samples, size=len(candidate_samples), replace=True
            )
            bootstrap_deltas.append(candidate_boot.mean() - baseline_boot.mean())

        bootstrap_deltas = np.array(bootstrap_deltas)
        alpha = 1 - self.confidence_level
        ci_lower = np.percentile(bootstrap_deltas, alpha / 2 * 100)
        ci_upper = np.percentile(bootstrap_deltas, (1 - alpha / 2) * 100)

        return observed_delta, ci_lower, ci_upper

    def permutation_test(
        self,
        baseline_samples: np.ndarray,
        candidate_samples: np.ndarray
    ) -> float:
        """
        Compute p-value using permutation test.

        Tests the null hypothesis that baseline and candidate
        come from the same distribution.

        Args:
            baseline_samples: Array of baseline metric values
            candidate_samples: Array of candidate metric values

        Returns:
            Two-sided p-value
        """
        baseline_samples = np.asarray(baseline_samples)
        candidate_samples = np.asarray(candidate_samples)

        observed_diff = abs(candidate_samples.mean() - baseline_samples.mean())
        combined = np.concatenate([baseline_samples, candidate_samples])
        n_baseline = len(baseline_samples)

        count_extreme = 0
        for _ in range(self.n_permutations):
            self.rng.shuffle(combined)
            perm_baseline = combined[:n_baseline]
            perm_candidate = combined[n_baseline:]
            perm_diff = abs(perm_candidate.mean() - perm_baseline.mean())
            if perm_diff >= observed_diff:
                count_extreme += 1

        return (count_extreme + 1) / (self.n_permutations + 1)

    def cohens_d(
        self,
        baseline_samples: np.ndarray,
        candidate_samples: np.ndarray
    ) -> float:
        """
        Compute Cohen's d effect size.

        Args:
            baseline_samples: Array of baseline metric values
            candidate_samples: Array of candidate metric values

        Returns:
            Cohen's d effect size
        """
        baseline_samples = np.asarray(baseline_samples)
        candidate_samples = np.asarray(candidate_samples)

        n1, n2 = len(baseline_samples), len(candidate_samples)
        var1, var2 = baseline_samples.var(ddof=1), candidate_samples.var(ddof=1)

        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

        if pooled_std == 0:
            return 0.0

        return (candidate_samples.mean() - baseline_samples.mean()) / pooled_std

    def power_analysis(
        self,
        effect_size: float,
        n_samples: int,
        alpha: float = 0.05
    ) -> float:
        """
        Estimate statistical power for detecting given effect size.

        Uses approximation based on normal distribution.

        Args:
            effect_size: Cohen's d effect size to detect
            n_samples: Number of samples per group
            alpha: Significance level

        Returns:
            Estimated power (probability of detecting effect if real)
        """
        from scipy import stats

        # Non-centrality parameter
        ncp = effect_size * np.sqrt(n_samples / 2)

        # Critical value for two-sided test
        critical = stats.norm.ppf(1 - alpha / 2)

        # Power calculation
        power = 1 - stats.norm.cdf(critical - ncp) + stats.norm.cdf(-critical - ncp)

        return power

    def samples_for_power(
        self,
        effect_size: float,
        target_power: float = 0.8,
        alpha: float = 0.05
    ) -> int:
        """
        Calculate sample size needed to achieve target power.

        Args:
            effect_size: Cohen's d effect size to detect
            target_power: Desired statistical power
            alpha: Significance level

        Returns:
            Required sample size per group
        """
        if effect_size == 0:
            return 999999  # Infinite samples needed for zero effect

        from scipy import stats

        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(target_power)

        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        return int(np.ceil(n))

    def analyze(
        self,
        baseline_samples: np.ndarray,
        candidate_samples: np.ndarray,
        alpha: float = 0.05
    ) -> StatisticalResult:
        """
        Perform complete statistical analysis.

        Args:
            baseline_samples: Array of baseline metric values
            candidate_samples: Array of candidate metric values
            alpha: Significance level

        Returns:
            StatisticalResult with all computed statistics
        """
        delta, ci_lower, ci_upper = self.bootstrap_ci(
            baseline_samples, candidate_samples
        )
        p_value = self.permutation_test(baseline_samples, candidate_samples)
        effect_size = self.cohens_d(baseline_samples, candidate_samples)

        n_samples = min(len(baseline_samples), len(candidate_samples))
        power = self.power_analysis(abs(effect_size), n_samples, alpha)
        samples_needed = self.samples_for_power(abs(effect_size), 0.8, alpha)

        return StatisticalResult(
            delta=delta,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            p_value=p_value,
            is_significant=p_value < alpha,
            effect_size=effect_size,
            power=power,
            samples_for_power_80=samples_needed
        )


def gate_with_significance(
    stat_result: StatisticalResult,
    threshold: float,
    higher_is_worse: bool = True
) -> str:
    """
    Make gating decision incorporating statistical significance.

    BLOCK only if:
    - CI lower bound exceeds threshold (regression is real)
    - Effect is statistically significant

    Args:
        stat_result: Result from statistical analysis
        threshold: Regression threshold for BLOCK
        higher_is_worse: Whether higher values indicate regression

    Returns:
        'OK', 'WARN', or 'BLOCK'
    """
    # Determine which CI bound to check
    if higher_is_worse:
        # For higher-is-worse, regression is positive delta
        # BLOCK if CI lower bound > threshold (confident regression)
        ci_bound = stat_result.ci_lower
        is_regression = stat_result.delta > 0
    else:
        # For lower-is-worse, regression is negative delta
        # BLOCK if CI upper bound < -threshold
        ci_bound = -stat_result.ci_upper
        is_regression = stat_result.delta < 0

    if not is_regression:
        return 'OK'

    if not stat_result.is_significant:
        return 'WARN'  # Trend but not significant

    if ci_bound > threshold:
        return 'BLOCK'  # Confident regression exceeds threshold
    elif abs(stat_result.delta) > threshold:
        return 'WARN'  # Point estimate exceeds but CI doesn't confirm
    else:
        return 'OK'
