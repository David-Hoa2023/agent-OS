"""Collaborative sessions and room management."""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


class SessionStatus(Enum):
    """Session status."""

    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


@dataclass
class SessionParticipant:
    """Participant in a collaborative session."""

    user_id: str
    username: str
    role: str = "participant"  # owner, moderator, participant
    joined_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class SessionMessage:
    """Message in a collaborative session."""

    message_id: str
    user_id: str
    content: str
    message_type: str = "chat"  # chat, system, agent_response
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "message_id": self.message_id,
            "user_id": self.user_id,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class CollaborativeSession:
    """Collaborative session for multiple users."""

    def __init__(
        self,
        session_id: str,
        name: str,
        owner_id: str,
        max_participants: int = 10
    ):
        """
        Initialize collaborative session.

        Args:
            session_id: Unique session identifier
            name: Session name
            owner_id: User ID of session owner
            max_participants: Maximum number of participants
        """
        self.session_id = session_id
        self.name = name
        self.owner_id = owner_id
        self.max_participants = max_participants

        self.participants: Dict[str, SessionParticipant] = {}
        self.messages: List[SessionMessage] = []
        self.shared_context: Dict[str, Any] = {}

        self.status = SessionStatus.ACTIVE
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_participant(
        self,
        user_id: str,
        username: str,
        role: str = "participant"
    ) -> bool:
        """
        Add a participant to the session.

        Args:
            user_id: User ID
            username: Username
            role: Participant role

        Returns:
            True if added successfully
        """
        if len(self.participants) >= self.max_participants:
            return False

        if user_id in self.participants:
            return False

        participant = SessionParticipant(
            user_id=user_id,
            username=username,
            role=role
        )

        self.participants[user_id] = participant
        self.updated_at = datetime.now()

        # Add system message
        self._add_system_message(f"{username} joined the session")

        return True

    def remove_participant(self, user_id: str) -> bool:
        """
        Remove a participant from the session.

        Args:
            user_id: User ID

        Returns:
            True if removed successfully
        """
        if user_id not in self.participants:
            return False

        participant = self.participants[user_id]
        username = participant.username

        del self.participants[user_id]
        self.updated_at = datetime.now()

        # Add system message
        self._add_system_message(f"{username} left the session")

        return True

    def add_message(
        self,
        user_id: str,
        content: str,
        message_type: str = "chat",
        metadata: Optional[Dict] = None
    ) -> SessionMessage:
        """
        Add a message to the session.

        Args:
            user_id: User ID sending the message
            content: Message content
            message_type: Type of message
            metadata: Optional metadata

        Returns:
            Created message
        """
        import uuid

        message = SessionMessage(
            message_id=str(uuid.uuid4()),
            user_id=user_id,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )

        self.messages.append(message)
        self.updated_at = datetime.now()

        return message

    def _add_system_message(self, content: str):
        """Add a system message."""
        self.add_message(
            user_id="system",
            content=content,
            message_type="system"
        )

    def get_messages(
        self,
        limit: int = 50,
        since: Optional[datetime] = None
    ) -> List[SessionMessage]:
        """
        Get session messages.

        Args:
            limit: Maximum number of messages
            since: Only messages after this time

        Returns:
            List of messages
        """
        messages = self.messages

        if since:
            messages = [m for m in messages if m.timestamp > since]

        return messages[-limit:]

    def update_shared_context(self, key: str, value: Any):
        """Update shared context."""
        self.shared_context[key] = value
        self.updated_at = datetime.now()

    def get_shared_context(self, key: str) -> Optional[Any]:
        """Get shared context value."""
        return self.shared_context.get(key)

    def get_participant_count(self) -> int:
        """Get number of participants."""
        return len(self.participants)

    def is_participant(self, user_id: str) -> bool:
        """Check if user is a participant."""
        return user_id in self.participants

    def get_participant(self, user_id: str) -> Optional[SessionParticipant]:
        """Get participant by user ID."""
        return self.participants.get(user_id)

    def to_dict(self) -> Dict:
        """Serialize session to dictionary."""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "owner_id": self.owner_id,
            "status": self.status.value,
            "participants": {
                user_id: {
                    "username": p.username,
                    "role": p.role,
                    "joined_at": p.joined_at.isoformat(),
                    "is_active": p.is_active
                }
                for user_id, p in self.participants.items()
            },
            "message_count": len(self.messages),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class SessionManager:
    """Manage multiple collaborative sessions."""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize session manager.

        Args:
            storage_path: Path to store session data
        """
        self.storage_path = storage_path
        self.sessions: Dict[str, CollaborativeSession] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids

    def create_session(
        self,
        session_id: str,
        name: str,
        owner_id: str,
        max_participants: int = 10
    ) -> CollaborativeSession:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            name: Session name
            owner_id: User ID of owner
            max_participants: Maximum participants

        Returns:
            Created session
        """
        if session_id in self.sessions:
            raise ValueError(f"Session '{session_id}' already exists")

        session = CollaborativeSession(
            session_id=session_id,
            name=name,
            owner_id=owner_id,
            max_participants=max_participants
        )

        self.sessions[session_id] = session

        # Add owner as participant
        session.add_participant(owner_id, "Owner", role="owner")

        # Index by user
        if owner_id not in self.user_sessions:
            self.user_sessions[owner_id] = set()
        self.user_sessions[owner_id].add(session_id)

        return session

    def get_session(self, session_id: str) -> Optional[CollaborativeSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted
        """
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]

        # Remove from user indices
        for user_id in session.participants.keys():
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(session_id)

        del self.sessions[session_id]
        return True

    def join_session(
        self,
        session_id: str,
        user_id: str,
        username: str,
        role: str = "participant"
    ) -> bool:
        """
        Join a user to a session.

        Args:
            session_id: Session ID
            user_id: User ID
            username: Username
            role: Participant role

        Returns:
            True if joined successfully
        """
        session = self.get_session(session_id)
        if not session:
            return False

        if session.add_participant(user_id, username, role):
            # Index by user
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)
            return True

        return False

    def leave_session(self, session_id: str, user_id: str) -> bool:
        """
        Remove a user from a session.

        Args:
            session_id: Session ID
            user_id: User ID

        Returns:
            True if left successfully
        """
        session = self.get_session(session_id)
        if not session:
            return False

        if session.remove_participant(user_id):
            # Remove from user index
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(session_id)
            return True

        return False

    def get_user_sessions(self, user_id: str) -> List[CollaborativeSession]:
        """Get all sessions for a user."""
        session_ids = self.user_sessions.get(user_id, set())
        return [
            self.sessions[sid]
            for sid in session_ids
            if sid in self.sessions
        ]

    def list_sessions(self, status: Optional[SessionStatus] = None) -> List[CollaborativeSession]:
        """
        List all sessions.

        Args:
            status: Filter by status

        Returns:
            List of sessions
        """
        sessions = list(self.sessions.values())

        if status:
            sessions = [s for s in sessions if s.status == status]

        return sessions

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        active_sessions = [s for s in self.sessions.values() if s.status == SessionStatus.ACTIVE]

        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(active_sessions),
            "total_participants": sum(s.get_participant_count() for s in active_sessions),
            "total_messages": sum(len(s.messages) for s in self.sessions.values())
        }
