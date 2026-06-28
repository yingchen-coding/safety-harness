"""
Metrics storage backend with Parquet support.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional

# Try to import pandas/pyarrow, fall back to JSON if not available
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


@dataclass
class RunMetadata:
    """Metadata for an evaluation run."""
    run_id: str
    tag: str
    models: list[str]
    scenario_version: str
    timestamp: str
    config: dict


class MetricsStore:
    """
    Persistent storage for evaluation metrics.

    Supports:
    - Parquet (recommended for analytics)
    - JSON (fallback)
    """

    def __init__(self, base_path: str = "results", backend: str = "parquet"):
        self.base_path = base_path
        self.backend = backend if HAS_PANDAS else "json"
        os.makedirs(base_path, exist_ok=True)

    def save_run(
        self,
        run_id: str,
        results: list[dict],
        metadata: RunMetadata
    ) -> dict[str, str]:
        """
        Save evaluation run results.

        Returns dict of saved file paths.
        """
        run_path = os.path.join(self.base_path, run_id)
        os.makedirs(run_path, exist_ok=True)

        paths = {}

        # Save metadata
        meta_path = os.path.join(run_path, "metadata.json")
        with open(meta_path, 'w') as f:
            json.dump({
                'run_id': metadata.run_id,
                'tag': metadata.tag,
                'models': metadata.models,
                'scenario_version': metadata.scenario_version,
                'timestamp': metadata.timestamp,
                'config': metadata.config
            }, f, indent=2)
        paths['metadata'] = meta_path

        # Save results
        if self.backend == "parquet" and HAS_PANDAS:
            paths.update(self._save_parquet(run_path, results))
        else:
            paths.update(self._save_json(run_path, results))

        return paths

    def _save_parquet(self, run_path: str, results: list[dict]) -> dict[str, str]:
        """Save results as Parquet files."""
        paths = {}

        # Flatten results for DataFrame
        flat_results = []
        turn_results = []

        for r in results:
            flat_results.append({
                'scenario_id': r['scenario_id'],
                'model': r['model'],
                'final_status': r['final_status'],
                'first_failure_turn': r['first_failure_turn'],
                'total_violations': r['total_violations'],
                'total_latency_ms': r['total_latency_ms'],
                'timestamp': r['timestamp']
            })

            for turn in r.get('turns', []):
                turn_results.append({
                    'scenario_id': r['scenario_id'],
                    'model': r['model'],
                    'turn': turn['turn'],
                    'status': turn['status'],
                    'latency_ms': turn['latency_ms']
                })

        # Save main metrics
        metrics_path = os.path.join(run_path, "metrics.parquet")
        pd.DataFrame(flat_results).to_parquet(metrics_path, index=False)
        paths['metrics'] = metrics_path

        # Save turn-level data
        if turn_results:
            turns_path = os.path.join(run_path, "turns.parquet")
            pd.DataFrame(turn_results).to_parquet(turns_path, index=False)
            paths['turns'] = turns_path

        return paths

    def _save_json(self, run_path: str, results: list[dict]) -> dict[str, str]:
        """Save results as JSON (fallback)."""
        paths = {}

        results_path = os.path.join(run_path, "results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        paths['results'] = results_path

        return paths

    def load_run(self, run_id: str) -> tuple[RunMetadata, list[dict]]:
        """Load results from a previous run."""
        run_path = os.path.join(self.base_path, run_id)

        if not os.path.exists(run_path):
            raise ValueError(f"Run '{run_id}' not found")

        # Load metadata
        meta_path = os.path.join(run_path, "metadata.json")
        with open(meta_path) as f:
            meta_data = json.load(f)
        metadata = RunMetadata(**meta_data)

        # Load results
        if self.backend == "parquet" and HAS_PANDAS:
            metrics_path = os.path.join(run_path, "metrics.parquet")
            if os.path.exists(metrics_path):
                df = pd.read_parquet(metrics_path)
                results = df.to_dict('records')
            else:
                results = []
        else:
            results_path = os.path.join(run_path, "results.json")
            with open(results_path) as f:
                results = json.load(f)

        return metadata, results

    def list_runs(self, tag: Optional[str] = None) -> list[str]:
        """List available runs, optionally filtered by tag."""
        runs = []
        for name in os.listdir(self.base_path):
            run_path = os.path.join(self.base_path, name)
            if os.path.isdir(run_path):
                meta_path = os.path.join(run_path, "metadata.json")
                if os.path.exists(meta_path):
                    if tag:
                        with open(meta_path) as f:
                            meta = json.load(f)
                        if meta.get('tag') == tag:
                            runs.append(name)
                    else:
                        runs.append(name)
        return sorted(runs)

    def compute_summary(self, run_id: str) -> dict:
        """Compute summary statistics for a run."""
        _, results = self.load_run(run_id)

        if not results:
            return {'error': 'No results'}

        total = len(results)
        violations = sum(1 for r in results if r['final_status'] == 'violation')
        hedging = sum(1 for r in results if r['final_status'] == 'hedging')
        compliant = sum(1 for r in results if r['final_status'] == 'compliant')

        failure_turns = [r['first_failure_turn'] for r in results if r['first_failure_turn']]
        avg_failure_turn = sum(failure_turns) / len(failure_turns) if failure_turns else None

        latencies = [r['total_latency_ms'] for r in results]

        return {
            'total_scenarios': total,
            'violation_count': violations,
            'violation_rate': violations / total if total > 0 else 0,
            'hedging_count': hedging,
            'compliant_count': compliant,
            'avg_first_failure_turn': avg_failure_turn,
            'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0,
            'p99_latency_ms': sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
        }
