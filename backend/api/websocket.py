"""WebSocket handler for live optimization progress."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections for optimization streams."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, optimization_id: str) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if optimization_id not in self._connections:
            self._connections[optimization_id] = []
        self._connections[optimization_id].append(websocket)

    def disconnect(self, websocket: WebSocket, optimization_id: str) -> None:
        """Remove a WebSocket connection."""
        if optimization_id in self._connections:
            self._connections[optimization_id] = [
                ws for ws in self._connections[optimization_id] if ws != websocket
            ]
            if not self._connections[optimization_id]:
                del self._connections[optimization_id]

    async def broadcast(self, optimization_id: str, message: dict[str, Any]) -> None:
        """Send a message to all connections for an optimization."""
        if optimization_id in self._connections:
            dead: list[WebSocket] = []
            for ws in self._connections[optimization_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws, optimization_id)

    @property
    def active_connections(self) -> int:
        """Return total number of active connections."""
        return sum(len(ws_list) for ws_list in self._connections.values())

    @property
    def tracked_optimizations(self) -> list[str]:
        """Return IDs of optimizations with active listeners."""
        return list(self._connections.keys())


manager = ConnectionManager()


@router.websocket("/optimizations/{optimization_id}/stream")
async def optimization_stream(
    websocket: WebSocket, optimization_id: str
) -> None:
    """Stream live optimization progress via WebSocket.

    Messages sent:
    - connected: Initial connection confirmation
    - progress: Phase/candidate progress updates
    - pong: Response to client ping
    - error: On any error
    """
    await manager.connect(websocket, optimization_id)
    try:
        await websocket.send_json({
            "type": "connected",
            "optimization_id": optimization_id,
        })
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, optimization_id)
    except Exception:
        logger.exception("WebSocket error for %s", optimization_id)
        manager.disconnect(websocket, optimization_id)


def create_progress_callback(optimization_id: str) -> Any:
    """Create a progress callback that broadcasts to WebSocket clients."""
    async def callback(phase: str, data: dict[str, Any]) -> None:
        await manager.broadcast(optimization_id, {
            "type": "progress",
            "phase": phase,
            "data": data,
        })
    return callback
