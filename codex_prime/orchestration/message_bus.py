"""Message bus for inter-agent communication."""

import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from threading import Lock


@dataclass
class Message:
    """Message passed between agents."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str = ""
    to_agent: Optional[str] = None  # None for broadcast
    message_type: str = "task"  # task, response, status, error
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    correlation_id: Optional[str] = None  # For tracking related messages


class MessageBus:
    """Central message bus for agent communication."""

    def __init__(self, max_history: int = 1000):
        """
        Initialize message bus.

        Args:
            max_history: Maximum messages to keep in history
        """
        self.max_history = max_history
        self.messages: deque[Message] = deque(maxlen=max_history)
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = Lock()

    def publish(self, message: Message):
        """
        Publish a message to the bus.

        Args:
            message: Message to publish
        """
        with self.lock:
            self.messages.append(message)

            # Notify subscribers
            if message.to_agent:
                # Direct message
                for callback in self.subscribers.get(message.to_agent, []):
                    callback(message)
            else:
                # Broadcast
                for agent_callbacks in self.subscribers.values():
                    for callback in agent_callbacks:
                        callback(message)

    def subscribe(self, agent_id: str, callback: Callable[[Message], None]):
        """
        Subscribe an agent to receive messages.

        Args:
            agent_id: Agent identifier
            callback: Function to call when message received
        """
        with self.lock:
            self.subscribers[agent_id].append(callback)

    def unsubscribe(self, agent_id: str):
        """
        Unsubscribe an agent.

        Args:
            agent_id: Agent identifier
        """
        with self.lock:
            if agent_id in self.subscribers:
                del self.subscribers[agent_id]

    def get_messages(
        self,
        agent_id: Optional[str] = None,
        message_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Message]:
        """
        Get messages from history.

        Args:
            agent_id: Filter by recipient agent
            message_type: Filter by message type
            correlation_id: Filter by correlation ID
            limit: Maximum messages to return

        Returns:
            List of messages
        """
        with self.lock:
            filtered = list(self.messages)

            if agent_id:
                filtered = [m for m in filtered if m.to_agent == agent_id]

            if message_type:
                filtered = [m for m in filtered if m.message_type == message_type]

            if correlation_id:
                filtered = [m for m in filtered if m.correlation_id == correlation_id]

            return filtered[-limit:]

    def get_conversation(self, correlation_id: str) -> List[Message]:
        """
        Get all messages in a conversation.

        Args:
            correlation_id: Correlation ID

        Returns:
            List of messages in chronological order
        """
        messages = self.get_messages(correlation_id=correlation_id, limit=self.max_history)
        return sorted(messages, key=lambda m: m.timestamp)

    def clear(self):
        """Clear message history."""
        with self.lock:
            self.messages.clear()
