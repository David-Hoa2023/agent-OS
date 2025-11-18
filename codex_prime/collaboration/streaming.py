"""Token-by-token streaming for real-time responses."""

import asyncio
from typing import Optional, AsyncIterator, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class StreamStatus(Enum):
    """Streaming status."""

    STARTED = "started"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class StreamChunk:
    """Single chunk in a stream."""

    chunk_id: int
    content: str
    stream_id: str
    status: StreamStatus = StreamStatus.STREAMING
    timestamp: datetime = None
    metadata: dict = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "stream_id": self.stream_id,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class StreamingManager:
    """Manage token-by-token streaming."""

    def __init__(self):
        """Initialize streaming manager."""
        self.active_streams: dict[str, dict] = {}

    async def create_stream(
        self,
        stream_id: str,
        source: AsyncIterator[str],
        chunk_callback: Optional[Callable[[StreamChunk], Any]] = None
    ):
        """
        Create a new stream.

        Args:
            stream_id: Unique stream identifier
            source: Async iterator yielding content chunks
            chunk_callback: Optional callback called for each chunk
        """
        self.active_streams[stream_id] = {
            "status": StreamStatus.STARTED,
            "chunks": [],
            "started_at": datetime.now()
        }

        chunk_id = 0

        try:
            # Send start event
            start_chunk = StreamChunk(
                chunk_id=chunk_id,
                content="",
                stream_id=stream_id,
                status=StreamStatus.STARTED
            )

            if chunk_callback:
                await chunk_callback(start_chunk)

            chunk_id += 1

            # Stream content
            async for content in source:
                if content:
                    chunk = StreamChunk(
                        chunk_id=chunk_id,
                        content=content,
                        stream_id=stream_id,
                        status=StreamStatus.STREAMING
                    )

                    self.active_streams[stream_id]["chunks"].append(chunk)

                    if chunk_callback:
                        await chunk_callback(chunk)

                    chunk_id += 1

            # Send completion event
            end_chunk = StreamChunk(
                chunk_id=chunk_id,
                content="",
                stream_id=stream_id,
                status=StreamStatus.COMPLETED
            )

            self.active_streams[stream_id]["status"] = StreamStatus.COMPLETED
            self.active_streams[stream_id]["completed_at"] = datetime.now()

            if chunk_callback:
                await chunk_callback(end_chunk)

        except Exception as e:
            # Send error event
            error_chunk = StreamChunk(
                chunk_id=chunk_id,
                content="",
                stream_id=stream_id,
                status=StreamStatus.ERROR,
                metadata={"error": str(e)}
            )

            self.active_streams[stream_id]["status"] = StreamStatus.ERROR
            self.active_streams[stream_id]["error"] = str(e)

            if chunk_callback:
                await chunk_callback(error_chunk)

    def get_stream_status(self, stream_id: str) -> Optional[dict]:
        """Get status of a stream."""
        return self.active_streams.get(stream_id)

    def get_stream_content(self, stream_id: str) -> str:
        """Get full content of a completed stream."""
        stream = self.active_streams.get(stream_id)
        if not stream:
            return ""

        return "".join(chunk.content for chunk in stream.get("chunks", []))

    def cleanup_stream(self, stream_id: str):
        """Remove a stream from active streams."""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]

    async def stream_text(
        self,
        text: str,
        stream_id: str,
        chunk_size: int = 1,
        delay: float = 0.01,
        chunk_callback: Optional[Callable[[StreamChunk], Any]] = None
    ):
        """
        Stream text character by character or word by word.

        Args:
            text: Text to stream
            stream_id: Unique stream identifier
            chunk_size: Characters per chunk (1 = char-by-char, -1 = word-by-word)
            delay: Delay between chunks in seconds
            chunk_callback: Optional callback for each chunk
        """
        async def text_generator():
            """Generate text chunks."""
            if chunk_size == -1:
                # Word-by-word
                words = text.split()
                for word in words:
                    yield word + " "
                    await asyncio.sleep(delay)
            else:
                # Character-by-character or multi-character
                for i in range(0, len(text), chunk_size):
                    yield text[i:i+chunk_size]
                    await asyncio.sleep(delay)

        await self.create_stream(stream_id, text_generator(), chunk_callback)

    async def stream_provider_response(
        self,
        provider,
        stream_id: str,
        system: str,
        messages: list,
        chunk_callback: Optional[Callable[[StreamChunk], Any]] = None,
        **kwargs
    ):
        """
        Stream response from an LLM provider.

        Args:
            provider: LLM provider with stream_chat support
            stream_id: Unique stream identifier
            system: System prompt
            messages: Conversation messages
            chunk_callback: Optional callback for each chunk
            **kwargs: Additional provider arguments
        """
        # Check if provider supports streaming
        if not hasattr(provider, 'stream_chat'):
            raise ValueError(f"Provider {provider.__class__.__name__} does not support streaming")

        async def provider_generator():
            """Generate chunks from provider."""
            async for chunk in provider.stream_chat(system, messages, **kwargs):
                yield chunk

        await self.create_stream(stream_id, provider_generator(), chunk_callback)


class StreamBuffer:
    """Buffer for accumulating stream chunks."""

    def __init__(self, max_size: int = 1000):
        """
        Initialize stream buffer.

        Args:
            max_size: Maximum number of chunks to buffer
        """
        self.max_size = max_size
        self.chunks: list[StreamChunk] = []
        self.full_content = ""

    def add_chunk(self, chunk: StreamChunk):
        """Add a chunk to the buffer."""
        self.chunks.append(chunk)
        self.full_content += chunk.content

        # Keep buffer size under limit
        if len(self.chunks) > self.max_size:
            removed = self.chunks.pop(0)
            # Don't remove content from full_content as it should be complete

    def get_content(self) -> str:
        """Get full accumulated content."""
        return self.full_content

    def get_recent_chunks(self, n: int = 10) -> list[StreamChunk]:
        """Get N most recent chunks."""
        return self.chunks[-n:]

    def clear(self):
        """Clear the buffer."""
        self.chunks.clear()
        self.full_content = ""


# Utility function for simple streaming
async def simple_stream(
    text: str,
    callback: Callable[[str], Any],
    chunk_size: int = 1,
    delay: float = 0.01
):
    """
    Simple streaming utility.

    Args:
        text: Text to stream
        callback: Function to call with each chunk
        chunk_size: Characters per chunk
        delay: Delay between chunks
    """
    if chunk_size == -1:
        # Word-by-word
        words = text.split()
        for word in words:
            await callback(word + " ")
            await asyncio.sleep(delay)
    else:
        # Character-by-character
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            await callback(chunk)
            await asyncio.sleep(delay)
