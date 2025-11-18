"""Domain-specific agents for specialized tasks."""

from .base_agent import BaseAgent, AgentCapability
from .software.code_reviewer import CodeReviewerAgent
from .software.bug_hunter import BugHunterAgent
from .business.data_analyst import DataAnalystAgent

__all__ = [
    "BaseAgent",
    "AgentCapability",
    "CodeReviewerAgent",
    "BugHunterAgent",
    "DataAnalystAgent"
]
