import asyncio
import json
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")

    async def disconnect(self, client_id: str):
        async with self._lock:
            self._connections.pop(client_id, None)
        logger.info(f"WebSocket disconnected: {client_id}")

    async def broadcast(self, event: str, data: dict):
        message = json.dumps({"event": event, "data": data})
        async with self._lock:
            dead = []
            for client_id, ws in self._connections.items():
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append(client_id)
            for cid in dead:
                self._connections.pop(cid, None)

    async def send_to(self, client_id: str, event: str, data: dict):
        message = json.dumps({"event": event, "data": data})
        async with self._lock:
            ws = self._connections.get(client_id)
            if ws:
                try:
                    await ws.send_text(message)
                except Exception:
                    self._connections.pop(client_id, None)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


ws_manager = WebSocketManager()
