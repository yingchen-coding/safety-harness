"""
Base adapter protocol for evaluation suite integration.

All adapters must implement this interface to be compatible with the
regression suite orchestration layer.
"""

from typing import Protocol, Dict, Any, runtime_checkable
from dataclasses import dataclass


@dataclass
class AdapterResult:
    """Standardized result from an evaluation adapter."""
    suite_name: str
    metrics: Dict[str, float]
    metadata: Dict[str, Any]
    raw_results: Any = None


@runtime_checkable
class EvalAdapter(Protocol):
    """
    Protocol for evaluation suite adapters.

    Adapters wrap external evaluation tools (misuse benchmarks, red-team
    harnesses, trajectory analyzers) and provide a consistent interface
    for the regression suite.

    Example implementation:
        class MyAdapter:
            def run(self, model_id: str) -> AdapterResult:
                # Run evaluation
                results = my_eval_tool.evaluate(model_id)
                # Extract standardized metrics
                return AdapterResult(
                    suite_name="my_suite",
                    metrics={"violation_rate": results.violations / results.total},
                    metadata={"version": my_eval_tool.__version__}
                )

            @property
            def suite_name(self) -> str:
                return "my_suite"

            @property
            def metrics_schema(self) -> Dict[str, str]:
                return {"violation_rate": "higher_is_worse"}
    """

    def run(self, model_id: str) -> AdapterResult:
        """
        Run the evaluation suite against a model.

        Args:
            model_id: Identifier for the model to evaluate

        Returns:
            AdapterResult with standardized metrics
        """
        ...

    @property
    def suite_name(self) -> str:
        """Unique identifier for this evaluation suite."""
        ...

    @property
    def metrics_schema(self) -> Dict[str, str]:
        """
        Schema describing metrics and their direction.

        Returns:
            Dict mapping metric name to direction:
            - "higher_is_worse": Higher values indicate safety regression
            - "lower_is_worse": Lower values indicate safety regression
        """
        ...


def validate_adapter(adapter: Any) -> bool:
    """
    Validate that an object implements the EvalAdapter protocol.

    Args:
        adapter: Object to validate

    Returns:
        True if adapter implements protocol correctly
    """
    if not isinstance(adapter, EvalAdapter):
        return False

    # Check required properties exist
    try:
        _ = adapter.suite_name
        _ = adapter.metrics_schema
    except (AttributeError, NotImplementedError):
        return False

    return True
