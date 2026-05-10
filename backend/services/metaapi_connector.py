import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import MetaTrader5 as mt5

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_mt5_executor = ThreadPoolExecutor(max_workers=1)


def _run_sync(func, *args):
    return func(*args)


class MetaApiConnector:
    """Direct MT5 connector using the MetaTrader5 Python package.
    Connects to a local MT5 terminal — no cloud service needed."""

    def __init__(
        self,
        account_number: str | None = None,
        password: str | None = None,
        server: str | None = None,
        token: str | None = None,
        account_id: str | None = None,
    ):
        self.account_number = account_number
        self.password = password
        self.server = server
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def _run(self, func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_mt5_executor, _run_sync, func, *args)

    async def connect(self) -> bool:
        try:
            initialized = await self._run(self._init_mt5)
            if not initialized:
                return False
            self._connected = True
            info = await self.get_account_info()
            if info:
                logger.info(
                    f"MT5 connected: login={info.get('login')}, "
                    f"balance={info.get('balance')}, server={info.get('server')}"
                )
            return True
        except Exception as e:
            logger.error(f"MT5 connection failed: {e}")
            self._connected = False
            return False

    def _init_mt5(self) -> bool:
        if not mt5.initialize():
            logger.error(f"MT5 initialize failed: {mt5.last_error()}")
            return False

        if self.account_number and self.password and self.server:
            login = int(self.account_number)
            authorized = mt5.login(login, password=self.password, server=self.server)
            if not authorized:
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return False

        return True

    async def disconnect(self):
        await self._run(mt5.shutdown)
        self._connected = False
        logger.info("MT5 disconnected")

    async def get_account_info(self) -> dict | None:
        if not self._connected:
            return None
        try:
            info = await self._run(mt5.account_info)
            if info is None:
                return None
            info_dict = info._asdict()
            return {
                "login": info_dict.get("login"),
                "balance": info_dict.get("balance", 0.0),
                "equity": info_dict.get("equity", 0.0),
                "margin": info_dict.get("margin", 0.0),
                "margin_free": info_dict.get("margin_free", 0.0),
                "profit": info_dict.get("profit", 0.0),
                "server": info_dict.get("server", ""),
                "currency": info_dict.get("currency", "USD"),
                "leverage": info_dict.get("leverage", 0),
            }
        except Exception as e:
            logger.error(f"get_account_info error: {e}")
            return None

    async def get_tick(self, symbol: str) -> dict | None:
        if not self._connected:
            return None
        try:
            tick = await self._run(mt5.symbol_info_tick, symbol)
            if tick is None:
                return None
            tick_dict = tick._asdict()
            return {
                "bid": tick_dict.get("bid", 0.0),
                "ask": tick_dict.get("ask", 0.0),
                "time": tick_dict.get("time", 0),
                "volume": tick_dict.get("volume", 0),
            }
        except Exception as e:
            logger.error(f"get_tick error: {e}")
            return None

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[dict] | None:
        if not self._connected:
            return None
        try:
            tf_map = {
                "1m": mt5.TIMEFRAME_M1,
                "5m": mt5.TIMEFRAME_M5,
                "15m": mt5.TIMEFRAME_M15,
                "30m": mt5.TIMEFRAME_M30,
                "1h": mt5.TIMEFRAME_H1,
                "4h": mt5.TIMEFRAME_H4,
                "1d": mt5.TIMEFRAME_D1,
            }
            mt5_tf = tf_map.get(timeframe, mt5.TIMEFRAME_M1)
            rates = await self._run(mt5.copy_rates_from_pos, symbol, mt5_tf, 0, limit)
            if rates is None:
                return None
            return [
                {
                    "time": int(r[0]),
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "tick_volume": int(r[5]),
                }
                for r in rates
            ]
        except Exception as e:
            logger.error(f"get_candles error: {e}")
            return None

    async def get_positions(self) -> list[dict] | None:
        if not self._connected:
            return None
        try:
            positions = await self._run(mt5.positions_get)
            if positions is None:
                return []
            return [
                {
                    "ticket": p.ticket,
                    "symbol": p.symbol,
                    "type": "BUY" if p.type == 0 else "SELL",
                    "volume": p.volume,
                    "open_price": p.price_open,
                    "current_price": p.price_current,
                    "sl": p.sl,
                    "tp": p.tp,
                    "profit": p.profit,
                    "open_time": p.time,
                    "magic": p.magic,
                    "comment": p.comment,
                }
                for p in positions
            ]
        except Exception as e:
            logger.error(f"get_positions error: {e}")
            return None

    async def create_market_buy_order(
        self, symbol: str, volume: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        return await self._send_order(
            symbol, mt5.ORDER_TYPE_BUY, volume, stop_loss, take_profit, comment
        )

    async def create_market_sell_order(
        self, symbol: str, volume: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        return await self._send_order(
            symbol, mt5.ORDER_TYPE_SELL, volume, stop_loss, take_profit, comment
        )

    async def create_stop_buy_order(
        self, symbol: str, volume: float, price: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        return await self._send_pending_order(
            symbol, mt5.ORDER_TYPE_BUY_STOP, volume, price, stop_loss, take_profit, comment
        )

    async def create_stop_sell_order(
        self, symbol: str, volume: float, price: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        return await self._send_pending_order(
            symbol, mt5.ORDER_TYPE_SELL_STOP, volume, price, stop_loss, take_profit, comment
        )

    async def modify_position(
        self, position_id: str,
        stop_loss: float | None = None, take_profit: float | None = None
    ) -> dict | None:
        try:
            ticket = int(position_id)
            positions = await self._run(mt5.positions_get, ticket=ticket)
            if not positions:
                return None
            pos = positions[0]
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": pos.symbol,
                "sl": stop_loss if stop_loss is not None else pos.sl,
                "tp": take_profit if take_profit is not None else pos.tp,
                "magic": settings.magic_number,
            }
            result = await self._run(mt5.order_send, request)
            if result is None:
                return None
            result_dict = result._asdict()
            if result_dict.get("retcode") != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Modify failed: {result_dict}")
                return None
            return {"status": "modified", "ticket": ticket}
        except Exception as e:
            logger.error(f"modify_position error: {e}")
            return None

    async def close_position(self, position_id: str) -> dict | None:
        try:
            ticket = int(position_id)
            positions = await self._run(mt5.positions_get, ticket=ticket)
            if not positions:
                return None
            pos = positions[0]
            close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
            tick = await self._run(mt5.symbol_info_tick, pos.symbol)
            if not tick:
                return None
            price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "price": price,
                "magic": settings.magic_number,
                "comment": "LOT close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = await self._run(mt5.order_send, request)
            if result is None:
                return None
            result_dict = result._asdict()
            if result_dict.get("retcode") != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Close failed: {result_dict}")
                return None
            logger.info(f"Position {ticket} closed")
            return {"status": "closed", "ticket": ticket, "profit": pos.profit}
        except Exception as e:
            logger.error(f"close_position error: {e}")
            return None

    async def _send_order(
        self, symbol: str, order_type: int, volume: float,
        stop_loss: float | None, take_profit: float | None, comment: str
    ) -> dict | None:
        try:
            tick = await self._run(mt5.symbol_info_tick, symbol)
            if not tick:
                logger.error(f"No tick for {symbol}")
                return None

            price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "magic": settings.magic_number,
                "comment": comment or "LOT",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            if stop_loss:
                request["sl"] = stop_loss
            if take_profit:
                request["tp"] = take_profit

            result = await self._run(mt5.order_send, request)
            if result is None:
                logger.error(f"Order send returned None: {mt5.last_error()}")
                return None

            result_dict = result._asdict()
            if result_dict.get("retcode") != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: retcode={result_dict.get('retcode')}, comment={result_dict.get('comment')}")
                return None

            logger.info(f"Order filled: ticket={result_dict.get('order')}, price={result_dict.get('price')}")
            return {
                "ticket": result_dict.get("order"),
                "price": result_dict.get("price"),
                "volume": result_dict.get("volume"),
            }
        except Exception as e:
            logger.error(f"_send_order error: {e}")
            return None

    async def _send_pending_order(
        self, symbol: str, order_type: int, volume: float, price: float,
        stop_loss: float | None, take_profit: float | None, comment: str
    ) -> dict | None:
        try:
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "magic": settings.magic_number,
                "comment": comment or "LOT",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            if stop_loss:
                request["sl"] = stop_loss
            if take_profit:
                request["tp"] = take_profit

            result = await self._run(mt5.order_send, request)
            if result is None:
                return None

            result_dict = result._asdict()
            if result_dict.get("retcode") != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Pending order failed: {result_dict}")
                return None

            return {
                "ticket": result_dict.get("order"),
                "price": price,
                "volume": volume,
            }
        except Exception as e:
            logger.error(f"_send_pending_order error: {e}")
            return None
