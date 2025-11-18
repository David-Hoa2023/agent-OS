"""Analytics engine for usage patterns and insights."""

import time
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class UsageEvent:
    """Single usage event."""
    event_type: str
    timestamp: float
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnalyticsEngine:
    """Analyze usage patterns and generate insights."""

    def __init__(self, retention_days: int = 30):
        """
        Initialize analytics engine.

        Args:
            retention_days: Number of days to retain events
        """
        self.retention_days = retention_days
        self.events: List[UsageEvent] = []
        self.event_counts: Counter = Counter()

    def track_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        **metadata
    ):
        """
        Track a usage event.

        Args:
            event_type: Type of event
            user_id: Optional user ID
            project_id: Optional project ID
            **metadata: Additional event data
        """
        event = UsageEvent(
            event_type=event_type,
            timestamp=time.time(),
            user_id=user_id,
            project_id=project_id,
            metadata=metadata
        )

        self.events.append(event)
        self.event_counts[event_type] += 1

        # Cleanup old events
        self._cleanup_old_events()

    def get_event_counts(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> Dict[str, int]:
        """
        Get event counts.

        Args:
            event_type: Optional filter by event type
            start_time: Optional start timestamp
            end_time: Optional end timestamp

        Returns:
            Dictionary of event counts
        """
        filtered = self._filter_events(event_type, start_time, end_time)
        return Counter(e.event_type for e in filtered)

    def get_user_activity(
        self,
        user_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get user activity statistics.

        Args:
            user_id: Optional user ID filter
            days: Number of days to analyze

        Returns:
            Activity statistics
        """
        start_time = time.time() - (days * 86400)
        events = [e for e in self.events if e.timestamp >= start_time]

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if not events:
            return {
                'total_events': 0,
                'unique_users': 0,
                'events_by_type': {},
                'events_by_day': {}
            }

        # Calculate statistics
        unique_users = len(set(e.user_id for e in events if e.user_id))
        events_by_type = Counter(e.event_type for e in events)

        # Group by day
        events_by_day = defaultdict(int)
        for event in events:
            day = datetime.fromtimestamp(event.timestamp).strftime('%Y-%m-%d')
            events_by_day[day] += 1

        return {
            'total_events': len(events),
            'unique_users': unique_users,
            'events_by_type': dict(events_by_type),
            'events_by_day': dict(events_by_day)
        }

    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """
        Get project statistics.

        Args:
            project_id: Project ID

        Returns:
            Project statistics
        """
        project_events = [e for e in self.events if e.project_id == project_id]

        if not project_events:
            return {
                'total_events': 0,
                'first_activity': None,
                'last_activity': None,
                'unique_users': 0
            }

        return {
            'total_events': len(project_events),
            'first_activity': min(e.timestamp for e in project_events),
            'last_activity': max(e.timestamp for e in project_events),
            'unique_users': len(set(e.user_id for e in project_events if e.user_id)),
            'events_by_type': dict(Counter(e.event_type for e in project_events))
        }

    def get_insights(self) -> Dict[str, Any]:
        """
        Generate insights from usage data.

        Returns:
            Dictionary of insights
        """
        if not self.events:
            return {'message': 'No data available'}

        now = time.time()
        last_24h = [e for e in self.events if now - e.timestamp < 86400]
        last_7d = [e for e in self.events if now - e.timestamp < 604800]

        return {
            'total_events': len(self.events),
            'events_last_24h': len(last_24h),
            'events_last_7d': len(last_7d),
            'top_events': dict(self.event_counts.most_common(10)),
            'active_projects': len(set(e.project_id for e in self.events if e.project_id)),
            'active_users': len(set(e.user_id for e in self.events if e.user_id))
        }

    def _filter_events(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[UsageEvent]:
        """Filter events by criteria."""
        filtered = self.events

        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]

        if start_time:
            filtered = [e for e in filtered if e.timestamp >= start_time]

        if end_time:
            filtered = [e for e in filtered if e.timestamp <= end_time]

        return filtered

    def _cleanup_old_events(self):
        """Remove events older than retention period."""
        cutoff = time.time() - (self.retention_days * 86400)
        self.events = [e for e in self.events if e.timestamp >= cutoff]


# Global analytics instance
_default_analytics: Optional[AnalyticsEngine] = None


def get_analytics() -> AnalyticsEngine:
    """Get or create global analytics engine."""
    global _default_analytics

    if _default_analytics is None:
        _default_analytics = AnalyticsEngine()

    return _default_analytics
