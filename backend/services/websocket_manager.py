import asyncio
import json
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._user_map: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, websocket: WebSocket, user_id: str | None = None):
        await websocket.accept()
        async with self._lock:
            self._connections[client_id] = websocket
            if user_id:
                if user_id not in self._user_map:
                    self._user_map[user_id] = set()
                self._user_map[user_id].add(client_id)
        logger.info(f"WebSocket connected: {client_id} (user: {user_id})")

    async def disconnect(self, client_id: str):
        async with self._lock:
            self._connections.pop(client_id, None)
            for user_id, clients in list(self._user_map.items()):
                clients.discard(client_id)
                if not clients:
                    del self._user_map[user_id]
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

    async def broadcast_to_user(self, user_id: str, event: str, data: dict):
        message = json.dumps({"event": event, "data": data})
        async with self._lock:
            client_ids = self._user_map.get(user_id, set())
            dead = []
            for client_id in client_ids:
                ws = self._connections.get(client_id)
                if ws:
                    try:
                        await ws.send_text(message)
                    except Exception:
                        dead.append(client_id)
            for cid in dead:
                self._connections.pop(cid, None)
                client_ids.discard(cid)

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

    def get_user_connections(self, user_id: str) -> int:
        return len(self._user_map.get(user_id, set()))


ws_manager = WebSocketManager()
