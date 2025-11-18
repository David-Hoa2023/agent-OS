"""Anthropic Claude provider implementation."""

import os
from typing import Optional, List, Dict, Any
from .base import BaseProvider

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicProvider(BaseProvider):
    """Anthropic Claude chat provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096
    ):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens

    def chat(
        self,
        system: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.4
    ) -> str:
        """Send chat completion request to Claude."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=temperature,
            system=system,
            messages=messages
        )

        return response.content[0].text

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings.

        Note: Anthropic doesn't provide embeddings API yet.
        This is a placeholder that raises NotImplementedError.
        """
        raise NotImplementedError(
            "Anthropic doesn't provide embeddings API. Use OpenAI or local embeddings."
        )

    def stream_chat(
        self,
        system: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.4
    ):
        """
        Stream chat completion responses.

        Yields:
            Text chunks as they arrive
        """
        with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=temperature,
            system=system,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                yield text
