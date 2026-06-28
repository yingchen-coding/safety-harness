"""
Alert dispatch system.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert to be dispatched."""
    id: str
    severity: AlertSeverity
    source: str
    message: str
    details: dict
    timestamp: str

    def to_dict(self) -> dict:
        result = asdict(self)
        result['severity'] = self.severity.value
        return result


class AlertDispatcher:
    """
    Dispatches alerts to configured channels.

    Channels (mock implementations):
    - Log file
    - Slack webhook
    - Email
    - PagerDuty
    """

    def __init__(
        self,
        log_path: str = "results/alerts.jsonl",
        slack_webhook: Optional[str] = None,
        email_config: Optional[dict] = None,
        cooldown_seconds: int = 300
    ):
        self.log_path = log_path
        self.slack_webhook = slack_webhook
        self.email_config = email_config
        self.cooldown_seconds = cooldown_seconds

        self._last_alert_time: dict[str, float] = {}
        self._alert_count = 0

        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def dispatch(self, drift_alert) -> bool:
        """
        Dispatch an alert from drift detection.

        Returns True if alert was sent, False if suppressed.
        """
        # Check cooldown
        alert_key = f"{drift_alert.metric}:{drift_alert.severity}"
        now = datetime.now().timestamp()

        if alert_key in self._last_alert_time:
            elapsed = now - self._last_alert_time[alert_key]
            if elapsed < self.cooldown_seconds:
                logger.debug(f"Alert suppressed (cooldown): {alert_key}")
                return False

        self._last_alert_time[alert_key] = now
        self._alert_count += 1

        # Create alert object
        alert = Alert(
            id=f"alert_{self._alert_count:06d}",
            severity=AlertSeverity(drift_alert.severity),
            source="drift_monitor",
            message=drift_alert.message,
            details={
                'metric': drift_alert.metric,
                'current_value': drift_alert.current_value,
                'threshold': drift_alert.threshold,
                'trend': drift_alert.trend
            },
            timestamp=drift_alert.timestamp
        )

        # Dispatch to all channels
        self._log_alert(alert)
        self._send_slack(alert)
        self._send_email(alert)

        return True

    def _log_alert(self, alert: Alert) -> None:
        """Log alert to file."""
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(alert.to_dict()) + "\n")
        logger.info(f"[ALERT] {alert.severity.value.upper()}: {alert.message}")

    def _send_slack(self, alert: Alert) -> None:
        """Send alert to Slack (mock)."""
        if not self.slack_webhook:
            return

        # In production, would use requests.post()
        logger.info(f"[SLACK] Would send to {self.slack_webhook}: {alert.message}")

    def _send_email(self, alert: Alert) -> None:
        """Send alert via email (mock)."""
        if not self.email_config:
            return

        # In production, would use smtplib
        logger.info(f"[EMAIL] Would send to {self.email_config.get('to')}: {alert.message}")

    def _send_pagerduty(self, alert: Alert) -> None:
        """Send alert to PagerDuty (mock)."""
        if alert.severity != AlertSeverity.CRITICAL:
            return

        # In production, would use PagerDuty API
        logger.info(f"[PAGERDUTY] Would page on-call: {alert.message}")

    def get_recent_alerts(self, limit: int = 10) -> list[dict]:
        """Get recent alerts from log."""
        if not os.path.exists(self.log_path):
            return []

        alerts = []
        with open(self.log_path) as f:
            for line in f:
                alerts.append(json.loads(line))

        return alerts[-limit:]

    def get_alert_summary(self) -> dict:
        """Get summary of alerts."""
        alerts = self.get_recent_alerts(limit=1000)

        by_severity = {}
        by_metric = {}

        for alert in alerts:
            sev = alert['severity']
            by_severity[sev] = by_severity.get(sev, 0) + 1

            metric = alert['details'].get('metric', 'unknown')
            by_metric[metric] = by_metric.get(metric, 0) + 1

        return {
            'total_alerts': len(alerts),
            'by_severity': by_severity,
            'by_metric': by_metric
        }
