import asyncio
import time
import logging
from datetime import datetime, timezone
from enum import Enum

from core.sniper_ai import SniperAIEngine, SniperTick
from core.micro_timeframes import MicroTimeframeManager
from core.pattern_detector import PatternDetector, SupportResistanceDetector
from core.dynamic_sl import DynamicSLCalculator
from core.risk_manager import RiskManager
from core.volatility_monitor import VolatilityMonitor
from core.trailing_manager import TrailingManager
from core.session_manager import SessionManager
from core.indicators import (
    calculate_rsi, calculate_atr, calculate_adx,
    find_significant_high, find_significant_low,
)

logger = logging.getLogger(__name__)


class RobotStatus(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    EMERGENCY = "EMERGENCY"
    ERROR = "ERROR"


class TradingEngine:
    POINT = 0.01  # XAUUSD point

    def __init__(self, config: dict | None = None, connector=None):
        self.config = config or self._default_config()
        self.connector = connector  # MetaApi connector

        self.status = RobotStatus.STOPPED
        self._task: asyncio.Task | None = None
        self._running = False

        self.sniper = SniperAIEngine(self.config)
        self.micro_tf = MicroTimeframeManager(self.config)
        self.sl_calculator = DynamicSLCalculator(self.config)
        self.risk_manager = RiskManager(self.config)
        self.volatility = VolatilityMonitor(self.config)
        self.trailing = TrailingManager(self.config)
        self.session = SessionManager(self.config)

        self._last_bar_time: float = 0
        self._m1_closes: list[float] = []
        self._m1_highs: list[float] = []
        self._m1_lows: list[float] = []
        self._m1_opens: list[float] = []
        self._h1_highs: list[float] = []
        self._h1_lows: list[float] = []
        self._h4_highs: list[float] = []
        self._h4_lows: list[float] = []

        self._last_tick_bid: float = 0.0
        self._last_tick_ask: float = 0.0
        self._last_tick_time: float = 0.0

        self._buy_positions: int = 0
        self._sell_positions: int = 0
        self._open_positions: list[dict] = []
        self._account_balance: float = 0.0
        self._account_equity: float = 0.0
        self._free_margin: float = 0.0

        self._event_callbacks: list = []
        self._last_balance_update: float = 0.0

    @staticmethod
    def _default_config() -> dict:
        return {
            "risk_percent": 0.5,
            "use_current_balance_for_risk": True,
            "sl_method": "hybrid",
            "sl_atr_min_multiplier": 0.4,
            "sl_atr_max_multiplier": 1.0,
            "sl_swing_lookback": 10,
            "sl_min_distance": 30,
            "sl_max_distance": 180,
            "sl_use_volatility_adjustment": True,
            "max_daily_loss_percent": 3.0,
            "max_consecutive_losses": 8,
            "max_trades_per_day": 500,
            "trade_cooldown_minutes": 1,
            "use_trailing_stop": True,
            "use_break_even": True,
            "use_rapid_sl_movement": True,
            "use_stepped_trailing": True,
            "use_time_based_protection": True,
            "rapid_sl_trigger": 30,
            "rapid_sl_step": 20,
            "step_trigger1": 40, "step_move1": 20,
            "step_trigger2": 80, "step_move2": 50,
            "step_trigger3": 150, "step_move3": 100,
            "break_even_trigger": 40,
            "break_even_buffer": 8,
            "seconds_to_force_be": 60,
            "trail_start": 80,
            "trail_step": 40,
            "grid_breakeven_after_n": 2,
            "max_positions_per_direction": 1,
            "max_total_positions": 2,
            "allow_hedging": False,
            "use_pyramiding_lots": False,
            "lot_multiplier": 0.5,
            "entry_spacing_points": 120,
            "max_spread_points": 300,
            "max_margin_usage": 60.0,
            "max_gap_points": 150.0,
            "min_risk_reward_ratio": 2.0,
            "use_rsi_filter": True,
            "rsi_period": 9,
            "rsi_overbought": 72.0,
            "rsi_oversold": 28.0,
            "use_adx_filter": False,
            "adx_period": 14,
            "adx_min_value": 25.0,
            "use_spread_filter": True,
            "use_gap_filter": True,
            "use_volatility_filter": True,
            "use_sniper_ai": True,
            "sniper_min_score": 70,
            "sniper_tick_window": 40,
            "sniper_require_alignment": True,
            "sniper_w_momentum": 25.0,
            "sniper_w_acceleration": 20.0,
            "sniper_w_rsi": 15.0,
            "sniper_w_volatility": 10.0,
            "sniper_w_confluence": 15.0,
            "sniper_w_volume": 15.0,
            "use_micro_timeframes": True,
            "use_micro_5s": True,
            "use_micro_10s": True,
            "use_micro_15s": True,
            "use_micro_20s": True,
            "use_micro_30s": True,
            "micro_cooldown_sec": 3,
            "micro_bars_lookback": 100,
            "micro_sr_proximity_pts": 100,
            "volatility_scan_interval": 1,
            "min_volatility_percent": 0.3,
            "max_volatility_percent": 5.0,
            "allow_high_volatility_trading": True,
            "high_volatility_risk_factor": 0.5,
            "tp_points": 400,
            "bars_lookback": 25,
            "bars_n": 3,
            "min_dist_points": 100,
            "expiration_bars": 30,
            "trading_enabled": True,
        }

    def update_config(self, new_config: dict):
        self.config.update(new_config)
        self.sniper = SniperAIEngine(self.config)
        self.micro_tf = MicroTimeframeManager(self.config)
        self.sl_calculator = DynamicSLCalculator(self.config)
        self.risk_manager = RiskManager(self.config)
        self.volatility = VolatilityMonitor(self.config)
        self.trailing = TrailingManager(self.config)
        self.session = SessionManager(self.config)
        logger.info("Trading engine config updated")

    def on_event(self, callback):
        self._event_callbacks.append(callback)

    async def _emit(self, event: str, data: dict):
        for cb in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event, data)
                else:
                    cb(event, data)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    async def start(self):
        if self.status == RobotStatus.RUNNING:
            return
        self._running = True
        self.status = RobotStatus.RUNNING
        self._task = asyncio.create_task(self._main_loop())
        await self._emit("robot.status", {"status": "RUNNING"})
        logger.info("Trading engine started")

    async def stop(self):
        self._running = False
        self.status = RobotStatus.STOPPED
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._emit("robot.status", {"status": "STOPPED"})
        logger.info("Trading engine stopped")

    async def emergency_stop(self):
        self._running = False
        self.status = RobotStatus.EMERGENCY
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.connector:
            try:
                await self._close_all_positions()
            except Exception as e:
                logger.error(f"Emergency close error: {e}")
        await self._emit("emergency.triggered", {"status": "EMERGENCY"})
        logger.warning("EMERGENCY STOP triggered - all positions closed")

    async def _main_loop(self):
        logger.info("Main trading loop started")
        while self._running:
            try:
                await self._tick_cycle()
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trading loop error: {e}", exc_info=True)
                self.status = RobotStatus.ERROR
                await self._emit("robot.status", {"status": "ERROR", "error": str(e)})
                await asyncio.sleep(5)

    async def _tick_cycle(self):
        if not self.connector:
            return

        now = time.time()

        tick = await self._get_tick()
        if not tick:
            return

        bid = tick.get("bid", 0)
        ask = tick.get("ask", 0)
        ts = tick.get("time", now)
        spread = tick.get("spread", 0)

        self._last_tick_bid = bid
        self._last_tick_ask = ask
        self._last_tick_time = ts

        # Sniper AI tick collection
        if self.config.get("use_sniper_ai", True):
            self.sniper.collect_tick(SniperTick(
                time=datetime.fromtimestamp(ts, tz=timezone.utc),
                bid=bid, ask=ask, volume=tick.get("volume", 0)
            ))

        # Micro-timeframes update
        if self.config.get("use_micro_timeframes", True):
            self.micro_tf.update_all(ts, bid)
            await self._analyse_micro_opportunities(ts, bid, ask)

        # Balance update (every 10s)
        if now - self._last_balance_update >= 10:
            await self._update_account_info()
            self.session.update_balance()
            self._last_balance_update = now

        # Position tracking + SL management
        await self._update_positions()
        if self._open_positions:
            await self._manage_trailing(now)

        # Volatility scan
        self.volatility.update(
            now,
            h1_highs=self._h1_highs[:480],
            h1_lows=self._h1_lows[:480],
            candle_opens=self._m1_opens[:10],
            candle_highs=self._m1_highs[:10],
            candle_lows=self._m1_lows[:10],
            candle_closes=self._m1_closes[:10],
            current_price=bid,
        )

        # Push tick event
        await self._emit("tick.update", {
            "bid": bid, "ask": ask, "spread": spread,
            "time": ts,
        })

        # New M1 bar logic
        if await self._is_new_bar(ts):
            await self._on_new_bar(bid, ask, now)

    async def _on_new_bar(self, bid: float, ask: float, now: float):
        await self._fetch_candles()

        self.session.check_daily_reset(self._account_balance)

        can_trade, reason = self.session.can_trade(self._account_equity)
        if not can_trade:
            if reason == "daily_loss_limit":
                await self._close_all_positions()
            return

        if not self.config.get("trading_enabled", True):
            return

        if self.config.get("use_spread_filter") and not self._check_spread():
            return
        if self.config.get("use_gap_filter") and not self._check_gap():
            return
        if self.config.get("use_volatility_filter") and not self.volatility.validate_conditions():
            return

        # Update indicators
        rsi = calculate_rsi(self._m1_closes, self.config.get("rsi_period", 9))
        atr = calculate_atr(self._m1_highs, self._m1_lows, self._m1_closes, 14)
        adx = calculate_adx(self._m1_highs, self._m1_lows, self._m1_closes, 14)

        self.sniper.update_indicators(rsi, atr / self.POINT if self.POINT > 0 else 0)

        # RSI filter
        if self.config.get("use_rsi_filter"):
            rsi_ob = self.config.get("rsi_overbought", 72.0)
            rsi_os = self.config.get("rsi_oversold", 28.0)
        else:
            rsi_ob = 100.0
            rsi_os = 0.0

        # ADX filter
        if self.config.get("use_adx_filter") and adx < self.config.get("adx_min_value", 25):
            return

        # BUY logic
        if self.risk_manager.can_open_more(True, self._buy_positions, self._sell_positions):
            if rsi <= rsi_ob:
                high = find_significant_high(
                    self._m1_highs, ask,
                    self.config.get("bars_n", 3),
                    self.config.get("bars_lookback", 25),
                    self.config.get("min_dist_points", 100),
                    self.POINT,
                )
                if high > 0:
                    sl_dist = self.sl_calculator.calculate(
                        is_buy=True, entry_price=high, atr_value=atr,
                        point=self.POINT,
                        current_volatility=self.volatility.state.current_volatility,
                        average_volatility=self.volatility.state.average_volatility,
                        high_volatility_mode=self.volatility.state.high_volatility_mode,
                        recent_lows=self._m1_lows,
                        recent_highs=self._m1_highs,
                    )
                    await self._send_multi_buy(high, sl_dist, "M1")

        # SELL logic
        if self.risk_manager.can_open_more(False, self._buy_positions, self._sell_positions):
            if rsi >= rsi_os:
                low = find_significant_low(
                    self._m1_lows, bid,
                    self.config.get("bars_n", 3),
                    self.config.get("bars_lookback", 25),
                    self.config.get("min_dist_points", 100),
                    self.POINT,
                )
                if low > 0:
                    sl_dist = self.sl_calculator.calculate(
                        is_buy=False, entry_price=low, atr_value=atr,
                        point=self.POINT,
                        current_volatility=self.volatility.state.current_volatility,
                        average_volatility=self.volatility.state.average_volatility,
                        high_volatility_mode=self.volatility.state.high_volatility_mode,
                        recent_lows=self._m1_lows,
                        recent_highs=self._m1_highs,
                    )
                    await self._send_multi_sell(low, sl_dist, "M1")

    async def _analyse_micro_opportunities(self, ts: float, bid: float, ask: float):
        if not self.config.get("use_micro_timeframes"):
            return
        if not self.config.get("trading_enabled"):
            return

        can_trade, _ = self.session.can_trade(self._account_equity)
        if not can_trade:
            return

        if self.config.get("use_spread_filter") and not self._check_spread():
            return

        for label in self.micro_tf.INTERVALS:
            if not self.micro_tf.enabled_tfs.get(label, False):
                continue

            bars = self.micro_tf.get_bars(label)
            if len(bars) < 20:
                continue

            if not self.micro_tf.check_cooldown(label, ts):
                continue

            signal = PatternDetector.detect_pattern(bars, self.POINT)
            if signal == 0:
                continue

            supports, resistances = SupportResistanceDetector.detect_micro_sr(
                bars, self.config.get("micro_bars_lookback", 100)
            )

            proximity = self.config.get("micro_sr_proximity_pts", 100) * self.POINT

            if signal > 0 and self.risk_manager.can_open_more(True, self._buy_positions, self._sell_positions):
                near_support = any(abs(bid - s) < proximity for s in supports)
                if near_support:
                    atr = calculate_atr(self._m1_highs, self._m1_lows, self._m1_closes, 14)
                    sl_dist = self.sl_calculator.calculate(
                        is_buy=True, entry_price=ask, atr_value=atr,
                        point=self.POINT,
                        current_volatility=self.volatility.state.current_volatility,
                        average_volatility=self.volatility.state.average_volatility,
                        high_volatility_mode=self.volatility.state.high_volatility_mode,
                    )
                    await self._send_multi_buy(ask, sl_dist, f"MICRO_{label}")
                    self.micro_tf.record_trade(label)

            if signal < 0 and self.risk_manager.can_open_more(False, self._buy_positions, self._sell_positions):
                near_resistance = any(abs(ask - r) < proximity for r in resistances)
                if near_resistance:
                    atr = calculate_atr(self._m1_highs, self._m1_lows, self._m1_closes, 14)
                    sl_dist = self.sl_calculator.calculate(
                        is_buy=False, entry_price=bid, atr_value=atr,
                        point=self.POINT,
                        current_volatility=self.volatility.state.current_volatility,
                        average_volatility=self.volatility.state.average_volatility,
                        high_volatility_mode=self.volatility.state.high_volatility_mode,
                    )
                    await self._send_multi_sell(bid, sl_dist, f"MICRO_{label}")
                    self.micro_tf.record_trade(label)

    async def _send_multi_buy(self, base_price: float, sl_dist: float, source: str):
        if self.config.get("use_sniper_ai") and not self.sniper.allow_entry(is_buy=True):
            return

        tp_mult = self.config.get("min_risk_reward_ratio", 2.0)
        if self.volatility.state.high_volatility_mode:
            vol_spread = (
                (self.volatility.state.current_volatility - self.volatility.state.average_volatility)
                * base_price / 100
            )
            tp_mult += (vol_spread * 0.3 / sl_dist) if sl_dist > 0 else 0

        is_micro = "MICRO" in source
        spacing = self.config.get("entry_spacing_points", 120)

        for i in range(self.config.get("max_positions_per_direction", 1)):
            if not self.risk_manager.can_open_more(True, self._buy_positions, self._sell_positions):
                break
            if self.session.trades_today >= self.session.max_trades_per_day:
                break

            entry_price = base_price + (i * spacing * self.POINT) if not is_micro else self._last_tick_ask
            sl = entry_price - sl_dist
            tp = entry_price + (sl_dist * tp_mult)

            balance = self.session.get_balance_for_risk(self._account_balance)
            base_lots = self.risk_manager.calculate_lots(sl_dist, balance,
                self.volatility.state.current_volatility,
                self.volatility.state.average_volatility)
            lots = self.risk_manager.calculate_grid_lot(i, base_lots)

            if self.connector:
                try:
                    if is_micro:
                        result = await self.connector.create_market_buy_order(
                            symbol="XAUUSD", volume=lots, stop_loss=sl, take_profit=tp,
                            comment=f"v9.7 {source}_BUY_{i+1}"
                        )
                    else:
                        if entry_price <= self._last_tick_ask + self.config.get("min_dist_points", 100) * self.POINT:
                            continue
                        result = await self.connector.create_stop_buy_order(
                            symbol="XAUUSD", volume=lots, price=entry_price,
                            stop_loss=sl, take_profit=tp,
                            comment=f"v9.7 {source}_BUY_{i+1}"
                        )

                    if result:
                        self.session.record_trade_open()
                        self._buy_positions += 1
                        ticket = result.get("orderId", 0)
                        self.trailing.register_position(
                            ticket=ticket, open_price=entry_price,
                            open_time=time.time(), grid_index=i, entry_source=source
                        )
                        await self._emit("trade.opened", {
                            "ticket": ticket, "type": "BUY", "price": entry_price,
                            "sl": sl, "tp": tp, "lots": lots, "source": source
                        })
                        logger.info(f"Grid BUY {source}[{i+1}] @{entry_price:.2f} SL={sl:.2f} TP={tp:.2f} Lots={lots}")
                except Exception as e:
                    logger.error(f"Error sending BUY order: {e}")

    async def _send_multi_sell(self, base_price: float, sl_dist: float, source: str):
        if self.config.get("use_sniper_ai") and not self.sniper.allow_entry(is_buy=False):
            return

        tp_mult = self.config.get("min_risk_reward_ratio", 2.0)
        if self.volatility.state.high_volatility_mode:
            vol_spread = (
                (self.volatility.state.current_volatility - self.volatility.state.average_volatility)
                * base_price / 100
            )
            tp_mult += (vol_spread * 0.3 / sl_dist) if sl_dist > 0 else 0

        is_micro = "MICRO" in source
        spacing = self.config.get("entry_spacing_points", 120)

        for i in range(self.config.get("max_positions_per_direction", 1)):
            if not self.risk_manager.can_open_more(False, self._buy_positions, self._sell_positions):
                break
            if self.session.trades_today >= self.session.max_trades_per_day:
                break

            entry_price = base_price - (i * spacing * self.POINT) if not is_micro else self._last_tick_bid
            sl = entry_price + sl_dist
            tp = entry_price - (sl_dist * tp_mult)

            balance = self.session.get_balance_for_risk(self._account_balance)
            base_lots = self.risk_manager.calculate_lots(sl_dist, balance,
                self.volatility.state.current_volatility,
                self.volatility.state.average_volatility)
            lots = self.risk_manager.calculate_grid_lot(i, base_lots)

            if self.connector:
                try:
                    if is_micro:
                        result = await self.connector.create_market_sell_order(
                            symbol="XAUUSD", volume=lots, stop_loss=sl, take_profit=tp,
                            comment=f"v9.7 {source}_SELL_{i+1}"
                        )
                    else:
                        if entry_price >= self._last_tick_bid - self.config.get("min_dist_points", 100) * self.POINT:
                            continue
                        result = await self.connector.create_stop_sell_order(
                            symbol="XAUUSD", volume=lots, price=entry_price,
                            stop_loss=sl, take_profit=tp,
                            comment=f"v9.7 {source}_SELL_{i+1}"
                        )

                    if result:
                        self.session.record_trade_open()
                        self._sell_positions += 1
                        ticket = result.get("orderId", 0)
                        self.trailing.register_position(
                            ticket=ticket, open_price=entry_price,
                            open_time=time.time(), grid_index=i, entry_source=source
                        )
                        await self._emit("trade.opened", {
                            "ticket": ticket, "type": "SELL", "price": entry_price,
                            "sl": sl, "tp": tp, "lots": lots, "source": source
                        })
                        logger.info(f"Grid SELL {source}[{i+1}] @{entry_price:.2f} SL={sl:.2f} TP={tp:.2f} Lots={lots}")
                except Exception as e:
                    logger.error(f"Error sending SELL order: {e}")

    async def _manage_trailing(self, now: float):
        for pos in self._open_positions:
            ticket = pos.get("id", 0)
            is_buy = pos.get("type") == "POSITION_TYPE_BUY"
            current_price = self._last_tick_bid if is_buy else self._last_tick_ask
            current_sl = pos.get("stopLoss", 0) or 0
            current_tp = pos.get("takeProfit", 0) or 0

            mod = self.trailing.scan_position(
                ticket=ticket, is_buy=is_buy, current_price=current_price,
                current_sl=current_sl, current_tp=current_tp,
                now=now, point=self.POINT
            )
            if mod and self.connector:
                try:
                    await self.connector.modify_position(
                        position_id=str(ticket),
                        stop_loss=mod.new_sl, take_profit=current_tp
                    )
                    logger.info(f"SL modified ticket#{ticket}: {current_sl:.2f} -> {mod.new_sl:.2f}")
                except Exception as e:
                    logger.error(f"SL modification error ticket#{ticket}: {e}")

        active_tickets = {p.get("id", 0) for p in self._open_positions}
        self.trailing.cleanup(active_tickets)

    def _check_spread(self) -> bool:
        if self._last_tick_ask <= 0 or self._last_tick_bid <= 0:
            return True
        spread_points = (self._last_tick_ask - self._last_tick_bid) / self.POINT
        return spread_points <= self.config.get("max_spread_points", 300)

    def _check_gap(self) -> bool:
        if not self._m1_closes or self._last_tick_ask <= 0:
            return True
        prev_close = self._m1_closes[0] if self._m1_closes else 0
        if prev_close == 0:
            return True
        gap = max(
            abs(self._last_tick_ask - prev_close),
            abs(self._last_tick_bid - prev_close)
        ) / self.POINT
        return gap <= self.config.get("max_gap_points", 150)

    async def _is_new_bar(self, ts: float) -> bool:
        bar_time = ts - (ts % 60)
        if bar_time != self._last_bar_time:
            self._last_bar_time = bar_time
            return True
        return False

    async def _get_tick(self) -> dict | None:
        if not self.connector:
            return None
        try:
            return await self.connector.get_tick("XAUUSD")
        except Exception as e:
            logger.error(f"Get tick error: {e}")
            return None

    async def _fetch_candles(self):
        if not self.connector:
            return
        try:
            m1 = await self.connector.get_candles("XAUUSD", "1m", 100)
            if m1:
                self._m1_closes = [c["close"] for c in m1]
                self._m1_highs = [c["high"] for c in m1]
                self._m1_lows = [c["low"] for c in m1]
                self._m1_opens = [c["open"] for c in m1]

            h1 = await self.connector.get_candles("XAUUSD", "1h", 480)
            if h1:
                self._h1_highs = [c["high"] for c in h1]
                self._h1_lows = [c["low"] for c in h1]
        except Exception as e:
            logger.error(f"Fetch candles error: {e}")

    async def _update_account_info(self):
        if not self.connector:
            return
        try:
            info = await self.connector.get_account_info()
            if info:
                self._account_balance = info.get("balance", 0)
                self._account_equity = info.get("equity", 0)
                self._free_margin = info.get("freeMargin", 0)
                self.session.check_daily_reset(self._account_balance)
        except Exception as e:
            logger.error(f"Account info error: {e}")

    async def _update_positions(self):
        if not self.connector:
            return
        try:
            positions = await self.connector.get_positions()
            self._open_positions = positions or []
            self._buy_positions = sum(
                1 for p in self._open_positions if p.get("type") == "POSITION_TYPE_BUY"
            )
            self._sell_positions = sum(
                1 for p in self._open_positions if p.get("type") == "POSITION_TYPE_SELL"
            )

            await self._emit("position.update", {
                "positions": self._open_positions,
                "buy_count": self._buy_positions,
                "sell_count": self._sell_positions,
                "floating_pl": sum(p.get("profit", 0) for p in self._open_positions),
            })
        except Exception as e:
            logger.error(f"Update positions error: {e}")

    async def _close_all_positions(self):
        if not self.connector:
            return
        try:
            positions = await self.connector.get_positions()
            for pos in (positions or []):
                ticket = pos.get("id")
                if ticket:
                    await self.connector.close_position(str(ticket))
                    logger.info(f"Emergency closed position #{ticket}")
        except Exception as e:
            logger.error(f"Close all positions error: {e}")

    def get_status(self) -> dict:
        return {
            "robot_status": self.status.value,
            "balance": self._account_balance,
            "equity": self._account_equity,
            "daily_start_balance": self.session.daily_start_balance,
            "current_balance": self.session.current_balance,
            "today_realized_pl": self.session.today_realized_pl,
            "floating_pl": sum(p.get("profit", 0) for p in self._open_positions),
            "trades_today": self.session.trades_today,
            "max_trades_per_day": self.session.max_trades_per_day,
            "consecutive_losses": self.session.consecutive_losses,
            "max_consecutive_losses": self.session.max_consecutive_losses,
            "current_volatility": self.volatility.state.current_volatility,
            "average_volatility": self.volatility.state.average_volatility,
            "high_volatility_mode": self.volatility.state.high_volatility_mode,
            "open_positions_count": len(self._open_positions),
            "buy_positions": self._buy_positions,
            "sell_positions": self._sell_positions,
            "last_tick_price": self._last_tick_bid,
            "spread": (self._last_tick_ask - self._last_tick_bid) if self._last_tick_ask > 0 else None,
            "sniper_ai_active": self.config.get("use_sniper_ai", True),
            "sniper_last_score": self.sniper.last_signal.score,
            "sniper_last_direction": self.sniper.last_signal.direction,
        }
