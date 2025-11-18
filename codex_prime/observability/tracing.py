"""Request tracing for distributed systems."""

import time
import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from contextvars import ContextVar

# Context variable for current trace
current_trace: ContextVar[Optional['Trace']] = ContextVar('current_trace', default=None)


@dataclass
class Span:
    """Represents a single operation in a trace."""
    span_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    parent_span_id: Optional[str] = None

    def finish(self):
        """Mark span as finished."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Trace:
    """Represents a complete request trace."""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'trace_id': self.trace_id,
            'spans': [s.to_dict() for s in self.spans],
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.end_time - self.start_time if self.end_time else None,
            'metadata': self.metadata
        }


class RequestTracer:
    """Trace requests through the system."""

    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.max_traces = 1000  # Keep last 1000 traces

    def start_trace(self, trace_id: Optional[str] = None, **metadata) -> Trace:
        """
        Start a new trace.

        Args:
            trace_id: Optional trace ID (generated if not provided)
            **metadata: Additional metadata

        Returns:
            Trace object
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        trace = Trace(trace_id=trace_id, metadata=metadata)
        self.traces[trace_id] = trace

        # Limit trace storage
        if len(self.traces) > self.max_traces:
            oldest = min(self.traces.items(), key=lambda x: x[1].start_time)
            del self.traces[oldest[0]]

        # Set as current trace
        current_trace.set(trace)

        return trace

    def start_span(
        self,
        name: str,
        parent_span_id: Optional[str] = None,
        **tags
    ) -> Span:
        """
        Start a new span in current trace.

        Args:
            name: Span name
            parent_span_id: Optional parent span ID
            **tags: Span tags

        Returns:
            Span object
        """
        trace = current_trace.get()
        if trace is None:
            raise RuntimeError("No active trace. Call start_trace() first.")

        span = Span(
            span_id=str(uuid.uuid4()),
            name=name,
            start_time=time.time(),
            tags=tags,
            parent_span_id=parent_span_id
        )

        trace.spans.append(span)
        return span

    def finish_trace(self, trace_id: str):
        """Mark trace as finished."""
        if trace_id in self.traces:
            self.traces[trace_id].end_time = time.time()
            current_trace.set(None)

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get trace by ID."""
        return self.traces.get(trace_id)

    def get_recent_traces(self, limit: int = 100) -> List[Trace]:
        """Get recent traces."""
        sorted_traces = sorted(
            self.traces.values(),
            key=lambda t: t.start_time,
            reverse=True
        )
        return sorted_traces[:limit]


# Global tracer instance
_default_tracer: Optional[RequestTracer] = None


def get_tracer() -> RequestTracer:
    """Get or create global tracer."""
    global _default_tracer

    if _default_tracer is None:
        _default_tracer = RequestTracer()

    return _default_tracer


def trace_request(name: str, **metadata):
    """
    Decorator to trace a function as a request.

    Args:
        name: Request name
        **metadata: Additional metadata
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            trace = tracer.start_trace(**metadata)

            try:
                span = tracer.start_span(name, operation=func.__name__)
                result = func(*args, **kwargs)
                span.finish()
                return result
            except Exception as e:
                if trace.spans:
                    trace.spans[-1].error = str(e)
                    trace.spans[-1].finish()
                raise
            finally:
                tracer.finish_trace(trace.trace_id)

        return wrapper
    return decorator


class SpanContext:
    """Context manager for spans."""

    def __init__(self, name: str, **tags):
        self.name = name
        self.tags = tags
        self.span = None
        self.tracer = get_tracer()

    def __enter__(self):
        self.span = self.tracer.start_span(self.name, **self.tags)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.span.error = str(exc_val)
        self.span.finish()
        return False
