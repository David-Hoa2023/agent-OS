"""Presence detection and user activity tracking."""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio


class PresenceStatus(Enum):
    """User presence status."""

    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class UserPresence:
    """User presence information."""

    user_id: str
    username: str
    status: PresenceStatus = PresenceStatus.OFFLINE
    last_seen: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    current_session: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_online(self) -> bool:
        """Check if user is online."""
        return self.status == PresenceStatus.ONLINE

    def is_active(self, timeout_seconds: int = 300) -> bool:
        """
        Check if user is active.

        Args:
            timeout_seconds: Seconds of inactivity before considering inactive

        Returns:
            True if user has activity within timeout
        """
        return (datetime.now() - self.last_activity).total_seconds() < timeout_seconds

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "current_session": self.current_session,
            "metadata": self.metadata
        }


class PresenceManager:
    """Manage user presence and activity."""

    def __init__(
        self,
        away_timeout: int = 300,  # 5 minutes
        offline_timeout: int = 900  # 15 minutes
    ):
        """
        Initialize presence manager.

        Args:
            away_timeout: Seconds before marking user as away
            offline_timeout: Seconds before marking user as offline
        """
        self.away_timeout = away_timeout
        self.offline_timeout = offline_timeout

        self.users: Dict[str, UserPresence] = {}
        self.session_users: Dict[str, Set[str]] = {}  # session_id -> user_ids

        self._monitoring = False
        self._monitor_task = None

    def set_user_online(
        self,
        user_id: str,
        username: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> UserPresence:
        """
        Set user as online.

        Args:
            user_id: User ID
            username: Username
            session_id: Optional session ID
            metadata: Optional metadata

        Returns:
            User presence object
        """
        now = datetime.now()

        if user_id in self.users:
            presence = self.users[user_id]
            presence.status = PresenceStatus.ONLINE
            presence.last_seen = now
            presence.last_activity = now
            presence.current_session = session_id

            if metadata:
                presence.metadata.update(metadata)
        else:
            presence = UserPresence(
                user_id=user_id,
                username=username,
                status=PresenceStatus.ONLINE,
                last_seen=now,
                last_activity=now,
                current_session=session_id,
                metadata=metadata or {}
            )
            self.users[user_id] = presence

        # Index by session
        if session_id:
            if session_id not in self.session_users:
                self.session_users[session_id] = set()
            self.session_users[session_id].add(user_id)

        return presence

    def set_user_offline(self, user_id: str):
        """Set user as offline."""
        if user_id not in self.users:
            return

        presence = self.users[user_id]
        presence.status = PresenceStatus.OFFLINE
        presence.last_seen = datetime.now()

        # Remove from session index
        if presence.current_session:
            session_id = presence.current_session
            if session_id in self.session_users:
                self.session_users[session_id].discard(user_id)

            presence.current_session = None

    def update_activity(self, user_id: str):
        """Update user's last activity timestamp."""
        if user_id not in self.users:
            return

        presence = self.users[user_id]
        presence.last_activity = datetime.now()

        # If user was away, bring them back online
        if presence.status == PresenceStatus.AWAY:
            presence.status = PresenceStatus.ONLINE

    def set_user_status(self, user_id: str, status: PresenceStatus):
        """Manually set user status."""
        if user_id not in self.users:
            return

        self.users[user_id].status = status

    def get_user_presence(self, user_id: str) -> Optional[UserPresence]:
        """Get user presence."""
        return self.users.get(user_id)

    def get_online_users(self) -> List[UserPresence]:
        """Get all online users."""
        return [
            p for p in self.users.values()
            if p.status == PresenceStatus.ONLINE
        ]

    def get_session_users(self, session_id: str) -> List[UserPresence]:
        """Get all users in a session."""
        user_ids = self.session_users.get(session_id, set())
        return [
            self.users[uid]
            for uid in user_ids
            if uid in self.users
        ]

    def is_user_online(self, user_id: str) -> bool:
        """Check if user is online."""
        presence = self.get_user_presence(user_id)
        return presence is not None and presence.is_online()

    def start_monitoring(self):
        """Start background monitoring of user presence."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """Background loop to update user statuses."""
        while self._monitoring:
            try:
                await self._update_statuses()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue monitoring
                import logging
                logging.error(f"Error in presence monitoring: {e}")

    async def _update_statuses(self):
        """Update user statuses based on activity."""
        now = datetime.now()

        for user_id, presence in list(self.users.items()):
            if presence.status == PresenceStatus.OFFLINE:
                continue

            # Calculate inactivity duration
            inactive_seconds = (now - presence.last_activity).total_seconds()

            # Mark as offline if no activity for offline_timeout
            if inactive_seconds >= self.offline_timeout:
                self.set_user_offline(user_id)

            # Mark as away if no activity for away_timeout
            elif inactive_seconds >= self.away_timeout and presence.status == PresenceStatus.ONLINE:
                presence.status = PresenceStatus.AWAY

    def get_stats(self) -> Dict[str, Any]:
        """Get presence statistics."""
        statuses = {}
        for status in PresenceStatus:
            statuses[status.value] = len([
                p for p in self.users.values()
                if p.status == status
            ])

        return {
            "total_users": len(self.users),
            "by_status": statuses,
            "active_sessions": len(self.session_users)
        }

    def cleanup_inactive(self, days: int = 7):
        """
        Remove users inactive for specified days.

        Args:
            days: Days of inactivity before removal
        """
        cutoff = datetime.now() - timedelta(days=days)

        inactive_users = [
            user_id for user_id, presence in self.users.items()
            if presence.last_seen < cutoff
        ]

        for user_id in inactive_users:
            del self.users[user_id]


class ActivityTracker:
    """Track user activity patterns."""

    def __init__(self):
        """Initialize activity tracker."""
        self.activities: Dict[str, List[Dict]] = {}  # user_id -> activity log

    def log_activity(
        self,
        user_id: str,
        activity_type: str,
        details: Optional[Dict] = None
    ):
        """
        Log user activity.

        Args:
            user_id: User ID
            activity_type: Type of activity (message, command, etc.)
            details: Optional activity details
        """
        if user_id not in self.activities:
            self.activities[user_id] = []

        activity = {
            "type": activity_type,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }

        self.activities[user_id].append(activity)

        # Keep only recent activities (last 100 per user)
        if len(self.activities[user_id]) > 100:
            self.activities[user_id] = self.activities[user_id][-100:]

    def get_user_activities(
        self,
        user_id: str,
        limit: int = 50,
        since: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get user activities.

        Args:
            user_id: User ID
            limit: Maximum number of activities
            since: Only activities after this time

        Returns:
            List of activities
        """
        activities = self.activities.get(user_id, [])

        if since:
            activities = [
                a for a in activities
                if datetime.fromisoformat(a["timestamp"]) > since
            ]

        return activities[-limit:]

    def get_activity_summary(self, user_id: str) -> Dict[str, Any]:
        """Get activity summary for a user."""
        activities = self.activities.get(user_id, [])

        if not activities:
            return {"total": 0, "by_type": {}}

        # Count by type
        by_type = {}
        for activity in activities:
            activity_type = activity["type"]
            by_type[activity_type] = by_type.get(activity_type, 0) + 1

        return {
            "total": len(activities),
            "by_type": by_type,
            "latest": activities[-1] if activities else None
        }
