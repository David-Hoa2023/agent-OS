"""Intelligent provider routing for cost optimization and fallback."""

from typing import Optional, List, Dict, Any, Callable
from enum import Enum
import time
from dataclasses import dataclass, field

from .base import BaseProvider


class TaskComplexity(Enum):
    """Task complexity levels for routing decisions."""
    SIMPLE = "simple"        # Simple tasks, cheap models OK
    MODERATE = "moderate"    # Standard tasks, mid-tier models
    COMPLEX = "complex"      # Complex tasks, premium models


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    provider: BaseProvider
    name: str
    cost_per_1k_tokens: float
    max_tokens: int = 4096
    complexity_levels: List[TaskComplexity] = field(default_factory=lambda: [TaskComplexity.MODERATE])
    priority: int = 1  # Higher number = higher priority


class ProviderRouter:
    """Route requests to optimal provider based on task and fallback chain."""

    def __init__(
        self,
        complexity_estimator: Optional[Callable[[str], TaskComplexity]] = None
    ):
        """
        Initialize router.

        Args:
            complexity_estimator: Function to estimate task complexity from prompt
        """
        self.providers: Dict[str, ProviderConfig] = {}
        self.complexity_estimator = complexity_estimator or self._default_complexity_estimator
        self.stats = {
            'total_requests': 0,
            'by_provider': {},
            'by_complexity': {},
            'total_cost': 0.0,
            'fallbacks': 0
        }

    def register_provider(
        self,
        name: str,
        provider: BaseProvider,
        cost_per_1k_tokens: float,
        complexity_levels: List[TaskComplexity],
        priority: int = 1,
        max_tokens: int = 4096
    ) -> None:
        """Register a provider for routing."""
        self.providers[name] = ProviderConfig(
            provider=provider,
            name=name,
            cost_per_1k_tokens=cost_per_1k_tokens,
            max_tokens=max_tokens,
            complexity_levels=complexity_levels,
            priority=priority
        )
        self.stats['by_provider'][name] = 0

    def _default_complexity_estimator(self, prompt: str) -> TaskComplexity:
        """
        Simple heuristic to estimate task complexity.

        Args:
            prompt: User prompt

        Returns:
            Estimated complexity
        """
        # Simple heuristic based on length and keywords
        prompt_lower = prompt.lower()

        complex_keywords = [
            'analyze', 'design', 'architect', 'implement', 'complex',
            'detailed', 'comprehensive', 'multi-step', 'reasoning'
        ]

        simple_keywords = [
            'what is', 'define', 'explain briefly', 'summarize',
            'list', 'simple', 'quick', 'short'
        ]

        if any(kw in prompt_lower for kw in complex_keywords):
            return TaskComplexity.COMPLEX

        if any(kw in prompt_lower for kw in simple_keywords):
            return TaskComplexity.SIMPLE

        # Default to moderate
        return TaskComplexity.MODERATE

    def select_provider(
        self,
        prompt: str,
        complexity: Optional[TaskComplexity] = None,
        preferred_provider: Optional[str] = None
    ) -> ProviderConfig:
        """
        Select optimal provider for the task.

        Args:
            prompt: User prompt
            complexity: Optional explicit complexity
            preferred_provider: Optional preferred provider name

        Returns:
            Selected provider config

        Raises:
            ValueError: If no suitable provider found
        """
        # Use provided complexity or estimate it
        if complexity is None:
            complexity = self.complexity_estimator(prompt)

        # If preferred provider specified and available, use it
        if preferred_provider and preferred_provider in self.providers:
            config = self.providers[preferred_provider]
            if complexity in config.complexity_levels:
                return config

        # Find providers that handle this complexity
        candidates = [
            config for config in self.providers.values()
            if complexity in config.complexity_levels
        ]

        if not candidates:
            raise ValueError(f"No provider available for complexity: {complexity}")

        # Sort by priority (higher first), then by cost (lower first)
        candidates.sort(key=lambda c: (-c.priority, c.cost_per_1k_tokens))

        return candidates[0]

    def chat(
        self,
        system: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        complexity: Optional[TaskComplexity] = None,
        max_retries: int = 2
    ) -> str:
        """
        Route chat request to optimal provider with fallback.

        Args:
            system: System prompt
            messages: Conversation messages
            temperature: Sampling temperature
            complexity: Optional explicit complexity
            max_retries: Number of fallback attempts

        Returns:
            Model response

        Raises:
            RuntimeError: If all providers fail
        """
        # Estimate complexity from last user message
        last_message = messages[-1]['content'] if messages else ""
        selected_complexity = complexity or self.complexity_estimator(last_message)

        # Get fallback chain
        candidates = [
            config for config in self.providers.values()
            if selected_complexity in config.complexity_levels
        ]
        candidates.sort(key=lambda c: (-c.priority, c.cost_per_1k_tokens))

        errors = []
        for attempt, config in enumerate(candidates[:max_retries + 1]):
            try:
                start_time = time.time()

                response = config.provider.chat(system, messages, temperature)

                # Update stats
                elapsed = time.time() - start_time
                self.stats['total_requests'] += 1
                self.stats['by_provider'][config.name] += 1
                self.stats['by_complexity'][selected_complexity.value] = \
                    self.stats['by_complexity'].get(selected_complexity.value, 0) + 1

                # Estimate cost (rough approximation)
                total_tokens = len(system + str(messages) + response) // 4
                cost = (total_tokens / 1000) * config.cost_per_1k_tokens
                self.stats['total_cost'] += cost

                if attempt > 0:
                    self.stats['fallbacks'] += 1

                return response

            except Exception as e:
                errors.append(f"{config.name}: {str(e)}")
                continue

        # All providers failed
        raise RuntimeError(f"All providers failed. Errors: {'; '.join(errors)}")

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return dict(self.stats)

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            'total_requests': 0,
            'by_provider': {name: 0 for name in self.providers.keys()},
            'by_complexity': {},
            'total_cost': 0.0,
            'fallbacks': 0
        }


def create_default_router() -> ProviderRouter:
    """
    Create router with common provider configurations.

    Returns:
        Configured router
    """
    router = ProviderRouter()

    # Try to add providers if available
    try:
        from .openai_chat import OpenAIProvider

        # GPT-4 for complex tasks
        router.register_provider(
            name="gpt-4",
            provider=OpenAIProvider(model="gpt-4-turbo-preview"),
            cost_per_1k_tokens=0.03,  # Approximate
            complexity_levels=[TaskComplexity.COMPLEX, TaskComplexity.MODERATE],
            priority=2
        )

        # GPT-3.5 for simple/moderate tasks
        router.register_provider(
            name="gpt-3.5",
            provider=OpenAIProvider(model="gpt-3.5-turbo"),
            cost_per_1k_tokens=0.002,
            complexity_levels=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
            priority=1
        )
    except Exception:
        pass

    try:
        from .anthropic_claude import AnthropicProvider

        # Claude for complex tasks
        router.register_provider(
            name="claude",
            provider=AnthropicProvider(),
            cost_per_1k_tokens=0.024,
            complexity_levels=[TaskComplexity.COMPLEX, TaskComplexity.MODERATE],
            priority=2
        )
    except Exception:
        pass

    try:
        from .local_ollama import OllamaProvider

        # Local model for simple tasks (free!)
        router.register_provider(
            name="ollama",
            provider=OllamaProvider(),
            cost_per_1k_tokens=0.0,
            complexity_levels=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
            priority=0  # Lowest priority due to quality
        )
    except Exception:
        pass

    return router
