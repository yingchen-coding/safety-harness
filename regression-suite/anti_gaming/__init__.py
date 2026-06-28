"""
Anti-Gaming Subsystem

Protects release gates from metric gaming, overfitting, and adversarial optimization.

The Problem:
When safety metrics become targets, they become gameable. Teams may:
- Overfit to specific test cases
- Memorize regression suite answers
- Optimize for metrics instead of safety
- Selectively report favorable runs

This subsystem detects and flags these patterns.
"""

from .overfitting_detector import OverfittingDetector, OverfittingSignal
from .regression_memorization import MemorizationDetector, MemorizationResult
from .metric_hacking_alerts import MetricHackingMonitor, HackingAlert

__all__ = [
    "OverfittingDetector",
    "OverfittingSignal",
    "MemorizationDetector",
    "MemorizationResult",
    "MetricHackingMonitor",
    "HackingAlert",
]
