"""Local LLM provider using Ollama."""

import os
from typing import Optional, List, Dict, Any
import requests
from .base import BaseProvider


class OllamaProvider(BaseProvider):
    """Local LLM provider using Ollama."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: str = "llama2",
        timeout: int = 120
    ):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model
        self.timeout = timeout

    def chat(
        self,
        system: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.4
    ) -> str:
        """Send chat completion request to Ollama."""
        # Combine system message with messages
        full_messages = [{"role": "system", "content": system}]
        full_messages.extend(messages)

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": full_messages,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            },
            timeout=self.timeout
        )

        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama."""
        embeddings = []

        for text in texts:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                },
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()
            embeddings.append(data.get("embedding", []))

        return embeddings

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
        full_messages = [{"role": "system", "content": system}]
        full_messages.extend(messages)

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": full_messages,
                "stream": True,
                "options": {
                    "temperature": temperature
                }
            },
            stream=True,
            timeout=self.timeout
        )

        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                import json
                data = json.loads(line)
                if "message" in data and "content" in data["message"]:
                    yield data["message"]["content"]

    def list_models(self) -> List[str]:
        """List available models."""
        response = requests.get(f"{self.base_url}/api/tags", timeout=10)
        response.raise_for_status()
        data = response.json()
        return [model["name"] for model in data.get("models", [])]
