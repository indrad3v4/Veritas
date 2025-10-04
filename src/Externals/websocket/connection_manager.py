"""
WebSocket Connection Manager - Endpoint handler
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict
import logging

from src.Gateways.notifications import WebSocketGateway

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections at API layer
    Delegates to WebSocketGateway (Clean Architecture)
    """

    def __init__(self, gateway: WebSocketGateway):
        self.gateway = gateway

    async def handle_connection(self, websocket: WebSocket, user_id: str):
        """Handle WebSocket connection lifecycle"""
        await self.gateway.connect(websocket, user_id)

        try:
            # Send welcome message
            await websocket.send_json({
                "type": "connected",
                "message": "WebSocket connected successfully",
                "user_id": user_id
            })

            # Keep connection alive
            while True:
                # Wait for messages from client (heartbeat, etc.)
                data = await websocket.receive_text()

                # Echo back for heartbeat
                if data == "ping":
                    await websocket.send_text("pong")

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        finally:
            self.gateway.disconnect(websocket, user_id)
