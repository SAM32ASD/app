import asyncio
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)

TIMEFRAME_MAP = {
    "1m": mt5.TIMEFRAME_M1,
    "5m": mt5.TIMEFRAME_M5,
    "15m": mt5.TIMEFRAME_M15,
    "30m": mt5.TIMEFRAME_M30,
    "1h": mt5.TIMEFRAME_H1,
    "4h": mt5.TIMEFRAME_H4,
    "1d": mt5.TIMEFRAME_D1,
}

MAGIC = 298347


def _run_sync(func, *args):
    return func(*args)


class MT5Connector:
    def __init__(self, login: int = 0, password: str = "", server: str = "", path: str = ""):
        self._login = login
        self._password = password
        self._server = server
        self._path = path
        self._connected = False
        self._trade = None

    async def _run(self, func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, _run_sync, func, *args)

    async def connect(self):
        def _init():
            kwargs = {}
            if self._path:
                kwargs["path"] = self._path
            if self._login:
                kwargs["login"] = self._login
                kwargs["password"] = self._password
                kwargs["server"] = self._server

            if not mt5.initialize(**kwargs):
                err = mt5.last_error()
                logger.error(f"MT5 initialize failed: {err}")
                return False

            info = mt5.terminal_info()
            acc = mt5.account_info()
            logger.info(
                f"MT5 connected: {info.name} | Account {acc.login} "
                f"@ {acc.server} | Balance ${acc.balance:.2f} | "
                f"Trade allowed: {acc.trade_allowed}"
            )
            return True

        ok = await self._run(_init)
        self._connected = ok
        if not ok:
            raise ConnectionError("Cannot connect to MT5 terminal")

    async def disconnect(self):
        await self._run(mt5.shutdown)
        self._connected = False
        logger.info("MT5 disconnected")

    async def get_account_info(self) -> dict | None:
        def _get():
            acc = mt5.account_info()
            if not acc:
                return None
            return {
                "login": acc.login,
                "server": acc.server,
                "balance": acc.balance,
                "equity": acc.equity,
                "margin": acc.margin,
                "freeMargin": acc.margin_free,
                "leverage": acc.leverage,
                "profit": acc.profit,
                "tradeAllowed": acc.trade_allowed,
                "tradeExpert": acc.trade_expert,
                "name": acc.name,
                "currency": acc.currency,
            }
        return await self._run(_get)

    async def get_tick(self, symbol: str) -> dict | None:
        def _get():
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None
            return {
                "bid": tick.bid,
                "ask": tick.ask,
                "last": tick.last,
                "volume": tick.volume,
                "time": tick.time,
                "spread": round((tick.ask - tick.bid) / 0.01),
            }
        return await self._run(_get)

    async def get_candles(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> list[dict] | None:
        def _get():
            tf = TIMEFRAME_MAP.get(timeframe, mt5.TIMEFRAME_M1)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, limit)
            if rates is None or len(rates) == 0:
                return None
            result = []
            for r in rates:
                result.append({
                    "time": int(r["time"]),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                    "tick_volume": int(r["tick_volume"]),
                    "spread": int(r["spread"]),
                    "real_volume": int(r["real_volume"]),
                })
            result.reverse()
            return result
        return await self._run(_get)

    async def get_positions(self) -> list[dict] | None:
        def _get():
            positions = mt5.positions_get(symbol="XAUUSD")
            if positions is None:
                return []
            result = []
            for p in positions:
                if p.magic != MAGIC:
                    continue
                result.append({
                    "id": p.ticket,
                    "type": "POSITION_TYPE_BUY" if p.type == mt5.ORDER_TYPE_BUY else "POSITION_TYPE_SELL",
                    "symbol": p.symbol,
                    "volume": p.volume,
                    "openPrice": p.price_open,
                    "currentPrice": p.price_current,
                    "stopLoss": p.sl,
                    "takeProfit": p.tp,
                    "profit": p.profit,
                    "swap": p.swap,
                    "commission": p.commission if hasattr(p, "commission") else 0,
                    "openTime": p.time,
                    "magic": p.magic,
                    "comment": p.comment,
                })
            return result
        return await self._run(_get)

    async def create_market_buy_order(
        self, symbol: str, volume: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        def _send():
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY,
                "price": tick.ask,
                "magic": MAGIC,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": self._get_filling(symbol),
            }
            if stop_loss:
                request["sl"] = round(stop_loss, 2)
            if take_profit:
                request["tp"] = round(take_profit, 2)

            result = mt5.order_send(request)
            return self._parse_result(result, "BUY")
        return await self._run(_send)

    async def create_market_sell_order(
        self, symbol: str, volume: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        def _send():
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_SELL,
                "price": tick.bid,
                "magic": MAGIC,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": self._get_filling(symbol),
            }
            if stop_loss:
                request["sl"] = round(stop_loss, 2)
            if take_profit:
                request["tp"] = round(take_profit, 2)

            result = mt5.order_send(request)
            return self._parse_result(result, "SELL")
        return await self._run(_send)

    async def create_stop_buy_order(
        self, symbol: str, volume: float, price: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        def _send():
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY_STOP,
                "price": round(price, 2),
                "magic": MAGIC,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": self._get_filling(symbol),
            }
            if stop_loss:
                request["sl"] = round(stop_loss, 2)
            if take_profit:
                request["tp"] = round(take_profit, 2)

            result = mt5.order_send(request)
            return self._parse_result(result, "BUY_STOP")
        return await self._run(_send)

    async def create_stop_sell_order(
        self, symbol: str, volume: float, price: float,
        stop_loss: float | None = None, take_profit: float | None = None,
        comment: str = ""
    ) -> dict | None:
        def _send():
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_SELL_STOP,
                "price": round(price, 2),
                "magic": MAGIC,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": self._get_filling(symbol),
            }
            if stop_loss:
                request["sl"] = round(stop_loss, 2)
            if take_profit:
                request["tp"] = round(take_profit, 2)

            result = mt5.order_send(request)
            return self._parse_result(result, "SELL_STOP")
        return await self._run(_send)

    async def modify_position(
        self, position_id: str,
        stop_loss: float | None = None, take_profit: float | None = None
    ) -> dict | None:
        def _modify():
            ticket = int(position_id)
            pos = mt5.positions_get(ticket=ticket)
            if not pos:
                logger.error(f"Position {ticket} not found for modification")
                return None

            p = pos[0]
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": p.symbol,
                "position": ticket,
                "sl": round(stop_loss, 2) if stop_loss is not None else p.sl,
                "tp": round(take_profit, 2) if take_profit is not None else p.tp,
                "magic": MAGIC,
            }

            result = mt5.order_send(request)
            return self._parse_result(result, "MODIFY")
        return await self._run(_modify)

    async def close_position(self, position_id: str) -> dict | None:
        def _close():
            ticket = int(position_id)
            pos = mt5.positions_get(ticket=ticket)
            if not pos:
                logger.error(f"Position {ticket} not found for closing")
                return None

            p = pos[0]
            close_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            tick = mt5.symbol_info_tick(p.symbol)
            if not tick:
                return None
            price = tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": p.symbol,
                "volume": p.volume,
                "type": close_type,
                "position": ticket,
                "price": price,
                "magic": MAGIC,
                "comment": "close by engine",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": self._get_filling(p.symbol),
            }

            result = mt5.order_send(request)
            return self._parse_result(result, "CLOSE")
        return await self._run(_close)

    def _get_filling(self, symbol: str) -> int:
        info = mt5.symbol_info(symbol)
        if info is None:
            return mt5.ORDER_FILLING_IOC
        filling = info.filling_mode
        if filling & mt5.SYMBOL_FILLING_FOK:
            return mt5.ORDER_FILLING_FOK
        if filling & mt5.SYMBOL_FILLING_IOC:
            return mt5.ORDER_FILLING_IOC
        return mt5.ORDER_FILLING_RETURN

    @staticmethod
    def _parse_result(result, action: str) -> dict | None:
        if result is None:
            logger.error(f"MT5 {action}: order_send returned None")
            return None
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(
                f"MT5 {action} failed: retcode={result.retcode} "
                f"comment={result.comment}"
            )
            return None
        logger.info(
            f"MT5 {action} OK: order={result.order} deal={result.deal} "
            f"volume={result.volume} price={result.price}"
        )
        return {
            "orderId": result.order,
            "dealId": result.deal,
            "volume": result.volume,
            "price": result.price,
            "comment": result.comment,
        }
