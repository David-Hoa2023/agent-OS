"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat(
        self,
        system: str,
        messages: list[dict[str, str]],
        temperature: float = 0.4
    ) -> str:
        """
        Send chat completion request.

        Args:
            system: System prompt
            messages: Conversation history
            temperature: Sampling temperature

        Returns:
            Model response text
        """
        pass

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        pass


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        pass
