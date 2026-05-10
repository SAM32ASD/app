import asyncio
import time
import logging
from datetime import datetime, timezone
from enum import Enum

from core.sniper_ai import SniperAIEngine, SniperTick, SignalStrength
from core.micro_timeframes import MicroTimeframeManager
from core.pattern_detector import PatternDetector, SupportResistanceDetector
from core.dynamic_sl import DynamicSLCalculator
from core.risk_manager import RiskManager
from core.volatility_monitor import VolatilityMonitor
from core.trailing_manager import TrailingStopManager
from core.session_manager import SessionManager
from core.market_regime import MarketRegimeClassifier, MarketRegime
from core.adaptive_learning import AdaptiveLearningEngine, TradeFeedback
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
        self.connector = connector

        self.status = RobotStatus.STOPPED
        self._task: asyncio.Task | None = None
        self._running = False

        self.sniper = SniperAIEngine(self.config)
        self.micro_tf = MicroTimeframeManager(self.config)
        self.sl_calculator = DynamicSLCalculator(self.config)
        self.risk_manager = RiskManager(self.config)
        self.volatility = VolatilityMonitor(self.config)
        self.trailing = TrailingStopManager(self.config)
        self.session = SessionManager(self.config)
        self.regime_classifier = MarketRegimeClassifier(self.config)
        self.adaptive = AdaptiveLearningEngine(self.config)

        self._last_regime_update: float = 0
        self._regime_update_interval: float = 300.0
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
        self._current_atr: float = 0.0

    @staticmethod
    def _default_config() -> dict:
        return {
            "risk_percent": 0.5,
            "use_current_balance_for_risk": True,
            "sl_method": "hybrid",
            "sl_atr_min_multiplier": 0.4,
            "sl_atr_max_multiplier": 1.0,
            "sl_swing_lookback": 10,
            "sl_min": 30.0,
            "sl_max": 180.0,
            "sl_use_volatility_adjustment": True,
            "weak_signal_atr_multiplier": 1.3,
            "strong_signal_reduction": 0.15,
            "max_daily_loss_percent": 3.0,
            "max_consecutive_losses": 8,
            "max_trades_per_day": 500,
            "trade_cooldown_minutes": 1,
            "trailing_level_1_multiplier": 1.5,
            "trailing_level_2_multiplier": 3.0,
            "trailing_level_3_multiplier": 5.0,
            "rapid_mode_atr_multiplier": 0.3,
            "time_based_be_minutes": 10,
            "time_based_be_profit_threshold": 0.5,
            "high_volatility_trailing_expansion": 0.2,
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
            "sniper_min_score": 57,
            "sniper_tick_window": 40,
            "sniper_require_alignment": True,
            "sniper_w_momentum": 25.0,
            "sniper_w_acceleration": 20.0,
            "sniper_w_rsi": 25.0,
            "sniper_w_volatility": 10.0,
            "sniper_w_confluence": 15.0,
            "sniper_w_volume": 15.0,
            "weak_signal_lot_reduction": 0.7,
            "weak_signal_spread_threshold": 0.8,
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
        self.trailing = TrailingStopManager(self.config)
        self.session = SessionManager(self.config)
        self.regime_classifier = MarketRegimeClassifier(self.config)
        self.adaptive = AdaptiveLearningEngine(self.config)
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

    async def emergency_stop(self) -> dict:
        self._running = False
        self.status = RobotStatus.EMERGENCY
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        closed_count = 0
        if self.connector:
            try:
                closed_count = await self._close_all_positions()
            except Exception as e:
                logger.error(f"Emergency close error: {e}")

        await self._emit("emergency.triggered", {"status": "EMERGENCY", "closed_count": closed_count})
        logger.warning(f"EMERGENCY STOP - {closed_count} positions closed")
        return {"closed_count": closed_count}

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

        if self.config.get("use_sniper_ai", True):
            self.sniper.collect_tick(SniperTick(
                time=datetime.fromtimestamp(ts, tz=timezone.utc),
                bid=bid, ask=ask, volume=tick.get("volume", 0)
            ))

        if self.config.get("use_micro_timeframes", True):
            self.micro_tf.update_all(ts, bid)
            await self._analyse_micro_opportunities(ts, bid, ask)

        if now - self._last_balance_update >= 10:
            await self._update_account_info()
            self.session.update_balance()
            self._last_balance_update = now

        await self._update_positions()
        if self._open_positions:
            await self._manage_trailing(now)

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

        await self._emit("tick.update", {"bid": bid, "ask": ask, "spread": spread, "time": ts})

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

        rsi = calculate_rsi(self._m1_closes, self.config.get("rsi_period", 9))
        atr = calculate_atr(self._m1_highs, self._m1_lows, self._m1_closes, 14)
        adx = calculate_adx(self._m1_highs, self._m1_lows, self._m1_closes, 14)
        self._current_atr = atr

        if now - self._last_regime_update >= self._regime_update_interval:
            await self._update_regime(adx, atr, now)
            self._last_regime_update = now

        self.adaptive.check_safe_mode_expiry()

        self.sniper.update_indicators(rsi, atr / self.POINT if self.POINT > 0 else 0, adx)

        if self.config.get("use_rsi_filter"):
            rsi_ob = self.config.get("rsi_overbought", 72.0)
            rsi_os = self.config.get("rsi_oversold", 28.0)
        else:
            rsi_ob = 100.0
            rsi_os = 0.0

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
                    await self._execute_entry(True, high, atr, "M1")

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
                    await self._execute_entry(False, low, atr, "M1")

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
                    await self._execute_entry(True, ask, atr, f"MICRO_{label}")
                    self.micro_tf.record_trade(label)

            if signal < 0 and self.risk_manager.can_open_more(False, self._buy_positions, self._sell_positions):
                near_resistance = any(abs(ask - r) < proximity for r in resistances)
                if near_resistance:
                    atr = calculate_atr(self._m1_highs, self._m1_lows, self._m1_closes, 14)
                    await self._execute_entry(False, bid, atr, f"MICRO_{label}")
                    self.micro_tf.record_trade(label)

    async def _update_regime(self, adx: float, atr: float, now: float):
        atr_avg_20 = atr
        if len(self._h1_highs) >= 20 and len(self._h1_lows) >= 20:
            h1_atr_vals = [
                self._h1_highs[i] - self._h1_lows[i]
                for i in range(min(20, len(self._h1_highs)))
            ]
            atr_avg_20 = sum(h1_atr_vals) / len(h1_atr_vals) if h1_atr_vals else atr

        h1_closes = []
        if self._h1_highs and self._h1_lows:
            h1_closes = [(self._h1_highs[i] + self._h1_lows[i]) / 2
                         for i in range(min(len(self._h1_highs), len(self._h1_lows)))]

        tick_prices = None
        if hasattr(self.sniper, '_ticks') and self.sniper._ticks:
            tick_prices = [t.bid for t in list(self.sniper._ticks)[-50:]]

        result = self.regime_classifier.classify(
            h1_highs=self._h1_highs[:20],
            h1_lows=self._h1_lows[:20],
            h1_closes=h1_closes[:20],
            adx=adx,
            atr_current=atr,
            atr_average_20=atr_avg_20,
            tick_prices=tick_prices,
        )

        regime = result.regime.value
        weights = self.adaptive.get_effective_weights(regime, now)
        self.sniper.update_weights(weights)

        regime_adj = self.regime_classifier.get_regime_adjustments()
        self._regime_lot_adjustment = regime_adj.get("lot_adjustment", 1.0)
        self._regime_sl_adjustment = regime_adj.get("sl_adjustment", 1.0)
        self._regime_threshold_adjustment = regime_adj.get("threshold_adjustment", 0)
        self._regime_favor_direction = regime_adj.get("favor_direction", 0)

        await self._emit("regime.update", {
            "regime": regime,
            "confidence": result.confidence,
            "adx": result.adx,
            "atr_ratio": result.atr_ratio,
            "triggers": result.triggers,
        })

    async def _execute_entry(self, is_buy: bool, base_price: float, atr: float, source: str):
        regime_favor = getattr(self, "_regime_favor_direction", 0)
        if regime_favor != 0:
            counter_min = self.regime_classifier.get_regime_adjustments().get("counter_trend_min_score", 57)
            if is_buy and regime_favor == -1:
                last_score = self.sniper.last_signal.score
                if last_score < counter_min:
                    return
            elif not is_buy and regime_favor == 1:
                last_score = self.sniper.last_signal.score
                if last_score < counter_min:
                    return

        if not self.config.get("use_sniper_ai"):
            sniper_score = 70.0
            lot_multiplier = 1.0
            trailing_immediate = False
        else:
            adaptive_threshold = self.adaptive.get_effective_threshold()
            threshold_adj = getattr(self, "_regime_threshold_adjustment", 0)
            effective_min = adaptive_threshold + threshold_adj

            allowed, signal = self.sniper.allow_entry(is_buy=is_buy, min_score_override=effective_min)
            if not allowed:
                return
            sniper_score = signal.score
            lot_multiplier = signal.lot_multiplier
            trailing_immediate = signal.trailing_immediate

            adaptive_lot = self.adaptive.get_lot_multiplier(sniper_score)
            lot_multiplier *= adaptive_lot
            lot_multiplier *= getattr(self, "_regime_lot_adjustment", 1.0)

        sl_dist, sl_method = self.sl_calculator.calculate(
            is_buy=is_buy,
            entry_price=base_price,
            atr_value=atr,
            point=self.POINT,
            sniper_score=sniper_score,
            current_volatility=self.volatility.state.current_volatility,
            average_volatility=self.volatility.state.average_volatility,
            high_volatility_mode=self.volatility.state.high_volatility_mode,
            recent_lows=self._m1_lows,
            recent_highs=self._m1_highs,
        )

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
            if not self.risk_manager.can_open_more(is_buy, self._buy_positions, self._sell_positions):
                break
            if self.session.trades_today >= self.session.max_trades_per_day:
                break

            if is_buy:
                entry_price = base_price + (i * spacing * self.POINT) if not is_micro else self._last_tick_ask
                sl = entry_price - sl_dist
                tp = entry_price + (sl_dist * tp_mult)
            else:
                entry_price = base_price - (i * spacing * self.POINT) if not is_micro else self._last_tick_bid
                sl = entry_price + sl_dist
                tp = entry_price - (sl_dist * tp_mult)

            balance = self.session.get_balance_for_risk(self._account_balance)
            base_lots = self.risk_manager.calculate_lots(
                sl_dist, balance,
                self.volatility.state.current_volatility,
                self.volatility.state.average_volatility,
            )
            lots = self.risk_manager.calculate_grid_lot(i, base_lots)
            lots *= lot_multiplier

            lots = round(max(0.01, lots), 2)

            if not self.connector:
                continue

            try:
                order_type = "BUY" if is_buy else "SELL"
                comment = f"v9.7 {source}_{order_type}_{i+1} score={sniper_score:.0f}"

                if is_micro:
                    if is_buy:
                        result = await self.connector.create_market_buy_order(
                            symbol="XAUUSD", volume=lots, stop_loss=sl, take_profit=tp, comment=comment
                        )
                    else:
                        result = await self.connector.create_market_sell_order(
                            symbol="XAUUSD", volume=lots, stop_loss=sl, take_profit=tp, comment=comment
                        )
                else:
                    if is_buy:
                        if entry_price <= self._last_tick_ask + self.config.get("min_dist_points", 100) * self.POINT:
                            continue
                        result = await self.connector.create_stop_buy_order(
                            symbol="XAUUSD", volume=lots, price=entry_price,
                            stop_loss=sl, take_profit=tp, comment=comment
                        )
                    else:
                        if entry_price >= self._last_tick_bid - self.config.get("min_dist_points", 100) * self.POINT:
                            continue
                        result = await self.connector.create_stop_sell_order(
                            symbol="XAUUSD", volume=lots, price=entry_price,
                            stop_loss=sl, take_profit=tp, comment=comment
                        )

                if result:
                    self.session.record_trade_open()
                    if is_buy:
                        self._buy_positions += 1
                    else:
                        self._sell_positions += 1

                    ticket = result.get("orderId", 0)
                    self.trailing.register_position(
                        ticket=ticket,
                        open_price=entry_price,
                        open_time=time.time(),
                        initial_sl_distance=sl_dist,
                        grid_index=i,
                        entry_source=source,
                        sniper_score=sniper_score,
                        trailing_immediate=trailing_immediate,
                    )

                    await self._emit("trade.opened", {
                        "ticket": ticket,
                        "type": order_type,
                        "price": entry_price,
                        "sl": sl,
                        "tp": tp,
                        "lots": lots,
                        "source": source,
                        "sniper_score": sniper_score,
                        "sl_method": sl_method,
                        "lot_multiplier": lot_multiplier,
                    })
                    logger.info(
                        f"{order_type} {source}[{i+1}] @{entry_price:.2f} "
                        f"SL={sl:.2f}({sl_method}) TP={tp:.2f} "
                        f"Lots={lots} Score={sniper_score:.0f}"
                    )
            except Exception as e:
                logger.error(f"Error sending {order_type} order: {e}")

    async def _manage_trailing(self, now: float):
        for pos in self._open_positions:
            ticket = pos.get("id", 0)
            is_buy = pos.get("type") == "POSITION_TYPE_BUY"
            current_price = self._last_tick_bid if is_buy else self._last_tick_ask
            current_sl = pos.get("stopLoss", 0) or 0

            mod = self.trailing.scan_position(
                ticket=ticket,
                is_buy=is_buy,
                current_price=current_price,
                current_sl=current_sl,
                now=now,
                point=self.POINT,
                current_atr=self._current_atr,
                high_volatility_mode=self.volatility.state.high_volatility_mode,
            )
            if mod and self.connector:
                try:
                    current_tp = pos.get("takeProfit", 0) or 0
                    await self.connector.modify_position(
                        position_id=str(ticket),
                        stop_loss=mod.new_sl,
                        take_profit=current_tp,
                    )
                    logger.info(f"[Trailing] #{ticket}: SL {current_sl:.2f} -> {mod.new_sl:.2f} | {mod.reason}")
                except Exception as e:
                    logger.error(f"SL modification error #{ticket}: {e}")

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

    async def _close_all_positions(self) -> int:
        if not self.connector:
            return 0
        closed = 0
        try:
            positions = await self.connector.get_positions()
            for pos in (positions or []):
                ticket = pos.get("id")
                if ticket:
                    await self.connector.close_position(str(ticket))
                    closed += 1
                    logger.info(f"Emergency closed position #{ticket}")
        except Exception as e:
            logger.error(f"Close all positions error: {e}")
        return closed

    def record_trade_closed(self, trade: dict):
        profit_pips = trade.get("profit_pips", 0)
        won = trade.get("profit", 0) > 0
        score = trade.get("sniper_score", 0)
        direction = trade.get("direction", 0)

        sig = self.sniper.last_signal
        regime = self.regime_classifier.current_regime.regime.value

        feedback = TradeFeedback(
            timestamp=time.time(),
            score=score,
            direction=direction,
            profit_pips=profit_pips,
            won=won,
            regime=regime,
            momentum_score=sig.momentum,
            acceleration_score=sig.acceleration,
            rsi_score=sig.rsi_score,
            volume_score=sig.volume_score,
            confluence_score=sig.confluence_score,
        )
        self.adaptive.record_trade_feedback(feedback)

    def get_status(self) -> dict:
        regime = self.regime_classifier.current_regime
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
            "sniper_last_strength": self.sniper.last_signal.strength.value,
            "regime": regime.regime.value,
            "regime_confidence": regime.confidence,
            "adaptive_threshold": self.adaptive.get_effective_threshold(),
            "adaptive_safe_mode": self.adaptive.state.safe_mode,
            "adaptive_circuit_breaker": self.adaptive.state.circuit_breaker_active,
            "adaptive_weights": self.adaptive.state.current_weights,
        }
