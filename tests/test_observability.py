"""Tests for observability system."""

import pytest
import time
import tempfile
from pathlib import Path

from codex_prime.observability.logging import StructuredLogger, get_logger, LogContext
from codex_prime.observability.metrics import MetricsCollector, get_metrics, Timer
from codex_prime.observability.tracing import RequestTracer, get_tracer, SpanContext, trace_request
from codex_prime.observability.analytics import AnalyticsEngine, get_analytics


def test_structured_logger_creation():
    """Test creating structured logger."""
    logger = StructuredLogger("test")
    assert logger.logger.name == "test"


def test_structured_logger_logging():
    """Test logging with structured logger."""
    logger = StructuredLogger("test")

    # Should not raise
    logger.info("Test message", user_id="123", action="test")
    logger.error("Error message", error_code=500)
    logger.debug("Debug message")


def test_request_id_context():
    """Test request ID context management."""
    logger = StructuredLogger("test")

    request_id = logger.set_request_id("test-123")
    assert request_id == "test-123"

    logger.clear_request_id()


def test_log_context_manager():
    """Test log context manager."""
    logger = StructuredLogger("test")

    with LogContext(logger, "request-456") as log:
        log.info("Inside context")


def test_metrics_counter():
    """Test counter metrics."""
    metrics = MetricsCollector()

    metrics.increment_counter("requests")
    metrics.increment_counter("requests")
    metrics.increment_counter("requests", value=3)

    assert metrics.get_counter("requests") == 5


def test_metrics_gauge():
    """Test gauge metrics."""
    metrics = MetricsCollector()

    metrics.set_gauge("memory_usage", 1024.5)
    assert metrics.get_gauge("memory_usage") == 1024.5

    metrics.set_gauge("memory_usage", 2048.0)
    assert metrics.get_gauge("memory_usage") == 2048.0


def test_metrics_histogram():
    """Test histogram metrics."""
    metrics = MetricsCollector()

    # Record some observations
    for value in [1, 2, 3, 4, 5, 10, 20]:
        metrics.observe_histogram("response_time", value)

    stats = metrics.get_histogram_stats("response_time")

    assert stats['count'] == 7
    assert stats['min'] == 1
    assert stats['max'] == 20
    assert stats['mean'] == pytest.approx(6.43, rel=0.1)


def test_metrics_with_labels():
    """Test metrics with labels."""
    metrics = MetricsCollector()

    metrics.increment_counter("requests", labels={"method": "GET", "status": "200"})
    metrics.increment_counter("requests", labels={"method": "POST", "status": "201"})

    get_count = metrics.get_counter("requests", labels={"method": "GET", "status": "200"})
    post_count = metrics.get_counter("requests", labels={"method": "POST", "status": "201"})

    assert get_count == 1
    assert post_count == 1


def test_timer_context():
    """Test timer context manager."""
    metrics = MetricsCollector()

    with Timer(metrics, "operation_time"):
        time.sleep(0.01)  # Simulate work

    stats = metrics.get_histogram_stats("operation_time")
    assert stats['count'] == 1
    assert stats['mean'] > 0.01


def test_request_tracer():
    """Test request tracing."""
    tracer = RequestTracer()

    trace = tracer.start_trace(metadata={"user_id": "123"})
    assert trace.trace_id is not None

    span = tracer.start_span("operation1", operation_type="query")
    time.sleep(0.01)
    span.finish()

    assert span.duration > 0
    tracer.finish_trace(trace.trace_id)

    retrieved = tracer.get_trace(trace.trace_id)
    assert retrieved is not None
    assert len(retrieved.spans) == 1


def test_span_context():
    """Test span context manager."""
    tracer = RequestTracer()
    trace = tracer.start_trace()

    with SpanContext("database_query", table="users") as span:
        time.sleep(0.01)

    assert span.duration > 0
    assert span.tags["table"] == "users"


def test_trace_decorator():
    """Test trace decorator."""
    tracer = get_tracer()

    @trace_request("test_function", component="test")
    def my_function(x, y):
        return x + y

    result = my_function(2, 3)
    assert result == 5

    traces = tracer.get_recent_traces(limit=1)
    assert len(traces) > 0


def test_analytics_track_event():
    """Test tracking analytics events."""
    analytics = AnalyticsEngine()

    analytics.track_event("user_login", user_id="user1", project_id="proj1")
    analytics.track_event("api_call", user_id="user1", project_id="proj1")
    analytics.track_event("user_login", user_id="user2", project_id="proj1")

    counts = analytics.get_event_counts()
    assert counts["user_login"] == 2
    assert counts["api_call"] == 1


def test_analytics_user_activity():
    """Test user activity analytics."""
    analytics = AnalyticsEngine()

    # Add some events
    for i in range(5):
        analytics.track_event("action", user_id=f"user{i % 2}", project_id="proj1")

    activity = analytics.get_user_activity(days=7)

    assert activity['total_events'] == 5
    assert activity['unique_users'] == 2


def test_analytics_project_stats():
    """Test project statistics."""
    analytics = AnalyticsEngine()

    analytics.track_event("create", project_id="proj1", user_id="user1")
    analytics.track_event("update", project_id="proj1", user_id="user1")
    analytics.track_event("update", project_id="proj1", user_id="user2")

    stats = analytics.get_project_stats("proj1")

    assert stats['total_events'] == 3
    assert stats['unique_users'] == 2
    assert stats['events_by_type']['update'] == 2


def test_analytics_insights():
    """Test analytics insights generation."""
    analytics = AnalyticsEngine()

    # Add some events
    for i in range(10):
        analytics.track_event("test_event", user_id=f"user{i}", project_id=f"proj{i % 3}")

    insights = analytics.get_insights()

    assert insights['total_events'] == 10
    assert insights['active_projects'] == 3
    assert insights['active_users'] == 10


def test_get_all_metrics():
    """Test getting all metrics."""
    metrics = MetricsCollector()

    metrics.increment_counter("total_requests")
    metrics.set_gauge("active_connections", 42)
    metrics.observe_histogram("latency", 0.1)

    all_metrics = metrics.get_all_metrics()

    assert 'counters' in all_metrics
    assert 'gauges' in all_metrics
    assert 'histograms' in all_metrics
    assert all_metrics['gauges']['active_connections'] == 42


def test_metrics_reset():
    """Test resetting metrics."""
    metrics = MetricsCollector()

    metrics.increment_counter("requests")
    metrics.set_gauge("memory", 1024)

    metrics.reset()

    assert metrics.get_counter("requests") == 0
    assert metrics.get_gauge("memory") == 0
