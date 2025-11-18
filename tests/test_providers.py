"""Tests for provider ecosystem."""

import pytest
from codex_prime.providers.router import ProviderRouter, TaskComplexity, ProviderConfig
from codex_prime.providers.base import BaseProvider


class MockProvider(BaseProvider):
    """Mock provider for testing."""

    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.call_count = 0

    def chat(self, system: str, messages: list[dict[str, str]], temperature: float = 0.4) -> str:
        self.call_count += 1
        if self.should_fail:
            raise Exception(f"{self.name} failed")
        return f"Response from {self.name}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


def test_router_creation():
    """Test creating a router."""
    router = ProviderRouter()
    assert router.stats['total_requests'] == 0


def test_register_provider():
    """Test registering providers."""
    router = ProviderRouter()
    provider = MockProvider("test")

    router.register_provider(
        name="test",
        provider=provider,
        cost_per_1k_tokens=0.01,
        complexity_levels=[TaskComplexity.SIMPLE],
        priority=1
    )

    assert "test" in router.providers
    assert router.providers["test"].name == "test"


def test_complexity_estimation():
    """Test complexity estimation heuristic."""
    router = ProviderRouter()

    # Simple task
    simple = router._default_complexity_estimator("What is Python?")
    assert simple == TaskComplexity.SIMPLE

    # Complex task
    complex_prompt = router._default_complexity_estimator(
        "Design a comprehensive distributed system architecture"
    )
    assert complex_prompt == TaskComplexity.COMPLEX

    # Moderate task (default)
    moderate = router._default_complexity_estimator("Write a function to sort a list")
    assert moderate == TaskComplexity.MODERATE


def test_provider_selection_by_complexity():
    """Test provider selection based on complexity."""
    router = ProviderRouter()

    cheap = MockProvider("cheap")
    expensive = MockProvider("expensive")

    router.register_provider(
        name="cheap",
        provider=cheap,
        cost_per_1k_tokens=0.001,
        complexity_levels=[TaskComplexity.SIMPLE],
        priority=1
    )

    router.register_provider(
        name="expensive",
        provider=expensive,
        cost_per_1k_tokens=0.03,
        complexity_levels=[TaskComplexity.COMPLEX],
        priority=2
    )

    # Simple task should select cheap provider
    config = router.select_provider("What is 2+2?", complexity=TaskComplexity.SIMPLE)
    assert config.name == "cheap"

    # Complex task should select expensive provider
    config = router.select_provider(
        "Design a system",
        complexity=TaskComplexity.COMPLEX
    )
    assert config.name == "expensive"


def test_provider_selection_by_priority():
    """Test provider selection respects priority."""
    router = ProviderRouter()

    low = MockProvider("low")
    high = MockProvider("high")

    router.register_provider(
        name="low",
        provider=low,
        cost_per_1k_tokens=0.01,
        complexity_levels=[TaskComplexity.MODERATE],
        priority=1
    )

    router.register_provider(
        name="high",
        provider=high,
        cost_per_1k_tokens=0.01,
        complexity_levels=[TaskComplexity.MODERATE],
        priority=5
    )

    # Should select high priority provider
    config = router.select_provider("Test", complexity=TaskComplexity.MODERATE)
    assert config.name == "high"


def test_chat_routing():
    """Test chat request routing."""
    router = ProviderRouter()
    provider = MockProvider("test")

    router.register_provider(
        name="test",
        provider=provider,
        cost_per_1k_tokens=0.01,
        complexity_levels=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
        priority=1
    )

    response = router.chat(
        system="You are helpful",
        messages=[{"role": "user", "content": "Hello"}],
        complexity=TaskComplexity.SIMPLE
    )

    assert response == "Response from test"
    assert provider.call_count == 1
    assert router.stats['total_requests'] == 1


def test_fallback_on_failure():
    """Test fallback to next provider on failure."""
    router = ProviderRouter()

    failing = MockProvider("failing", should_fail=True)
    working = MockProvider("working", should_fail=False)

    router.register_provider(
        name="failing",
        provider=failing,
        cost_per_1k_tokens=0.01,
        complexity_levels=[TaskComplexity.SIMPLE],
        priority=2  # Higher priority
    )

    router.register_provider(
        name="working",
        provider=working,
        cost_per_1k_tokens=0.02,
        complexity_levels=[TaskComplexity.SIMPLE],
        priority=1  # Lower priority
    )

    response = router.chat(
        system="Test",
        messages=[{"role": "user", "content": "Hello"}],
        complexity=TaskComplexity.SIMPLE
    )

    # Should have fallen back to working provider
    assert response == "Response from working"
    assert failing.call_count == 1
    assert working.call_count == 1
    assert router.stats['fallbacks'] == 1


def test_all_providers_fail():
    """Test error when all providers fail."""
    router = ProviderRouter()

    failing1 = MockProvider("failing1", should_fail=True)
    failing2 = MockProvider("failing2", should_fail=True)

    router.register_provider(
        name="failing1",
        provider=failing1,
        cost_per_1k_tokens=0.01,
        complexity_levels=[TaskComplexity.SIMPLE],
        priority=1
    )

    router.register_provider(
        name="failing2",
        provider=failing2,
        cost_per_1k_tokens=0.01,
        complexity_levels=[TaskComplexity.SIMPLE],
        priority=1
    )

    with pytest.raises(RuntimeError, match="All providers failed"):
        router.chat(
            system="Test",
            messages=[{"role": "user", "content": "Hello"}],
            complexity=TaskComplexity.SIMPLE
        )


def test_stats_tracking():
    """Test statistics tracking."""
    router = ProviderRouter()
    provider = MockProvider("test")

    router.register_provider(
        name="test",
        provider=provider,
        cost_per_1k_tokens=0.01,
        complexity_levels=[TaskComplexity.SIMPLE],
        priority=1
    )

    # Make several requests
    for i in range(3):
        router.chat(
            system="Test",
            messages=[{"role": "user", "content": f"Message {i}"}],
            complexity=TaskComplexity.SIMPLE
        )

    stats = router.get_stats()

    assert stats['total_requests'] == 3
    assert stats['by_provider']['test'] == 3
    assert stats['total_cost'] > 0


def test_reset_stats():
    """Test resetting statistics."""
    router = ProviderRouter()
    provider = MockProvider("test")

    router.register_provider(
        name="test",
        provider=provider,
        cost_per_1k_tokens=0.01,
        complexity_levels=[TaskComplexity.SIMPLE],
        priority=1
    )

    router.chat(
        system="Test",
        messages=[{"role": "user", "content": "Hello"}],
        complexity=TaskComplexity.SIMPLE
    )

    assert router.stats['total_requests'] == 1

    router.reset_stats()

    assert router.stats['total_requests'] == 0
    assert router.stats['by_provider']['test'] == 0
