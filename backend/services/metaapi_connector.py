import logging
import httpx
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MetaApiConnector:
    def __init__(self):
        self.token = settings.metaapi_token
        self.account_id = settings.metaapi_account_id
        self.base_url = f"https://mt-client-api-v1.agiliumtrade.agiliumtrade.ai"
        self._client: httpx.AsyncClient | None = None
        self._connected = False

    async def connect(self):
        self._client = httpx.AsyncClient(
            headers={"auth-token": self.token},
            timeout=30.0,
        )
        self._connected = True
        logger.info("MetaApi connector initialized")

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
        self._connected = False

    def _url(self, path: str) -> str:
        return f"{self.base_url}/users/current/accounts/{self.account_id}{path}"

    async def get_account_info(self) -> dict | None:
        if not self._client:
            return None
        try:
            resp = await self._client.get(self._url("/account-information"))
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"get_account_info error: {e}")
            return None

    async def get_tick(self, symbol: str) -> dict | None:
        if not self._client:
            return None
        try:
            resp = await self._client.get(
                self._url(f"/symbols/{symbol}/current-tick")
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"get_tick error: {e}")
            return None

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[dict] | None:
        if not self._client:
            return None
        try:
            resp = await self._client.get(
                self._url(f"/symbols/{symbol}/current-candles/{timeframe}"),
                params={"limit": limit},
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"get_candles error: {e}")
            return None

    async def get_positions(self) -> list[dict] | None:
        if not self._client:
            return None
        try:
            resp = await self._client.get(self._url("/positions"))
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"get_positions error: {e}")
            return None

    async def create_market_buy_order(
        self, symbol: str, volume: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        return await self._trade({
            "actionType": "ORDER_TYPE_BUY",
            "symbol": symbol,
            "volume": volume,
            "stopLoss": stop_loss,
            "takeProfit": take_profit,
            "comment": comment,
        })

    async def create_market_sell_order(
        self, symbol: str, volume: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        return await self._trade({
            "actionType": "ORDER_TYPE_SELL",
            "symbol": symbol,
            "volume": volume,
            "stopLoss": stop_loss,
            "takeProfit": take_profit,
            "comment": comment,
        })

    async def create_stop_buy_order(
        self, symbol: str, volume: float, price: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        return await self._trade({
            "actionType": "ORDER_TYPE_BUY_STOP",
            "symbol": symbol,
            "volume": volume,
            "openPrice": price,
            "stopLoss": stop_loss,
            "takeProfit": take_profit,
            "comment": comment,
        })

    async def create_stop_sell_order(
        self, symbol: str, volume: float, price: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        return await self._trade({
            "actionType": "ORDER_TYPE_SELL_STOP",
            "symbol": symbol,
            "volume": volume,
            "openPrice": price,
            "stopLoss": stop_loss,
            "takeProfit": take_profit,
            "comment": comment,
        })

    async def modify_position(
        self, position_id: str,
        stop_loss: float | None = None, take_profit: float | None = None
    ) -> dict | None:
        body = {"actionType": "POSITION_MODIFY", "positionId": position_id}
        if stop_loss is not None:
            body["stopLoss"] = stop_loss
        if take_profit is not None:
            body["takeProfit"] = take_profit
        return await self._trade(body)

    async def close_position(self, position_id: str) -> dict | None:
        return await self._trade({
            "actionType": "POSITION_CLOSE_ID",
            "positionId": position_id,
        })

    async def _trade(self, body: dict) -> dict | None:
        if not self._client:
            return None
        try:
            resp = await self._client.post(self._url("/trade"), json=body)
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"Trade executed: {body.get('actionType')} -> {result}")
            return result
        except Exception as e:
            logger.error(f"Trade error: {body.get('actionType')} -> {e}")
            return None
