"""Base class for domain-specific agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class AgentCapability(Enum):
    """Agent capabilities."""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    RESEARCH = "research"
    WRITING = "writing"
    REVIEW = "review"


@dataclass
class AgentResponse:
    """Response from an agent."""
    content: str
    confidence: float  # 0-1
    suggestions: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """Base class for all domain-specific agents."""

    def __init__(
        self,
        name: str,
        capabilities: List[AgentCapability],
        provider=None,
        tools_registry=None
    ):
        """
        Initialize agent.

        Args:
            name: Agent name
            capabilities: List of agent capabilities
            provider: LLM provider for generation
            tools_registry: Optional tools registry
        """
        self.name = name
        self.capabilities = capabilities
        self.provider = provider
        self.tools_registry = tools_registry

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Get system prompt for this agent."""
        pass

    @abstractmethod
    def process(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Process a task.

        Args:
            task: Task description
            context: Optional context information

        Returns:
            AgentResponse
        """
        pass

    def can_handle(self, capability: AgentCapability) -> bool:
        """Check if agent has capability."""
        return capability in self.capabilities

    def _build_messages(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Build message list for LLM."""
        messages = []

        if context:
            context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
            messages.append({
                "role": "user",
                "content": f"Context:\n{context_str}\n\nTask: {task}"
            })
        else:
            messages.append({"role": "user", "content": task})

        return messages

    def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3
    ) -> str:
        """Call LLM provider."""
        if not self.provider:
            raise RuntimeError("No LLM provider configured")

        return self.provider.chat(
            system=self.system_prompt,
            messages=messages,
            temperature=temperature
        )
