"""Embedding provider abstraction."""

from abc import ABC, abstractmethod
from typing import Optional
import os


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        pass


class OpenAIEmbeddings(EmbeddingProvider):
    """OpenAI embeddings provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small"
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI package required: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]


class DummyEmbeddings(EmbeddingProvider):
    """Dummy embeddings for testing (random vectors)."""

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate dummy embeddings."""
        import random
        return [[random.random() for _ in range(self.dimension)] for _ in texts]
