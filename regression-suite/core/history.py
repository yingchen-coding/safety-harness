"""
Longitudinal trend tracking for safety metrics across releases.

Stores historical run results and detects slow erosion patterns
that might be missed in pairwise comparisons.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import numpy as np


@dataclass
class HistoricalRun:
    """Single historical regression run."""
    run_id: str
    timestamp: str
    model_version: str
    metrics: dict[str, float]
    verdict: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'HistoricalRun':
        return cls(**data)


@dataclass
class TrendAnalysis:
    """Result of trend analysis across versions."""
    metric: str
    values: list[float]
    versions: list[str]
    slope: float
    r_squared: float
    is_eroding: bool
    projected_threshold_breach: Optional[int]  # Releases until breach
    recommendation: str

    def to_dict(self) -> dict:
        return {
            'metric': self.metric,
            'values': [round(v, 4) for v in self.values],
            'versions': self.versions,
            'slope': round(self.slope, 6),
            'r_squared': round(self.r_squared, 4),
            'is_eroding': self.is_eroding,
            'projected_threshold_breach': self.projected_threshold_breach,
            'recommendation': self.recommendation
        }


class HistoryStore:
    """
    Persistent storage for historical regression results.

    Stores results in JSON format for simplicity.
    Production systems would use a proper database.
    """

    def __init__(self, storage_path: str = 'data/history.json'):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._runs: list[HistoricalRun] = []
        self._load()

    def _load(self) -> None:
        """Load history from disk."""
        if self.storage_path.exists():
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self._runs = [HistoricalRun.from_dict(r) for r in data]

    def _save(self) -> None:
        """Persist history to disk."""
        with open(self.storage_path, 'w') as f:
            json.dump([r.to_dict() for r in self._runs], f, indent=2)

    def add_run(self, run: HistoricalRun) -> None:
        """Add a new run to history."""
        self._runs.append(run)
        self._save()

    def get_runs(
        self,
        limit: Optional[int] = None,
        metric: Optional[str] = None
    ) -> list[HistoricalRun]:
        """
        Retrieve historical runs.

        Args:
            limit: Maximum number of runs to return (most recent)
            metric: Filter to runs containing this metric

        Returns:
            List of HistoricalRun objects
        """
        runs = self._runs

        if metric:
            runs = [r for r in runs if metric in r.metrics]

        runs = sorted(runs, key=lambda r: r.timestamp, reverse=True)

        if limit:
            runs = runs[:limit]

        return list(reversed(runs))  # Chronological order

    def get_metric_series(self, metric: str) -> tuple[list[str], list[float]]:
        """
        Get time series for a specific metric.

        Args:
            metric: Metric name

        Returns:
            Tuple of (versions, values)
        """
        runs = self.get_runs(metric=metric)
        versions = [r.model_version for r in runs]
        values = [r.metrics[metric] for r in runs]
        return versions, values

    def clear(self) -> None:
        """Clear all history."""
        self._runs = []
        self._save()


class TrendAnalyzer:
    """
    Analyze trends in safety metrics over time.

    Detects slow erosion that might be missed in pairwise comparisons.
    """

    def __init__(
        self,
        erosion_threshold: float = 0.01,
        min_runs: int = 3
    ):
        self.erosion_threshold = erosion_threshold
        self.min_runs = min_runs

    def linear_regression(
        self,
        values: list[float]
    ) -> tuple[float, float]:
        """
        Fit linear regression to values.

        Args:
            values: List of metric values in chronological order

        Returns:
            Tuple of (slope, r_squared)
        """
        if len(values) < 2:
            return 0.0, 0.0

        x = np.arange(len(values))
        y = np.array(values)

        # Linear regression
        n = len(values)
        sum_x = x.sum()
        sum_y = y.sum()
        sum_xy = (x * y).sum()
        sum_x2 = (x ** 2).sum()

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

        # R-squared
        y_pred = slope * x + (sum_y - slope * sum_x) / n
        ss_res = ((y - y_pred) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

        return slope, r_squared

    def project_breach(
        self,
        current_value: float,
        slope: float,
        threshold: float,
        higher_is_worse: bool = True
    ) -> Optional[int]:
        """
        Project when threshold will be breached at current erosion rate.

        Args:
            current_value: Current metric value
            slope: Erosion slope per release
            threshold: Threshold value
            higher_is_worse: Whether higher values are worse

        Returns:
            Number of releases until breach, or None if not applicable
        """
        if slope == 0:
            return None

        if higher_is_worse:
            if current_value >= threshold:
                return 0  # Already breached
            if slope <= 0:
                return None  # Improving, won't breach
            releases = (threshold - current_value) / slope
        else:
            if current_value <= threshold:
                return 0  # Already breached
            if slope >= 0:
                return None  # Improving, won't breach
            releases = (current_value - threshold) / abs(slope)

        return int(np.ceil(releases)) if releases > 0 else None

    def analyze_metric(
        self,
        metric: str,
        versions: list[str],
        values: list[float],
        threshold: float,
        higher_is_worse: bool = True
    ) -> TrendAnalysis:
        """
        Analyze trend for a single metric.

        Args:
            metric: Metric name
            versions: List of version identifiers
            values: List of metric values
            threshold: Warning threshold
            higher_is_worse: Whether higher values are worse

        Returns:
            TrendAnalysis result
        """
        if len(values) < self.min_runs:
            return TrendAnalysis(
                metric=metric,
                values=values,
                versions=versions,
                slope=0.0,
                r_squared=0.0,
                is_eroding=False,
                projected_threshold_breach=None,
                recommendation=f'Insufficient data (need {self.min_runs} runs)'
            )

        slope, r_squared = self.linear_regression(values)

        # Determine if eroding
        if higher_is_worse:
            is_eroding = slope > self.erosion_threshold
        else:
            is_eroding = slope < -self.erosion_threshold

        # Project breach
        current_value = values[-1]
        breach_releases = self.project_breach(
            current_value, slope, threshold, higher_is_worse
        )

        # Generate recommendation
        if is_eroding and r_squared > 0.7:
            if breach_releases and breach_releases <= 3:
                recommendation = f'CRITICAL: Threshold breach projected in {breach_releases} releases'
            elif breach_releases and breach_releases <= 10:
                recommendation = f'WARNING: Slow erosion detected, breach in ~{breach_releases} releases'
            else:
                recommendation = 'MONITOR: Erosion trend detected but not urgent'
        elif is_eroding:
            recommendation = 'INVESTIGATE: Possible erosion but low confidence (noisy data)'
        else:
            recommendation = 'OK: No significant erosion trend'

        return TrendAnalysis(
            metric=metric,
            values=values,
            versions=versions,
            slope=slope,
            r_squared=r_squared,
            is_eroding=is_eroding,
            projected_threshold_breach=breach_releases,
            recommendation=recommendation
        )

    def analyze_all(
        self,
        history_store: HistoryStore,
        thresholds: dict[str, float],
        higher_is_worse: dict[str, bool]
    ) -> list[TrendAnalysis]:
        """
        Analyze trends for all metrics in history.

        Args:
            history_store: HistoryStore instance
            thresholds: Dict mapping metric name to threshold
            higher_is_worse: Dict mapping metric name to direction

        Returns:
            List of TrendAnalysis results
        """
        results = []

        for metric, threshold in thresholds.items():
            versions, values = history_store.get_metric_series(metric)
            if not values:
                continue

            analysis = self.analyze_metric(
                metric=metric,
                versions=versions,
                values=values,
                threshold=threshold,
                higher_is_worse=higher_is_worse.get(metric, True)
            )
            results.append(analysis)

        return results


def generate_trend_report(analyses: list[TrendAnalysis]) -> str:
    """
    Generate markdown report of trend analyses.

    Args:
        analyses: List of TrendAnalysis results

    Returns:
        Markdown formatted report
    """
    lines = ['# Safety Trend Report\n']

    # Summary
    eroding = [a for a in analyses if a.is_eroding]
    critical = [a for a in eroding if a.projected_threshold_breach and a.projected_threshold_breach <= 3]

    lines.append('## Summary\n')
    lines.append(f'- Metrics analyzed: {len(analyses)}')
    lines.append(f'- Eroding trends: {len(eroding)}')
    lines.append(f'- Critical (breach ≤3 releases): {len(critical)}\n')

    # Critical alerts
    if critical:
        lines.append('## Critical Alerts\n')
        for a in critical:
            lines.append(f'- **{a.metric}**: {a.recommendation}')
        lines.append('')

    # Detailed analysis
    lines.append('## Metric Details\n')
    lines.append('| Metric | Slope | R² | Eroding | Breach In | Recommendation |')
    lines.append('|--------|-------|----|---------|-----------|--------------------|')

    for a in analyses:
        breach = str(a.projected_threshold_breach) if a.projected_threshold_breach else '-'
        eroding_mark = '⚠️' if a.is_eroding else '✓'
        lines.append(
            f'| {a.metric} | {a.slope:.4f} | {a.r_squared:.2f} | '
            f'{eroding_mark} | {breach} | {a.recommendation.split(":")[0]} |'
        )

    return '\n'.join(lines)
