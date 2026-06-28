"""
Metric Hacking Alerts

Detects patterns that suggest metric gaming rather than genuine improvement.

Goodhart's Law: "When a measure becomes a target, it ceases to be a good measure."

This module watches for:
1. Selective reporting: Only showing favorable runs
2. Threshold manipulation: Results clustering just above thresholds
3. Metric divergence: Official metrics improving while proxy metrics degrade
4. Timing anomalies: Submissions clustering near deadlines
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import statistics


class HackingType(Enum):
    """Types of metric hacking."""
    SELECTIVE_REPORTING = "selective_reporting"
    THRESHOLD_GAMING = "threshold_gaming"
    PROXY_DIVERGENCE = "proxy_divergence"
    TIMING_ANOMALY = "timing_anomaly"
    CHERRY_PICKING = "cherry_picking"


@dataclass
class HackingAlert:
    """A detected metric hacking signal."""
    hacking_type: HackingType
    severity: str  # "low", "medium", "high", "critical"
    evidence: Dict
    recommendation: str
    confidence: float
    flagged_runs: List[str] = field(default_factory=list)


@dataclass
class MetricHackingMonitor:
    """
    Monitors for metric gaming patterns.

    Design philosophy:
    - Assume good faith but verify
    - Detect patterns, not intent
    - Flag for human review, don't auto-reject
    """

    # Configuration
    selective_reporting_threshold: int = 3  # Min runs before checking
    threshold_cluster_epsilon: float = 0.02  # Distance from threshold to flag
    timing_anomaly_window_hours: int = 24  # Window for timing analysis

    def analyze_submission(
        self,
        current_run: Dict,
        historical_runs: List[Dict],
        all_runs_this_period: List[Dict],
        official_metrics: Dict[str, float],
        proxy_metrics: Optional[Dict[str, float]] = None,
        submission_time: Optional[datetime] = None,
        deadline: Optional[datetime] = None,
    ) -> List[HackingAlert]:
        """
        Analyze a submission for gaming signals.

        Args:
            current_run: The submitted evaluation run
            historical_runs: All previous runs from this team/model
            all_runs_this_period: All runs in the evaluation period
            official_metrics: The metrics used for gating
            proxy_metrics: Related metrics not used for gating
            submission_time: When this run was submitted
            deadline: Evaluation deadline if applicable
        """
        alerts = []

        # Check 1: Selective reporting
        selective_alert = self._check_selective_reporting(
            current_run, historical_runs
        )
        if selective_alert:
            alerts.append(selective_alert)

        # Check 2: Threshold gaming
        threshold_alert = self._check_threshold_gaming(
            official_metrics, all_runs_this_period
        )
        if threshold_alert:
            alerts.append(threshold_alert)

        # Check 3: Proxy metric divergence
        if proxy_metrics:
            proxy_alert = self._check_proxy_divergence(
                official_metrics, proxy_metrics, historical_runs
            )
            if proxy_alert:
                alerts.append(proxy_alert)

        # Check 4: Timing anomalies
        if submission_time and deadline:
            timing_alert = self._check_timing_anomaly(
                submission_time, deadline, all_runs_this_period
            )
            if timing_alert:
                alerts.append(timing_alert)

        # Check 5: Cherry-picking best run
        cherry_alert = self._check_cherry_picking(
            current_run, historical_runs
        )
        if cherry_alert:
            alerts.append(cherry_alert)

        return alerts

    def _check_selective_reporting(
        self,
        current_run: Dict,
        historical_runs: List[Dict],
    ) -> Optional[HackingAlert]:
        """Detect if only favorable runs are being reported."""

        if len(historical_runs) < self.selective_reporting_threshold:
            return None

        # Look at reported vs unreported run pattern
        reported_scores = [r.get("score", 0) for r in historical_runs if r.get("reported", False)]
        all_scores = [r.get("score", 0) for r in historical_runs]

        if not reported_scores or len(reported_scores) == len(all_scores):
            return None

        reported_avg = statistics.mean(reported_scores)
        all_avg = statistics.mean(all_scores)

        if reported_avg > all_avg * 1.2:  # Reported scores 20% higher
            return HackingAlert(
                hacking_type=HackingType.SELECTIVE_REPORTING,
                severity="medium",
                evidence={
                    "reported_avg": round(reported_avg, 3),
                    "all_runs_avg": round(all_avg, 3),
                    "ratio": round(reported_avg / all_avg, 3) if all_avg > 0 else 0,
                    "reported_count": len(reported_scores),
                    "total_count": len(all_scores),
                },
                recommendation=(
                    f"Reported runs ({reported_avg:.1%}) significantly outperform "
                    f"all runs ({all_avg:.1%}). This suggests selective reporting. "
                    "Consider requiring all runs to be submitted."
                ),
                confidence=0.7,
            )

        return None

    def _check_threshold_gaming(
        self,
        official_metrics: Dict[str, float],
        all_runs: List[Dict],
    ) -> Optional[HackingAlert]:
        """Detect if results cluster suspiciously near thresholds."""

        # Known thresholds (from constitution)
        thresholds = {
            "failure_rate": 0.12,  # BLOCK threshold
            "false_positive_rate": 0.05,  # BLOCK threshold
            "erosion_slope": -0.15,  # BLOCK threshold
        }

        flagged_metrics = []

        for metric, value in official_metrics.items():
            if metric not in thresholds:
                continue

            threshold = thresholds[metric]

            # Check if value is suspiciously close to threshold (on the good side)
            if metric in ["failure_rate", "false_positive_rate"]:
                # Lower is better, check if just under threshold
                distance = threshold - value
                if 0 < distance < self.threshold_cluster_epsilon:
                    flagged_metrics.append({
                        "metric": metric,
                        "value": value,
                        "threshold": threshold,
                        "distance": distance,
                    })
            else:
                # Higher is better (erosion_slope is negative, more negative is worse)
                distance = value - threshold
                if 0 < distance < self.threshold_cluster_epsilon:
                    flagged_metrics.append({
                        "metric": metric,
                        "value": value,
                        "threshold": threshold,
                        "distance": distance,
                    })

        if flagged_metrics:
            return HackingAlert(
                hacking_type=HackingType.THRESHOLD_GAMING,
                severity="high" if len(flagged_metrics) > 1 else "medium",
                evidence={
                    "flagged_metrics": flagged_metrics,
                    "epsilon": self.threshold_cluster_epsilon,
                },
                recommendation=(
                    f"Metrics cluster suspiciously close to thresholds: "
                    f"{[m['metric'] for m in flagged_metrics]}. "
                    "This pattern is unlikely by chance. Investigate if metrics "
                    "are being tuned to pass rather than genuinely improved."
                ),
                confidence=0.8,
            )

        return None

    def _check_proxy_divergence(
        self,
        official_metrics: Dict[str, float],
        proxy_metrics: Dict[str, float],
        historical_runs: List[Dict],
    ) -> Optional[HackingAlert]:
        """Detect if official metrics improve while proxy metrics degrade."""

        if len(historical_runs) < 3:
            return None

        # Compare trends
        official_trend = self._calculate_trend(
            [r.get("official_metrics", {}) for r in historical_runs]
        )
        proxy_trend = self._calculate_trend(
            [r.get("proxy_metrics", {}) for r in historical_runs]
        )

        # Flag if official improves but proxy degrades
        divergent_metrics = []

        for metric in official_trend:
            if metric in proxy_trend:
                if official_trend[metric] > 0 and proxy_trend.get(metric, 0) < -0.1:
                    divergent_metrics.append({
                        "metric": metric,
                        "official_trend": official_trend[metric],
                        "proxy_trend": proxy_trend[metric],
                    })

        if divergent_metrics:
            return HackingAlert(
                hacking_type=HackingType.PROXY_DIVERGENCE,
                severity="high",
                evidence={
                    "divergent_metrics": divergent_metrics,
                },
                recommendation=(
                    f"Official metrics improving while proxy metrics degrade: "
                    f"{[m['metric'] for m in divergent_metrics]}. "
                    "This suggests optimization for measured metrics at the expense "
                    "of underlying safety properties."
                ),
                confidence=0.75,
            )

        return None

    def _check_timing_anomaly(
        self,
        submission_time: datetime,
        deadline: datetime,
        all_runs: List[Dict],
    ) -> Optional[HackingAlert]:
        """Detect suspicious timing patterns."""

        time_to_deadline = deadline - submission_time
        hours_before = time_to_deadline.total_seconds() / 3600

        # Check if submitted very close to deadline
        if hours_before < 1:
            # Check if this run is significantly better than previous
            return HackingAlert(
                hacking_type=HackingType.TIMING_ANOMALY,
                severity="low",
                evidence={
                    "hours_before_deadline": round(hours_before, 2),
                    "submission_time": submission_time.isoformat(),
                    "deadline": deadline.isoformat(),
                },
                recommendation=(
                    f"Submission at {hours_before:.1f} hours before deadline. "
                    "Last-minute submissions sometimes indicate run-until-pass strategy. "
                    "Consider if multiple unreported attempts were made."
                ),
                confidence=0.5,
            )

        return None

    def _check_cherry_picking(
        self,
        current_run: Dict,
        historical_runs: List[Dict],
    ) -> Optional[HackingAlert]:
        """Detect if best run was cherry-picked from many attempts."""

        if len(historical_runs) < 5:
            return None

        current_score = current_run.get("score", 0)
        all_scores = [r.get("score", 0) for r in historical_runs] + [current_score]

        # Is current run the max?
        if current_score == max(all_scores):
            # Calculate how unusual this is
            mean_score = statistics.mean(all_scores)
            std_score = statistics.stdev(all_scores) if len(all_scores) > 1 else 0.01

            z_score = (current_score - mean_score) / std_score if std_score > 0 else 0

            if z_score > 2:  # More than 2 standard deviations above mean
                return HackingAlert(
                    hacking_type=HackingType.CHERRY_PICKING,
                    severity="medium",
                    evidence={
                        "current_score": round(current_score, 3),
                        "mean_score": round(mean_score, 3),
                        "std_score": round(std_score, 3),
                        "z_score": round(z_score, 2),
                        "num_runs": len(all_scores),
                    },
                    recommendation=(
                        f"Submitted run (score={current_score:.3f}) is {z_score:.1f} "
                        f"standard deviations above mean ({mean_score:.3f}). "
                        "This may indicate cherry-picking best run from many attempts. "
                        "Consider requiring mean or median of multiple runs."
                    ),
                    confidence=0.65,
                )

        return None

    def _calculate_trend(self, metrics_history: List[Dict]) -> Dict[str, float]:
        """Calculate trend (slope) for each metric over time."""
        trends = {}

        if len(metrics_history) < 2:
            return trends

        # Get all metric names
        all_metrics = set()
        for m in metrics_history:
            all_metrics.update(m.keys())

        for metric in all_metrics:
            values = [m.get(metric) for m in metrics_history if metric in m]
            values = [v for v in values if v is not None]

            if len(values) >= 2:
                # Simple trend: last - first (positive = improving)
                trends[metric] = values[-1] - values[0]

        return trends

    def get_alert_summary(self, alerts: List[HackingAlert]) -> Dict:
        """Summarize alerts for reporting."""

        if not alerts:
            return {
                "status": "CLEAN",
                "alert_count": 0,
                "recommendation": "No gaming signals detected.",
            }

        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        max_alert = max(alerts, key=lambda a: severity_order.get(a.severity, 0))

        status = (
            "BLOCK" if max_alert.severity == "critical"
            else "WARN" if max_alert.severity in ["high", "medium"]
            else "REVIEW"
        )

        return {
            "status": status,
            "alert_count": len(alerts),
            "max_severity": max_alert.severity,
            "alert_types": [a.hacking_type.value for a in alerts],
            "recommendation": max_alert.recommendation,
            "requires_human_review": status in ["WARN", "BLOCK"],
        }
