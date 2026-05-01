import logging

logger = logging.getLogger(__name__)


class DynamicSLCalculator:
    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.method: str = cfg.get("sl_method", "hybrid")
        self.atr_min_multiplier: float = cfg.get("sl_atr_min_multiplier", 0.4)
        self.atr_max_multiplier: float = cfg.get("sl_atr_max_multiplier", 1.0)
        self.swing_lookback: int = cfg.get("sl_swing_lookback", 10)
        self.min_distance: int = cfg.get("sl_min_distance", 30)
        self.max_distance: int = cfg.get("sl_max_distance", 180)
        self.use_volatility_adjustment: bool = cfg.get("sl_use_volatility_adjustment", True)

    def calculate(
        self,
        is_buy: bool,
        entry_price: float,
        atr_value: float,
        point: float,
        current_volatility: float = 0.0,
        average_volatility: float = 0.0,
        high_volatility_mode: bool = False,
        recent_lows: list[float] | None = None,
        recent_highs: list[float] | None = None,
        supports: list[float] | None = None,
        resistances: list[float] | None = None,
    ) -> float:
        sl_distance = 0.0

        if self.method in ("atr_adaptive", "hybrid"):
            sl_distance = self._sl_atr_adaptive(
                atr_value, current_volatility, average_volatility
            )

        if self.method in ("swing_points", "hybrid"):
            swing_sl = self._sl_by_swings(
                is_buy, entry_price, recent_lows or [], recent_highs or []
            )
            if swing_sl > 0:
                sl_distance = max(sl_distance, swing_sl) if self.method == "hybrid" else swing_sl

        if self.method == "support_resistance":
            sr_sl = self._sl_by_sr(
                is_buy, entry_price, supports or [], resistances or [], point
            )
            if sr_sl > 0:
                sl_distance = sr_sl

        if self.use_volatility_adjustment:
            sl_distance = self._adjust_by_volatility(
                sl_distance, current_volatility, average_volatility, high_volatility_mode
            )

        sl_distance = max(sl_distance, self.min_distance * point)
        sl_distance = min(sl_distance, self.max_distance * point)

        return sl_distance

    def _sl_atr_adaptive(
        self, atr_value: float, current_vol: float, average_vol: float
    ) -> float:
        if atr_value <= 0:
            return 0.0

        vol_ratio = current_vol / average_vol if average_vol > 0 else 1.0
        if vol_ratio > 1.5:
            multiplier = self.atr_max_multiplier
        elif vol_ratio > 1.0:
            multiplier = (self.atr_min_multiplier + self.atr_max_multiplier) / 1.5
        elif vol_ratio < 0.7:
            multiplier = self.atr_min_multiplier * 0.8
        else:
            multiplier = self.atr_min_multiplier

        return atr_value * multiplier

    def _sl_by_swings(
        self, is_buy: bool, entry_price: float,
        recent_lows: list[float], recent_highs: list[float]
    ) -> float:
        if is_buy and recent_lows:
            lowest = min(recent_lows[:self.swing_lookback]) if recent_lows else 0
            if lowest > 0:
                buffer = (entry_price - lowest) * 0.1
                return (entry_price - lowest) + buffer
        elif not is_buy and recent_highs:
            highest = max(recent_highs[:self.swing_lookback]) if recent_highs else 0
            if highest > 0:
                buffer = (highest - entry_price) * 0.1
                return (highest - entry_price) + buffer
        return 0.0

    def _sl_by_sr(
        self, is_buy: bool, entry_price: float,
        supports: list[float], resistances: list[float], point: float
    ) -> float:
        nearest = 0.0
        min_dist = float("inf")

        if is_buy:
            for s in supports:
                if s < entry_price:
                    dist = entry_price - s
                    if dist < min_dist and dist > self.min_distance * point:
                        min_dist = dist
                        nearest = s
        else:
            for r in resistances:
                if r > entry_price:
                    dist = r - entry_price
                    if dist < min_dist and dist > self.min_distance * point:
                        min_dist = dist
                        nearest = r

        if nearest > 0:
            buffer = min_dist * 0.05
            return min_dist + buffer
        return 0.0

    def _adjust_by_volatility(
        self, base_distance: float, current_vol: float,
        average_vol: float, high_vol_mode: bool
    ) -> float:
        adjustment = 1.0
        if high_vol_mode:
            adjustment = 1.3
        elif average_vol > 0 and current_vol > average_vol * 1.2:
            adjustment = 1.15
        elif average_vol > 0 and current_vol < average_vol * 0.6:
            adjustment = 0.9
        return base_distance * adjustment
