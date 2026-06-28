"""
Base classes for safeguards.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class SafeguardLevel(Enum):
    """Severity levels for safeguard responses."""
    PASS = "pass"           # No issues detected
    WARN = "warn"           # Minor concern, log but continue
    SOFT_STOP = "soft_stop" # Pause and ask for clarification
    HARD_STOP = "hard_stop" # Block execution


@dataclass
class SafeguardResult:
    """Result of a safeguard check."""
    level: SafeguardLevel
    score: float  # 0-1, higher = more concerning
    reason: str
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    @property
    def blocked(self) -> bool:
        return self.level == SafeguardLevel.HARD_STOP

    @property
    def soft_stop(self) -> bool:
        return self.level == SafeguardLevel.SOFT_STOP

    @property
    def hard_stop(self) -> bool:
        return self.level == SafeguardLevel.HARD_STOP

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "score": self.score,
            "reason": self.reason,
            "blocked": self.blocked,
            "soft_stop": self.soft_stop,
            "hard_stop": self.hard_stop,
            **self.details
        }


class BaseSafeguard(ABC):
    """
    Abstract base class for safeguards.

    Safeguards can be:
    - Pre-action: Check before tool execution
    - Mid-trajectory: Monitor during execution
    - Post-action: Audit after completion
    """

    name: str = "base"
    description: str = "Base safeguard"

    def __init__(self, sensitivity: float = 0.5):
        """
        Initialize safeguard.

        Args:
            sensitivity: 0-1, higher = more sensitive (more likely to trigger)
        """
        self.sensitivity = sensitivity

    @abstractmethod
    def check(self, *args, **kwargs) -> SafeguardResult:
        """Run the safeguard check."""
        pass

    def adjust_threshold(self, base_threshold: float) -> float:
        """Adjust threshold based on sensitivity."""
        # Higher sensitivity = lower threshold = easier to trigger
        return base_threshold * (1 - self.sensitivity * 0.5)
