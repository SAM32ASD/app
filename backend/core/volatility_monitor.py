from dataclasses import dataclass
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class VolatilityState:
    current_volatility: float = 0.0
    average_volatility: float = 0.0
    recent_candle_volatility: float = 0.0
    normalized_atr: float = 0.0
    true_range_volatility: float = 0.0
    high_volatility_mode: bool = False
    risk_multiplier: float = 1.0
    status: str = "NORMAL"


class VolatilityMonitor:
    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.scan_interval: int = cfg.get("volatility_scan_interval", 1)
        self.min_volatility: float = cfg.get("min_volatility_percent", 0.3)
        self.max_volatility: float = cfg.get("max_volatility_percent", 5.0)
        self.allow_high_vol: bool = cfg.get("allow_high_volatility_trading", True)
        self.high_vol_risk_factor: float = cfg.get("high_volatility_risk_factor", 0.5)

        self.state = VolatilityState()
        self._last_scan_time: float = 0.0

    def calculate_intraday_volatility(
        self, h1_highs: list[float], h1_lows: list[float]
    ) -> float:
        if not h1_highs or not h1_lows or len(h1_highs) != len(h1_lows):
            return 0.0
        sum_range = 0.0
        valid = 0
        for h, l in zip(h1_highs, h1_lows):
            if h > 0 and l > 0 and h > l:
                sum_range += (h - l) / h
                valid += 1
        return (sum_range / valid * 100) if valid > 0 else 0.0

    def calculate_recent_candle_volatility(
        self, opens: list[float], highs: list[float], lows: list[float]
    ) -> float:
        if not opens or not highs or not lows:
            return 0.0
        total = 0.0
        count = 0
        for o, h, l in zip(opens, highs, lows):
            if h > 0 and l > 0 and o > 0:
                total += (h - l) / o * 100
                count += 1
        return total / count if count > 0 else 0.0

    def calculate_true_range_volatility(
        self, highs: list[float], lows: list[float], closes: list[float]
    ) -> float:
        if len(highs) < 2 or len(lows) < 2 or len(closes) < 2:
            return 0.0
        tr_sum = 0.0
        count = 0
        for i in range(len(highs) - 1):
            h = highs[i]
            l = lows[i]
            prev_c = closes[i + 1]
            if h > 0 and l > 0 and prev_c > 0:
                tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
                tr_sum += tr
                count += 1
        if count == 0:
            return 0.0
        avg_tr = tr_sum / count
        current_price = closes[0] if closes else 1.0
        return (avg_tr / current_price * 100) if current_price > 0 else 0.0

    def calculate_normalized_atr(
        self, atr_values: list[float], current_price: float
    ) -> float:
        if not atr_values or current_price <= 0:
            return 0.0
        valid = [a for a in atr_values if a > 0]
        if not valid:
            return 0.0
        avg_atr = sum(valid) / len(valid)
        return (avg_atr / current_price) * 100

    def update(
        self,
        now: float,
        h1_highs: list[float] | None = None,
        h1_lows: list[float] | None = None,
        candle_opens: list[float] | None = None,
        candle_highs: list[float] | None = None,
        candle_lows: list[float] | None = None,
        candle_closes: list[float] | None = None,
        atr_values: list[float] | None = None,
        current_price: float = 0.0,
    ):
        if now - self._last_scan_time < self.scan_interval:
            return
        self._last_scan_time = now

        new_intraday = self.calculate_intraday_volatility(h1_highs or [], h1_lows or [])

        self.state.recent_candle_volatility = self.calculate_recent_candle_volatility(
            candle_opens or [], candle_highs or [], candle_lows or []
        )

        self.state.normalized_atr = self.calculate_normalized_atr(
            atr_values or [], current_price
        )

        self.state.true_range_volatility = self.calculate_true_range_volatility(
            candle_highs or [], candle_lows or [], candle_closes or []
        )

        if self.state.average_volatility == 0:
            self.state.average_volatility = new_intraday
        else:
            self.state.average_volatility = (
                self.state.average_volatility * 0.6 + new_intraday * 0.4
            )

        self.state.current_volatility = new_intraday

        was_high = self.state.high_volatility_mode
        vol_ratio = (
            self.state.current_volatility / self.state.average_volatility
            if self.state.average_volatility > 0
            else 1.0
        )

        high_by_intraday = vol_ratio > 1.5
        high_by_recent = self.state.recent_candle_volatility > 0.8
        high_by_atr = self.state.normalized_atr > 0.6
        high_by_tr = self.state.true_range_volatility > 0.7

        self.state.high_volatility_mode = (
            (high_by_intraday and high_by_recent) or high_by_atr or high_by_tr
        )

        if self.state.high_volatility_mode and not was_high:
            logger.warning("HIGH VOLATILITY MODE ACTIVATED")
        elif not self.state.high_volatility_mode and was_high:
            logger.info("Back to normal volatility")

        self._update_risk_multiplier()
        self._update_status()

    def _update_risk_multiplier(self):
        avg = self.state.average_volatility
        cur = self.state.current_volatility
        natr = self.state.normalized_atr
        vol_ratio = cur / avg if avg > 0 else 1.0

        if vol_ratio > 2.0 or natr > 0.8:
            self.state.risk_multiplier = self.high_vol_risk_factor
        elif vol_ratio > 1.5 or natr > 0.5:
            self.state.risk_multiplier = 0.7
        elif vol_ratio < 0.5:
            self.state.risk_multiplier = 0.8
        else:
            self.state.risk_multiplier = 1.0

    def _update_status(self):
        if self.state.high_volatility_mode:
            self.state.status = "HIGH"
        elif self.state.average_volatility > 0:
            ratio = self.state.current_volatility / self.state.average_volatility
            if ratio > 1.3:
                self.state.status = "ELEVATED"
            elif ratio < 0.7:
                self.state.status = "LOW"
            else:
                self.state.status = "NORMAL"
        else:
            self.state.status = "NORMAL"

    def validate_conditions(self) -> bool:
        if self.state.current_volatility < self.min_volatility:
            return False
        if self.state.current_volatility > self.max_volatility:
            return self.allow_high_vol
        return True
