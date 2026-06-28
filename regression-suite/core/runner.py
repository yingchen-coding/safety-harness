"""
Regression test runner that orchestrates baseline vs candidate evaluation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from adapters import MisuseAdapter, RedTeamAdapter, TrajectoryAdapter


@dataclass
class SuiteResult:
    """Results from a single evaluation suite."""
    suite: str
    model: str
    metrics: dict
    raw_result: dict


@dataclass
class RunResult:
    """Complete results from a regression run."""
    baseline_model: str
    candidate_model: str
    suites: list[str]
    baseline_results: dict[str, SuiteResult]
    candidate_results: dict[str, SuiteResult]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            'baseline_model': self.baseline_model,
            'candidate_model': self.candidate_model,
            'suites': self.suites,
            'baseline_results': {
                k: {'suite': v.suite, 'metrics': v.metrics}
                for k, v in self.baseline_results.items()
            },
            'candidate_results': {
                k: {'suite': v.suite, 'metrics': v.metrics}
                for k, v in self.candidate_results.items()
            },
            'timestamp': self.timestamp
        }


class RegressionRunner:
    """
    Orchestrates regression testing between baseline and candidate models.
    """

    AVAILABLE_SUITES = ['misuse', 'redteam', 'trajectory']

    def __init__(self):
        self.adapters = {
            'misuse': MisuseAdapter(),
            'redteam': RedTeamAdapter(),
            'trajectory': TrajectoryAdapter()
        }

    def run(
        self,
        baseline_model: str,
        candidate_model: str,
        suites: Optional[list[str]] = None,
        verbose: bool = False
    ) -> RunResult:
        """
        Run regression evaluation.

        Args:
            baseline_model: Baseline model identifier
            candidate_model: Candidate model identifier
            suites: List of suites to run (default: all)
            verbose: Print progress

        Returns:
            RunResult with all evaluation data
        """
        suites = suites or self.AVAILABLE_SUITES

        # Validate suites
        for suite in suites:
            if suite not in self.AVAILABLE_SUITES:
                raise ValueError(f"Unknown suite: {suite}")

        baseline_results = {}
        candidate_results = {}

        for suite in suites:
            if verbose:
                print(f"Running {suite} suite...")

            adapter = self.adapters[suite]

            # Run baseline
            if verbose:
                print(f"  Evaluating baseline: {baseline_model}")
            baseline_raw = adapter.run(baseline_model)
            baseline_metrics = adapter.get_metrics(baseline_raw)
            baseline_results[suite] = SuiteResult(
                suite=suite,
                model=baseline_model,
                metrics=baseline_metrics,
                raw_result=baseline_raw.to_dict()
            )

            # Run candidate
            if verbose:
                print(f"  Evaluating candidate: {candidate_model}")
            candidate_raw = adapter.run(candidate_model)
            candidate_metrics = adapter.get_metrics(candidate_raw)
            candidate_results[suite] = SuiteResult(
                suite=suite,
                model=candidate_model,
                metrics=candidate_metrics,
                raw_result=candidate_raw.to_dict()
            )

            if verbose:
                print("  Done.")

        return RunResult(
            baseline_model=baseline_model,
            candidate_model=candidate_model,
            suites=suites,
            baseline_results=baseline_results,
            candidate_results=candidate_results
        )

    def run_quick(self, verbose: bool = False) -> RunResult:
        """Run quick regression test with simulated models."""
        return self.run(
            baseline_model="model_v1",
            candidate_model="model_v2",
            suites=['misuse', 'redteam', 'trajectory'],
            verbose=verbose
        )
