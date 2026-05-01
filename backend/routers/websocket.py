import asyncio
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/trading")
async def trading_websocket(websocket: WebSocket):
    client_id = str(uuid.uuid4())
    await ws_manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WS message from {client_id}: {data}")
    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(client_id)
