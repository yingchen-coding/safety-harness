"""
Pipeline configuration management.
"""

from dataclasses import dataclass, field
import json
import os


@dataclass
class EvalConfig:
    """Evaluation settings."""
    max_turns: int = 10
    timeout_seconds: int = 30
    retry_attempts: int = 3


@dataclass
class WorkerConfig:
    """Worker pool settings."""
    num_workers: int = 4
    rate_limit_rps: float = 10.0


@dataclass
class MonitoringConfig:
    """Monitoring and alerting settings."""
    drift_window_hours: int = 24
    erosion_threshold: float = 0.15
    failure_rate_threshold: float = 0.10
    alert_cooldown_minutes: int = 60


@dataclass
class StorageConfig:
    """Storage backend settings."""
    backend: str = "parquet"  # parquet, sqlite, duckdb
    base_path: str = "results"
    retention_days: int = 90


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    evaluation: EvalConfig = field(default_factory=EvalConfig)
    workers: WorkerConfig = field(default_factory=WorkerConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

    @classmethod
    def from_file(cls, path: str) -> 'PipelineConfig':
        """Load config from JSON file."""
        if not os.path.exists(path):
            return cls()

        with open(path) as f:
            data = json.load(f)

        return cls(
            evaluation=EvalConfig(**data.get('evaluation', {})),
            workers=WorkerConfig(**data.get('workers', {})),
            monitoring=MonitoringConfig(**data.get('monitoring', {})),
            storage=StorageConfig(**data.get('storage', {}))
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'evaluation': {
                'max_turns': self.evaluation.max_turns,
                'timeout_seconds': self.evaluation.timeout_seconds,
                'retry_attempts': self.evaluation.retry_attempts
            },
            'workers': {
                'num_workers': self.workers.num_workers,
                'rate_limit_rps': self.workers.rate_limit_rps
            },
            'monitoring': {
                'drift_window_hours': self.monitoring.drift_window_hours,
                'erosion_threshold': self.monitoring.erosion_threshold,
                'failure_rate_threshold': self.monitoring.failure_rate_threshold,
                'alert_cooldown_minutes': self.monitoring.alert_cooldown_minutes
            },
            'storage': {
                'backend': self.storage.backend,
                'base_path': self.storage.base_path,
                'retention_days': self.storage.retention_days
            }
        }
