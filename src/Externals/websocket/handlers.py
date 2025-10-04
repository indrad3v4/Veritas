"""
WebSocket Handlers - FastAPI WebSocket routes
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from src.Externals.api.dependencies import get_websocket_gateway
from .connection_manager import ConnectionManager

router = APIRouter(tags=["websocket"])

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID from authentication"),
    gateway = Depends(get_websocket_gateway)
):
    """
    WebSocket endpoint for real-time notifications

    Usage from frontend:
    ```
    const ws = new WebSocket(`wss://veritas-api.repl.co/ws?user_id=${userId}`);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Notification:', data);
    };
    ```
    """

    manager = ConnectionManager(gateway)
    await manager.handle_connection(websocket, user_id)
