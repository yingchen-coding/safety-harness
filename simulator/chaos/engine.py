"""
Chaos Engineering Engine

Core infrastructure for chaos experiments on safeguards.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Any, Callable
from enum import Enum
from datetime import datetime
import random


class DegradationLevel(Enum):
    """How well the system degraded under failure."""
    GRACEFUL = "graceful"      # System maintained safety with reduced functionality
    PARTIAL = "partial"        # Some safety preserved, some lost
    CATASTROPHIC = "catastrophic"  # Safety completely lost
    UNKNOWN = "unknown"


@dataclass
class ChaosResult:
    """Result of a chaos experiment."""

    experiment_name: str
    injection_type: str
    injection_config: Dict[str, Any]

    # Outcome
    degradation_level: DegradationLevel
    safety_maintained: bool
    functionality_maintained: bool

    # Evidence
    original_behavior: Dict[str, Any]
    chaos_behavior: Dict[str, Any]
    delta: Dict[str, Any]

    # Analysis
    root_cause: str
    recommendation: str
    confidence: float

    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "experiment_name": self.experiment_name,
            "injection_type": self.injection_type,
            "injection_config": self.injection_config,
            "degradation_level": self.degradation_level.value,
            "safety_maintained": self.safety_maintained,
            "functionality_maintained": self.functionality_maintained,
            "original_behavior": self.original_behavior,
            "chaos_behavior": self.chaos_behavior,
            "delta": self.delta,
            "root_cause": self.root_cause,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


class ChaosExperiment(Protocol):
    """Protocol for chaos experiment implementations."""

    def name(self) -> str:
        """Experiment name."""
        ...

    def inject(self, config: Dict) -> Callable:
        """Return a decorator/wrapper that injects the failure."""
        ...

    def analyze(
        self,
        original_results: Dict,
        chaos_results: Dict,
        config: Dict,
    ) -> ChaosResult:
        """Analyze the difference between original and chaos runs."""
        ...


@dataclass
class ChaosEngine:
    """
    Engine for running chaos experiments.

    Usage:
        engine = ChaosEngine()
        engine.register(DropSafeguardChaos())
        engine.register(DelayAlertingChaos())

        results = engine.run_all(
            safeguard_pipeline=pipeline,
            test_scenarios=scenarios,
        )

        for result in results:
            if not result.safety_maintained:
                print(f"FAILURE: {result.experiment_name}")
                print(f"  Root cause: {result.root_cause}")
                print(f"  Recommendation: {result.recommendation}")
    """

    experiments: Dict[str, ChaosExperiment] = field(default_factory=dict)
    random_seed: int = 42

    def __post_init__(self):
        random.seed(self.random_seed)

    def register(self, experiment: ChaosExperiment) -> None:
        """Register a chaos experiment."""
        self.experiments[experiment.name()] = experiment

    def run_experiment(
        self,
        experiment_name: str,
        safeguard_pipeline: Any,
        test_scenarios: List[Dict],
        config: Optional[Dict] = None,
    ) -> ChaosResult:
        """
        Run a single chaos experiment.

        Args:
            experiment_name: Name of registered experiment
            safeguard_pipeline: The safeguard pipeline to test
            test_scenarios: Test scenarios to run
            config: Experiment configuration

        Returns:
            ChaosResult with analysis
        """
        if experiment_name not in self.experiments:
            raise ValueError(f"Unknown experiment: {experiment_name}")

        experiment = self.experiments[experiment_name]
        config = config or {}

        # Run without chaos
        original_results = self._run_pipeline(safeguard_pipeline, test_scenarios)

        # Inject chaos
        chaos_wrapper = experiment.inject(config)

        # Run with chaos
        chaos_results = self._run_pipeline_with_chaos(
            safeguard_pipeline, test_scenarios, chaos_wrapper
        )

        # Analyze
        return experiment.analyze(original_results, chaos_results, config)

    def run_all(
        self,
        safeguard_pipeline: Any,
        test_scenarios: List[Dict],
        configs: Optional[Dict[str, Dict]] = None,
    ) -> List[ChaosResult]:
        """
        Run all registered chaos experiments.

        Args:
            safeguard_pipeline: The safeguard pipeline to test
            test_scenarios: Test scenarios to run
            configs: Per-experiment configurations

        Returns:
            List of ChaosResult objects
        """
        configs = configs or {}
        results = []

        for name, experiment in self.experiments.items():
            config = configs.get(name, {})
            try:
                result = self.run_experiment(
                    name, safeguard_pipeline, test_scenarios, config
                )
                results.append(result)
            except Exception as e:
                # Log but continue with other experiments
                print(f"Warning: {name} failed with {e}")

        return results

    def _run_pipeline(
        self,
        pipeline: Any,
        scenarios: List[Dict],
    ) -> Dict[str, Any]:
        """Run pipeline without chaos."""
        results = {
            "scenarios_run": len(scenarios),
            "blocked": 0,
            "warned": 0,
            "passed": 0,
            "alerts_fired": 0,
            "latencies_ms": [],
        }

        for scenario in scenarios:
            # Simulate pipeline execution
            # In real implementation, this would call the actual pipeline
            outcome = self._simulate_pipeline_run(pipeline, scenario)
            results["blocked"] += outcome.get("blocked", 0)
            results["warned"] += outcome.get("warned", 0)
            results["passed"] += outcome.get("passed", 0)
            results["alerts_fired"] += outcome.get("alerts", 0)
            results["latencies_ms"].append(outcome.get("latency_ms", 100))

        return results

    def _run_pipeline_with_chaos(
        self,
        pipeline: Any,
        scenarios: List[Dict],
        chaos_wrapper: Callable,
    ) -> Dict[str, Any]:
        """Run pipeline with chaos injection."""
        results = {
            "scenarios_run": len(scenarios),
            "blocked": 0,
            "warned": 0,
            "passed": 0,
            "alerts_fired": 0,
            "latencies_ms": [],
            "chaos_triggered": 0,
        }

        for scenario in scenarios:
            # Apply chaos wrapper
            outcome = chaos_wrapper(
                lambda: self._simulate_pipeline_run(pipeline, scenario)
            )()

            results["blocked"] += outcome.get("blocked", 0)
            results["warned"] += outcome.get("warned", 0)
            results["passed"] += outcome.get("passed", 0)
            results["alerts_fired"] += outcome.get("alerts", 0)
            results["latencies_ms"].append(outcome.get("latency_ms", 100))
            results["chaos_triggered"] += outcome.get("chaos_triggered", 0)

        return results

    def _simulate_pipeline_run(
        self,
        pipeline: Any,
        scenario: Dict,
    ) -> Dict:
        """Simulate a single pipeline run."""
        # Simplified simulation
        # Real implementation would execute actual pipeline

        is_attack = scenario.get("is_attack", random.random() > 0.7)

        if is_attack:
            # Safeguards should catch this
            if random.random() > 0.1:  # 90% detection rate
                return {"blocked": 1, "passed": 0, "warned": 0, "alerts": 1, "latency_ms": 150}
            else:
                return {"blocked": 0, "passed": 1, "warned": 0, "alerts": 0, "latency_ms": 100}
        else:
            # Benign scenario
            if random.random() > 0.95:  # 5% false positive rate
                return {"blocked": 1, "passed": 0, "warned": 0, "alerts": 1, "latency_ms": 120}
            else:
                return {"blocked": 0, "passed": 1, "warned": 0, "alerts": 0, "latency_ms": 80}

    def get_summary(self, results: List[ChaosResult]) -> Dict:
        """Summarize chaos experiment results."""

        graceful = [r for r in results if r.degradation_level == DegradationLevel.GRACEFUL]
        partial = [r for r in results if r.degradation_level == DegradationLevel.PARTIAL]
        catastrophic = [r for r in results if r.degradation_level == DegradationLevel.CATASTROPHIC]

        safety_maintained = [r for r in results if r.safety_maintained]

        status = (
            "PASS" if len(catastrophic) == 0 and len(safety_maintained) == len(results)
            else "WARN" if len(catastrophic) == 0
            else "FAIL"
        )

        return {
            "status": status,
            "total_experiments": len(results),
            "graceful_degradation": len(graceful),
            "partial_degradation": len(partial),
            "catastrophic_failure": len(catastrophic),
            "safety_maintained": len(safety_maintained),
            "critical_issues": [
                {
                    "experiment": r.experiment_name,
                    "root_cause": r.root_cause,
                    "recommendation": r.recommendation,
                }
                for r in catastrophic
            ],
        }
