import logging
import asyncio
from datetime import datetime, timezone

from services.metaapi_connector import MetaApiConnector
from services.websocket_manager import ws_manager
from services.redis_service import get_redis
from core.trading_engine import TradingEngine

logger = logging.getLogger(__name__)


class UserEngine:
    def __init__(self, user_id: str, connector: MetaApiConnector, engine: TradingEngine):
        self.user_id = user_id
        self.connector = connector
        self.engine = engine
        self.connection_status = "DISCONNECTED"
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5


class EngineManager:
    def __init__(self):
        self._engines: dict[str, UserEngine] = {}
        self._lock = asyncio.Lock()

    @property
    def engines(self) -> dict[str, UserEngine]:
        return self._engines

    def get_user_engine(self, user_id: str) -> UserEngine | None:
        return self._engines.get(user_id)

    def get_connection_status(self, user_id: str) -> str | None:
        ue = self._engines.get(user_id)
        return ue.connection_status if ue else None

    async def connect_mt5(
        self, user_id: str, account_number: str, password: str, server: str
    ) -> bool:
        async with self._lock:
            connector = MetaApiConnector(
                account_number=account_number,
                password=password,
                server=server,
            )

            try:
                connected = await connector.connect()
                if not connected:
                    return False
            except Exception as e:
                logger.error(f"MT5 connection failed for user {user_id}: {e}")
                return False

            engine = TradingEngine(connector=connector)

            async def event_handler(event: str, data: dict):
                await ws_manager.broadcast_to_user(user_id, event, data)

            engine.on_event(event_handler)

            user_engine = UserEngine(user_id=user_id, connector=connector, engine=engine)
            user_engine.connection_status = "CONNECTED"
            user_engine.reconnect_attempts = 0

            if user_id in self._engines:
                old = self._engines[user_id]
                if old.engine.status.value == "RUNNING":
                    await old.engine.stop()
                await old.connector.disconnect()

            self._engines[user_id] = user_engine

            r = await get_redis()
            await r.set(f"mt5:connection:{user_id}", "CONNECTED")

            logger.info(f"MT5 connected for user {user_id} (account: {account_number})")
            return True

    async def disconnect_mt5(self, user_id: str):
        async with self._lock:
            ue = self._engines.get(user_id)
            if not ue:
                return

            if ue.engine.status.value == "RUNNING":
                await ue.engine.stop()

            await ue.connector.disconnect()
            ue.connection_status = "DISCONNECTED"

            r = await get_redis()
            await r.set(f"mt5:connection:{user_id}", "DISCONNECTED")

            del self._engines[user_id]
            logger.info(f"MT5 disconnected for user {user_id}")

    async def start_trading(self, user_id: str) -> bool:
        ue = self._engines.get(user_id)
        if not ue:
            return False
        if ue.connection_status != "CONNECTED":
            return False
        if ue.engine.status.value == "RUNNING":
            return False

        await ue.engine.start()

        r = await get_redis()
        await r.set(f"robot:status:{user_id}", "RUNNING")

        await ws_manager.broadcast_to_user(user_id, "robot.status", {"status": "RUNNING"})
        return True

    async def stop_trading(self, user_id: str) -> bool:
        ue = self._engines.get(user_id)
        if not ue:
            return False
        if ue.engine.status.value != "RUNNING":
            return False

        await ue.engine.stop()

        r = await get_redis()
        await r.set(f"robot:status:{user_id}", "STOPPED")

        await ws_manager.broadcast_to_user(user_id, "robot.status", {"status": "STOPPED"})
        return True

    async def emergency_stop(self, user_id: str) -> dict:
        ue = self._engines.get(user_id)
        if not ue:
            return {"closed_positions": 0}

        result = await ue.engine.emergency_stop()

        r = await get_redis()
        await r.set(f"robot:status:{user_id}", "EMERGENCY")

        await ws_manager.broadcast_to_user(user_id, "emergency.triggered", {
            "status": "EMERGENCY",
            "closed_positions": result.get("closed_count", 0) if isinstance(result, dict) else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return result if isinstance(result, dict) else {"closed_positions": 0}

    def get_status(self, user_id: str) -> dict:
        ue = self._engines.get(user_id)
        if not ue:
            return {
                "robot_status": "STOPPED",
                "connection_status": "DISCONNECTED",
                "positions": [],
                "buy_count": 0,
                "sell_count": 0,
            }
        return ue.engine.get_status()

    async def reconnect(self, user_id: str, account_number: str, password: str, server: str):
        ue = self._engines.get(user_id)
        max_attempts = ue.max_reconnect_attempts if ue else 5

        for attempt in range(1, max_attempts + 1):
            delay = min(2 ** attempt, 30)
            logger.info(f"Reconnection attempt {attempt}/{max_attempts} for user {user_id} (delay: {delay}s)")

            await asyncio.sleep(delay)

            success = await self.connect_mt5(user_id, account_number, password, server)
            if success:
                logger.info(f"Reconnection successful for user {user_id} on attempt {attempt}")
                await ws_manager.broadcast_to_user(user_id, "mt5.reconnected", {
                    "attempt": attempt,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                return True

        logger.error(f"Reconnection failed for user {user_id} after {max_attempts} attempts")

        r = await get_redis()
        await r.set(f"mt5:connection:{user_id}", "ERROR")

        await ws_manager.broadcast_to_user(user_id, "mt5.connection_error", {
            "message": "Reconnection failed after maximum attempts",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return False

    async def shutdown(self):
        for user_id in list(self._engines.keys()):
            await self.disconnect_mt5(user_id)


engine_manager = EngineManager()
