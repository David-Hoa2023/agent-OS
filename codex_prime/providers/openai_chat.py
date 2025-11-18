"""OpenAI provider implementation."""

import os
from typing import Optional
from .base import BaseProvider

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseProvider):
    """OpenAI chat and embedding provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        embedding_model: str = "text-embedding-3-small"
    ):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.embedding_model = embedding_model

    def chat(
        self,
        system: str,
        messages: list[dict[str, str]],
        temperature: float = 0.4
    ) -> str:
        """Send chat completion request to OpenAI."""
        formatted_messages = [{"role": "system", "content": system}]
        formatted_messages.extend(messages)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=temperature
        )

        return response.choices[0].message.content or ""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI."""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )

        return [item.embedding for item in response.data]

    def stream_chat(
        self,
        system: str,
        messages: list[dict[str, str]],
        temperature: float = 0.4
    ):
        """
        Stream chat completion responses.

        Yields:
            Text chunks as they arrive
        """
        formatted_messages = [{"role": "system", "content": system}]
        formatted_messages.extend(messages)

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=temperature,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
