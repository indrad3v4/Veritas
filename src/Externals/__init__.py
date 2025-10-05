"""
WebSocket External Layer
"""
from .websocket.handlers import router as websocket_router

__all__ = ["websocket_router"]
