"""WebSocket server for real-time communication."""

import asyncio
import json
from typing import Dict, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Try to import websockets
try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = Any


logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """WebSocket connection information."""

    connection_id: str
    websocket: WebSocketServerProtocol
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.connections: Dict[str, Connection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.session_connections: Dict[str, Set[str]] = {}  # session_id -> connection_ids

    def add_connection(
        self,
        connection_id: str,
        websocket: WebSocketServerProtocol,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Connection:
        """Add a new connection."""
        connection = Connection(
            connection_id=connection_id,
            websocket=websocket,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {}
        )

        self.connections[connection_id] = connection

        # Index by user
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)

        # Index by session
        if session_id:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(connection_id)

        return connection

    def remove_connection(self, connection_id: str):
        """Remove a connection."""
        if connection_id not in self.connections:
            return

        connection = self.connections[connection_id]

        # Remove from user index
        if connection.user_id and connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]

        # Remove from session index
        if connection.session_id and connection.session_id in self.session_connections:
            self.session_connections[connection.session_id].discard(connection_id)
            if not self.session_connections[connection.session_id]:
                del self.session_connections[connection.session_id]

        # Remove connection
        del self.connections[connection_id]

    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Get a connection by ID."""
        return self.connections.get(connection_id)

    def get_user_connections(self, user_id: str) -> Set[Connection]:
        """Get all connections for a user."""
        connection_ids = self.user_connections.get(user_id, set())
        return {self.connections[cid] for cid in connection_ids if cid in self.connections}

    def get_session_connections(self, session_id: str) -> Set[Connection]:
        """Get all connections in a session."""
        connection_ids = self.session_connections.get(session_id, set())
        return {self.connections[cid] for cid in connection_ids if cid in self.connections}

    def get_all_connections(self) -> Set[Connection]:
        """Get all active connections."""
        return set(self.connections.values())


class WebSocketServer:
    """WebSocket server for real-time communication."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        message_handler: Optional[Callable] = None
    ):
        """
        Initialize WebSocket server.

        Args:
            host: Server host
            port: Server port
            message_handler: Callback for handling messages
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets package required. Install with: pip install websockets")

        self.host = host
        self.port = port
        self.message_handler = message_handler
        self.connection_manager = ConnectionManager()
        self.server = None
        self._running = False

    async def start(self):
        """Start the WebSocket server."""
        self.server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port
        )
        self._running = True
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop(self):
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self._running = False
            logger.info("WebSocket server stopped")

    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle a new WebSocket connection."""
        import uuid
        connection_id = str(uuid.uuid4())

        logger.info(f"New connection: {connection_id} from {websocket.remote_address}")

        # Add connection
        connection = self.connection_manager.add_connection(connection_id, websocket)

        try:
            # Send welcome message
            await self.send_to_connection(connection_id, {
                "type": "connected",
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat()
            })

            # Handle messages
            async for message in websocket:
                await self._process_message(connection_id, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {connection_id}")
        except Exception as e:
            logger.error(f"Error handling connection {connection_id}: {e}")
        finally:
            # Remove connection
            self.connection_manager.remove_connection(connection_id)
            logger.info(f"Connection removed: {connection_id}")

    async def _process_message(self, connection_id: str, message: str):
        """Process incoming message."""
        try:
            data = json.loads(message)

            # Handle authentication
            if data.get("type") == "auth":
                await self._handle_auth(connection_id, data)
                return

            # Handle join session
            if data.get("type") == "join_session":
                await self._handle_join_session(connection_id, data)
                return

            # Call custom message handler
            if self.message_handler:
                response = await self.message_handler(connection_id, data)
                if response:
                    await self.send_to_connection(connection_id, response)

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from {connection_id}: {message}")
            await self.send_to_connection(connection_id, {
                "type": "error",
                "message": "Invalid JSON"
            })
        except Exception as e:
            logger.error(f"Error processing message from {connection_id}: {e}")
            await self.send_to_connection(connection_id, {
                "type": "error",
                "message": str(e)
            })

    async def _handle_auth(self, connection_id: str, data: Dict):
        """Handle authentication."""
        user_id = data.get("user_id")
        if not user_id:
            await self.send_to_connection(connection_id, {
                "type": "auth_failed",
                "message": "user_id required"
            })
            return

        # Update connection with user_id
        connection = self.connection_manager.get_connection(connection_id)
        if connection:
            # Remove old indices
            if connection.user_id:
                old_user_id = connection.user_id
                if old_user_id in self.connection_manager.user_connections:
                    self.connection_manager.user_connections[old_user_id].discard(connection_id)

            # Update user_id
            connection.user_id = user_id

            # Add new index
            if user_id not in self.connection_manager.user_connections:
                self.connection_manager.user_connections[user_id] = set()
            self.connection_manager.user_connections[user_id].add(connection_id)

            await self.send_to_connection(connection_id, {
                "type": "auth_success",
                "user_id": user_id
            })

    async def _handle_join_session(self, connection_id: str, data: Dict):
        """Handle joining a session."""
        session_id = data.get("session_id")
        if not session_id:
            await self.send_to_connection(connection_id, {
                "type": "join_failed",
                "message": "session_id required"
            })
            return

        connection = self.connection_manager.get_connection(connection_id)
        if connection:
            # Remove from old session
            if connection.session_id:
                old_session_id = connection.session_id
                if old_session_id in self.connection_manager.session_connections:
                    self.connection_manager.session_connections[old_session_id].discard(connection_id)

            # Join new session
            connection.session_id = session_id

            if session_id not in self.connection_manager.session_connections:
                self.connection_manager.session_connections[session_id] = set()
            self.connection_manager.session_connections[session_id].add(connection_id)

            # Notify user
            await self.send_to_connection(connection_id, {
                "type": "joined_session",
                "session_id": session_id
            })

            # Notify others in session
            await self.broadcast_to_session(session_id, {
                "type": "user_joined",
                "user_id": connection.user_id,
                "connection_id": connection_id
            }, exclude=[connection_id])

    async def send_to_connection(self, connection_id: str, data: Dict):
        """Send message to a specific connection."""
        connection = self.connection_manager.get_connection(connection_id)
        if not connection:
            return

        try:
            message = json.dumps(data)
            await connection.websocket.send(message)
        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")

    async def send_to_user(self, user_id: str, data: Dict):
        """Send message to all connections of a user."""
        connections = self.connection_manager.get_user_connections(user_id)
        tasks = [
            self.send_to_connection(conn.connection_id, data)
            for conn in connections
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_to_session(
        self,
        session_id: str,
        data: Dict,
        exclude: Optional[list] = None
    ):
        """Broadcast message to all connections in a session."""
        exclude = exclude or []
        connections = self.connection_manager.get_session_connections(session_id)

        tasks = [
            self.send_to_connection(conn.connection_id, data)
            for conn in connections
            if conn.connection_id not in exclude
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_to_all(self, data: Dict, exclude: Optional[list] = None):
        """Broadcast message to all connections."""
        exclude = exclude or []
        connections = self.connection_manager.get_all_connections()

        tasks = [
            self.send_to_connection(conn.connection_id, data)
            for conn in connections
            if conn.connection_id not in exclude
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            "total_connections": len(self.connection_manager.connections),
            "active_users": len(self.connection_manager.user_connections),
            "active_sessions": len(self.connection_manager.session_connections),
            "host": self.host,
            "port": self.port,
            "running": self._running
        }
