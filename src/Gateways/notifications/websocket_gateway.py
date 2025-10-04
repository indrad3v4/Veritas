"""
WebSocket Gateway - Real-time notifications
"""
from typing import Dict, Any, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketGateway:
    """
    WebSocket Gateway - Manages real-time connections
    """

    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Register new WebSocket connection for user"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections for specific user"""
        if user_id not in self.active_connections:
            logger.warning(f"No active connections for user {user_id}")
            return

        dead_connections = set()

        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {str(e)}")
                dead_connections.add(connection)

        # Clean up dead connections
        for connection in dead_connections:
            self.disconnect(connection, user_id)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)
