"""
Model API client abstraction.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import random
import time


@dataclass
class ModelResponse:
    """Response from model API."""
    content: str
    model: str
    latency_ms: float
    tokens_used: int = 0


class ModelClient(ABC):
    """Abstract model client interface."""

    @abstractmethod
    def chat(self, messages: list[dict], model: str) -> ModelResponse:
        """Send chat request to model."""
        pass


class SimulatedModelClient(ModelClient):
    """
    Simulated model client for testing.

    Produces realistic-looking responses with configurable failure rates.
    """

    def __init__(
        self,
        base_failure_rate: float = 0.2,
        latency_range: tuple[float, float] = (100, 500)
    ):
        self.base_failure_rate = base_failure_rate
        self.latency_range = latency_range

    def chat(self, messages: list[dict], model: str) -> ModelResponse:
        """Simulate model response."""
        start = time.time()

        # Simulate latency
        latency = random.uniform(*self.latency_range)
        time.sleep(latency / 1000)

        # Calculate turn-dependent failure rate
        turn = len([m for m in messages if m.get('role') == 'user'])
        failure_rate = self.base_failure_rate * (1 + turn * 0.1)

        # Generate response
        if random.random() < failure_rate:
            # Simulated violation
            content = self._generate_violation_response(messages)
        elif random.random() < 0.2:
            # Simulated hedging
            content = self._generate_hedging_response(messages)
        else:
            # Simulated compliant response
            content = self._generate_compliant_response(messages)

        actual_latency = (time.time() - start) * 1000

        return ModelResponse(
            content=content,
            model=model,
            latency_ms=actual_latency,
            tokens_used=random.randint(50, 200)
        )

    def _generate_violation_response(self, messages: list[dict]) -> str:
        """Generate a response that simulates a policy violation."""
        responses = [
            "Here's how you can approach this: First, you'll need to...",
            "I can help with that. Step 1: Start by...",
            "Sure, here's a detailed guide:\n1. First...\n2. Then...",
            "The best approach would be to:\n```\n# Code example\n```",
        ]
        return random.choice(responses)

    def _generate_hedging_response(self, messages: list[dict]) -> str:
        """Generate a response with hedging language."""
        responses = [
            "I should note some concerns about this request, but hypothetically...",
            "While I have reservations, I can provide general information...",
            "This is a sensitive topic. In theory, one might consider...",
            "I'm not entirely comfortable with this, however...",
        ]
        return random.choice(responses)

    def _generate_compliant_response(self, messages: list[dict]) -> str:
        """Generate a policy-compliant refusal."""
        responses = [
            "I cannot assist with this request as it may violate safety guidelines.",
            "I'm not able to help with that particular task.",
            "I must decline this request. Is there something else I can help with?",
            "This falls outside what I can assist with. Let me suggest an alternative...",
        ]
        return random.choice(responses)


class OpenAIClient(ModelClient):
    """OpenAI API client (stub for production use)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # In production: self.client = openai.OpenAI(api_key=api_key)

    def chat(self, messages: list[dict], model: str) -> ModelResponse:
        """Call OpenAI API."""
        # Stub - would use actual API in production
        raise NotImplementedError("OpenAI client requires API key configuration")


class AnthropicClient(ModelClient):
    """Anthropic API client (stub for production use)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # In production: self.client = anthropic.Anthropic(api_key=api_key)

    def chat(self, messages: list[dict], model: str) -> ModelResponse:
        """Call Anthropic API."""
        # Stub - would use actual API in production
        raise NotImplementedError("Anthropic client requires API key configuration")
