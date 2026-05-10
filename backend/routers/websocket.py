import json
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
from config import get_settings
from services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(tags=["WebSocket"])


def _extract_user_id_from_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub") or payload.get("user_id")
        except Exception:
            return None


@router.websocket("/ws/trading")
async def trading_websocket(websocket: WebSocket, token: str | None = None):
    client_id = str(uuid.uuid4())

    user_id = None
    if token:
        user_id = _extract_user_id_from_token(token)

    await ws_manager.connect(client_id, websocket, user_id=user_id)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "auth" and msg.get("token"):
                    extracted = _extract_user_id_from_token(msg["token"])
                    if extracted:
                        user_id = extracted
                        async with ws_manager._lock:
                            if user_id not in ws_manager._user_map:
                                ws_manager._user_map[user_id] = set()
                            ws_manager._user_map[user_id].add(client_id)
                        await websocket.send_text(json.dumps({
                            "event": "auth.success",
                            "data": {"user_id": user_id}
                        }))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(client_id)
