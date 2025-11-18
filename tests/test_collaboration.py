"""Tests for real-time collaboration features."""

import pytest
import asyncio
from datetime import datetime, timedelta
from codex_prime.collaboration import (
    # Sessions
    CollaborativeSession, SessionManager, SessionStatus,
    # Presence
    PresenceManager, UserPresence, PresenceStatus, ActivityTracker,
    # Streaming
    StreamingManager, StreamChunk, StreamStatus, StreamBuffer, simple_stream
)


# Session Tests

def test_create_session():
    """Test creating a collaborative session."""
    session = CollaborativeSession(
        session_id="session1",
        name="Test Session",
        owner_id="user1"
    )

    assert session.session_id == "session1"
    assert session.name == "Test Session"
    assert session.owner_id == "user1"
    assert session.status == SessionStatus.ACTIVE


def test_add_participant():
    """Test adding participants."""
    session = CollaborativeSession("session1", "Test", "user1")

    # Add participant
    success = session.add_participant("user2", "Alice")
    assert success
    assert session.get_participant_count() == 2  # Owner + Alice
    assert session.is_participant("user2")


def test_max_participants():
    """Test maximum participants limit."""
    session = CollaborativeSession("session1", "Test", "user1", max_participants=3)

    session.add_participant("user2", "Alice")
    session.add_participant("user3", "Bob")

    # Should fail - at max capacity
    success = session.add_participant("user4", "Charlie")
    assert not success


def test_remove_participant():
    """Test removing participants."""
    session = CollaborativeSession("session1", "Test", "user1")
    session.add_participant("user2", "Alice")

    success = session.remove_participant("user2")
    assert success
    assert not session.is_participant("user2")


def test_add_message():
    """Test adding messages."""
    session = CollaborativeSession("session1", "Test", "user1")

    message = session.add_message("user1", "Hello world!")
    assert message.content == "Hello world!"
    assert message.user_id == "user1"
    assert message.message_type == "chat"


def test_get_messages():
    """Test getting messages with limits."""
    session = CollaborativeSession("session1", "Test", "user1")

    for i in range(10):
        session.add_message("user1", f"Message {i}")

    messages = session.get_messages(limit=5)
    assert len(messages) <= 10  # Includes system messages
    assert messages[-1].content == "Message 9"


def test_shared_context():
    """Test shared context."""
    session = CollaborativeSession("session1", "Test", "user1")

    session.update_shared_context("key1", "value1")
    assert session.get_shared_context("key1") == "value1"

    session.update_shared_context("counter", 42)
    assert session.get_shared_context("counter") == 42


def test_session_serialization():
    """Test serializing session."""
    session = CollaborativeSession("session1", "Test", "user1")
    session.add_participant("user2", "Alice")

    data = session.to_dict()
    assert data["session_id"] == "session1"
    assert data["name"] == "Test"
    assert len(data["participants"]) == 2


# Session Manager Tests

def test_session_manager_create():
    """Test creating session with manager."""
    manager = SessionManager()

    session = manager.create_session("session1", "Test", "user1")
    assert session.session_id == "session1"
    assert manager.get_session("session1") == session


def test_session_manager_join():
    """Test joining session."""
    manager = SessionManager()
    manager.create_session("session1", "Test", "user1")

    success = manager.join_session("session1", "user2", "Alice")
    assert success

    session = manager.get_session("session1")
    assert session.is_participant("user2")


def test_session_manager_leave():
    """Test leaving session."""
    manager = SessionManager()
    manager.create_session("session1", "Test", "user1")
    manager.join_session("session1", "user2", "Alice")

    success = manager.leave_session("session1", "user2")
    assert success

    session = manager.get_session("session1")
    assert not session.is_participant("user2")


def test_session_manager_get_user_sessions():
    """Test getting user sessions."""
    manager = SessionManager()
    manager.create_session("session1", "Test 1", "user1")
    manager.create_session("session2", "Test 2", "user1")

    sessions = manager.get_user_sessions("user1")
    assert len(sessions) == 2


def test_session_manager_delete():
    """Test deleting session."""
    manager = SessionManager()
    manager.create_session("session1", "Test", "user1")

    success = manager.delete_session("session1")
    assert success
    assert manager.get_session("session1") is None


def test_session_manager_stats():
    """Test session statistics."""
    manager = SessionManager()
    manager.create_session("session1", "Test 1", "user1")
    manager.create_session("session2", "Test 2", "user2")

    stats = manager.get_stats()
    assert stats["total_sessions"] == 2
    assert stats["active_sessions"] == 2


# Presence Tests

def test_set_user_online():
    """Test setting user online."""
    manager = PresenceManager()

    presence = manager.set_user_online("user1", "Alice")
    assert presence.user_id == "user1"
    assert presence.status == PresenceStatus.ONLINE
    assert manager.is_user_online("user1")


def test_set_user_offline():
    """Test setting user offline."""
    manager = PresenceManager()
    manager.set_user_online("user1", "Alice")

    manager.set_user_offline("user1")
    assert not manager.is_user_online("user1")


def test_update_activity():
    """Test updating user activity."""
    manager = PresenceManager()
    presence = manager.set_user_online("user1", "Alice")

    old_activity = presence.last_activity
    import time
    time.sleep(0.1)

    manager.update_activity("user1")
    assert presence.last_activity > old_activity


def test_get_online_users():
    """Test getting online users."""
    manager = PresenceManager()
    manager.set_user_online("user1", "Alice")
    manager.set_user_online("user2", "Bob")
    manager.set_user_offline("user2")

    online = manager.get_online_users()
    assert len(online) == 1
    assert online[0].user_id == "user1"


def test_session_users():
    """Test getting users in a session."""
    manager = PresenceManager()
    manager.set_user_online("user1", "Alice", session_id="session1")
    manager.set_user_online("user2", "Bob", session_id="session1")
    manager.set_user_online("user3", "Charlie", session_id="session2")

    users = manager.get_session_users("session1")
    assert len(users) == 2


def test_presence_stats():
    """Test presence statistics."""
    manager = PresenceManager()
    manager.set_user_online("user1", "Alice")
    manager.set_user_online("user2", "Bob")
    manager.set_user_offline("user2")

    stats = manager.get_stats()
    assert stats["total_users"] == 2
    assert stats["by_status"][PresenceStatus.ONLINE.value] == 1
    assert stats["by_status"][PresenceStatus.OFFLINE.value] == 1


@pytest.mark.asyncio
async def test_presence_monitoring():
    """Test automatic presence monitoring."""
    manager = PresenceManager(away_timeout=1, offline_timeout=2)

    presence = manager.set_user_online("user1", "Alice")
    assert presence.status == PresenceStatus.ONLINE

    # Start monitoring
    manager.start_monitoring()

    # Wait for away timeout
    await asyncio.sleep(1.5)
    await manager._update_statuses()
    assert presence.status == PresenceStatus.AWAY

    # Wait for offline timeout
    await asyncio.sleep(1)
    await manager._update_statuses()
    assert presence.status == PresenceStatus.OFFLINE

    await manager.stop_monitoring()


# Activity Tracker Tests

def test_log_activity():
    """Test logging activity."""
    tracker = ActivityTracker()

    tracker.log_activity("user1", "message", {"content": "Hello"})
    tracker.log_activity("user1", "command", {"cmd": "/help"})

    activities = tracker.get_user_activities("user1")
    assert len(activities) == 2


def test_activity_summary():
    """Test activity summary."""
    tracker = ActivityTracker()

    tracker.log_activity("user1", "message")
    tracker.log_activity("user1", "message")
    tracker.log_activity("user1", "command")

    summary = tracker.get_activity_summary("user1")
    assert summary["total"] == 3
    assert summary["by_type"]["message"] == 2
    assert summary["by_type"]["command"] == 1


# Streaming Tests

@pytest.mark.asyncio
async def test_stream_text():
    """Test streaming text."""
    manager = StreamingManager()
    chunks_received = []

    async def callback(chunk: StreamChunk):
        chunks_received.append(chunk)

    await manager.stream_text("Hello", "stream1", chunk_size=1, delay=0.01, chunk_callback=callback)

    # Should have start chunk + 5 char chunks + end chunk
    assert len(chunks_received) >= 5
    assert chunks_received[0].status == StreamStatus.STARTED
    assert chunks_received[-1].status == StreamStatus.COMPLETED


@pytest.mark.asyncio
async def test_stream_word_by_word():
    """Test word-by-word streaming."""
    manager = StreamingManager()
    chunks_received = []

    async def callback(chunk: StreamChunk):
        chunks_received.append(chunk)

    await manager.stream_text("Hello world test", "stream1", chunk_size=-1, delay=0.01, chunk_callback=callback)

    # Should have start + 3 words + end
    content_chunks = [c for c in chunks_received if c.status == StreamStatus.STREAMING]
    assert len(content_chunks) == 3


@pytest.mark.asyncio
async def test_stream_buffer():
    """Test stream buffer."""
    buffer = StreamBuffer(max_size=5)

    for i in range(10):
        chunk = StreamChunk(chunk_id=i, content=f"chunk{i}", stream_id="stream1")
        buffer.add_chunk(chunk)

    # Should only keep last 5 chunks
    recent = buffer.get_recent_chunks(10)
    assert len(recent) == 5

    # But full content should have all
    content = buffer.get_content()
    assert "chunk0" in content
    assert "chunk9" in content


@pytest.mark.asyncio
async def test_simple_stream():
    """Test simple streaming utility."""
    chunks = []

    async def callback(chunk: str):
        chunks.append(chunk)

    await simple_stream("Hello", callback, chunk_size=1, delay=0.01)

    assert len(chunks) == 5
    assert "".join(chunks) == "Hello"


def test_stream_status():
    """Test getting stream status."""
    manager = StreamingManager()

    # No status for non-existent stream
    status = manager.get_stream_status("nonexistent")
    assert status is None


@pytest.mark.asyncio
async def test_stream_cleanup():
    """Test cleaning up streams."""
    manager = StreamingManager()

    async def dummy_source():
        yield "test"

    await manager.create_stream("stream1", dummy_source())

    assert "stream1" in manager.active_streams

    manager.cleanup_stream("stream1")
    assert "stream1" not in manager.active_streams
