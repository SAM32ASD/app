import logging
import numpy as np
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MarketRegime(str, Enum):
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    RANGING = "RANGING"
    VOLATILE_CHAOS = "VOLATILE_CHAOS"
    UNKNOWN = "UNKNOWN"


@dataclass
class RegimeResult:
    regime: MarketRegime
    confidence: float
    adx: float
    atr_ratio: float
    trend_direction: float
    triggers: list[str]


class MarketRegimeClassifier:
    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.adx_trend_threshold: float = cfg.get("regime_adx_trend_threshold", 30.0)
        self.adx_range_threshold: float = cfg.get("regime_adx_range_threshold", 20.0)
        self.atr_chaos_multiplier: float = cfg.get("regime_atr_chaos_multiplier", 1.5)
        self.confidence_min: float = cfg.get("regime_confidence_min", 70.0)
        self.lookback_bars: int = cfg.get("regime_lookback_bars", 20)

        self._last_regime = RegimeResult(
            regime=MarketRegime.UNKNOWN, confidence=0.0,
            adx=0.0, atr_ratio=0.0, trend_direction=0.0, triggers=[]
        )
        self._regime_history: list[MarketRegime] = []

    @property
    def current_regime(self) -> RegimeResult:
        return self._last_regime

    def classify(
        self,
        h1_highs: list[float],
        h1_lows: list[float],
        h1_closes: list[float],
        adx: float,
        atr_current: float,
        atr_average_20: float,
        tick_prices: list[float] | None = None,
    ) -> RegimeResult:
        triggers = []
        scores = {
            MarketRegime.TRENDING_BULL: 0.0,
            MarketRegime.TRENDING_BEAR: 0.0,
            MarketRegime.RANGING: 0.0,
            MarketRegime.VOLATILE_CHAOS: 0.0,
        }

        # 1) ADX-based trend detection
        if adx > self.adx_trend_threshold:
            triggers.append(f"ADX={adx:.1f}>30 (trending)")
            # Determine direction from price structure
            if len(h1_closes) >= self.lookback_bars:
                recent = h1_closes[:self.lookback_bars]
                ma20 = np.mean(recent)
                current = recent[0] if recent else 0

                higher_highs = self._count_higher_highs(h1_highs[:self.lookback_bars])
                lower_lows = self._count_lower_lows(h1_lows[:self.lookback_bars])

                if current > ma20 and higher_highs >= lower_lows:
                    scores[MarketRegime.TRENDING_BULL] += 40
                    triggers.append("price>MA20 + higher highs")
                elif current < ma20 and lower_lows >= higher_highs:
                    scores[MarketRegime.TRENDING_BEAR] += 40
                    triggers.append("price<MA20 + lower lows")
                else:
                    scores[MarketRegime.TRENDING_BULL] += 20
                    scores[MarketRegime.TRENDING_BEAR] += 20
        elif adx < self.adx_range_threshold:
            scores[MarketRegime.RANGING] += 35
            triggers.append(f"ADX={adx:.1f}<20 (ranging)")

        # 2) ATR ratio (chaos detection)
        atr_ratio = atr_current / atr_average_20 if atr_average_20 > 0 else 1.0
        if atr_ratio > self.atr_chaos_multiplier:
            scores[MarketRegime.VOLATILE_CHAOS] += 40
            triggers.append(f"ATR_ratio={atr_ratio:.2f}>1.5 (chaotic)")
        elif atr_ratio < 0.7:
            scores[MarketRegime.RANGING] += 15
            triggers.append(f"ATR_ratio={atr_ratio:.2f}<0.7 (compressed)")

        # 3) Bollinger-like squeeze detection for ranging
        if len(h1_closes) >= self.lookback_bars:
            std = np.std(h1_closes[:self.lookback_bars])
            mean = np.mean(h1_closes[:self.lookback_bars])
            bb_width = (std * 2) / mean * 100 if mean > 0 else 0

            if bb_width < 0.8:
                scores[MarketRegime.RANGING] += 20
                triggers.append(f"BB_width={bb_width:.2f}% (squeeze)")
            elif bb_width > 2.5:
                scores[MarketRegime.VOLATILE_CHAOS] += 15
                triggers.append(f"BB_width={bb_width:.2f}% (expansion)")

        # 4) Rejection wicks / gaps for chaos
        if len(h1_highs) >= 10 and len(h1_lows) >= 10 and len(h1_closes) >= 10:
            wick_count = 0
            for i in range(min(10, len(h1_highs))):
                body = abs(h1_closes[i] - (h1_closes[i+1] if i+1 < len(h1_closes) else h1_closes[i]))
                full_range = h1_highs[i] - h1_lows[i]
                if full_range > 0 and body / full_range < 0.3:
                    wick_count += 1
            if wick_count >= 5:
                scores[MarketRegime.VOLATILE_CHAOS] += 15
                triggers.append(f"rejection_wicks={wick_count}/10")

        # 5) Tick-level micro-trend confirmation
        if tick_prices and len(tick_prices) >= 50:
            recent_50 = tick_prices[:50]
            tick_direction = (recent_50[0] - recent_50[-1])
            if tick_direction > 0:
                scores[MarketRegime.TRENDING_BULL] += 10
            elif tick_direction < 0:
                scores[MarketRegime.TRENDING_BEAR] += 10

        # Determine winner
        max_regime = max(scores, key=scores.get)
        max_score = scores[max_regime]
        total = sum(scores.values())
        confidence = (max_score / total * 100) if total > 0 else 0

        # Consistency bonus: if last 3 results agree
        self._regime_history.append(max_regime)
        if len(self._regime_history) > 10:
            self._regime_history = self._regime_history[-10:]

        if len(self._regime_history) >= 3 and all(r == max_regime for r in self._regime_history[-3:]):
            confidence = min(100, confidence + 15)
            triggers.append("3x consistent")

        trend_direction = 0.0
        if max_regime == MarketRegime.TRENDING_BULL:
            trend_direction = 1.0
        elif max_regime == MarketRegime.TRENDING_BEAR:
            trend_direction = -1.0

        result = RegimeResult(
            regime=max_regime,
            confidence=round(confidence, 1),
            adx=adx,
            atr_ratio=round(atr_ratio, 2),
            trend_direction=trend_direction,
            triggers=triggers,
        )

        if result.regime != self._last_regime.regime:
            logger.info(
                f"[Regime] Change: {self._last_regime.regime.value} -> {result.regime.value} "
                f"(confidence={result.confidence}%) triggers={triggers}"
            )

        self._last_regime = result
        return result

    def _count_higher_highs(self, highs: list[float]) -> int:
        count = 0
        for i in range(len(highs) - 1):
            if highs[i] > highs[i + 1]:
                count += 1
        return count

    def _count_lower_lows(self, lows: list[float]) -> int:
        count = 0
        for i in range(len(lows) - 1):
            if lows[i] < lows[i + 1]:
                count += 1
        return count

    def get_regime_weights(self) -> dict[str, float]:
        """Return recommended indicator weights for current regime."""
        regime = self._last_regime.regime

        weights = {
            MarketRegime.TRENDING_BULL: {
                "momentum": 35, "acceleration": 25, "rsi": 15, "volume": 10, "pattern": 15
            },
            MarketRegime.TRENDING_BEAR: {
                "momentum": 35, "acceleration": 25, "rsi": 15, "volume": 10, "pattern": 15
            },
            MarketRegime.RANGING: {
                "momentum": 10, "acceleration": 10, "rsi": 35, "volume": 15, "pattern": 30
            },
            MarketRegime.VOLATILE_CHAOS: {
                "momentum": 15, "acceleration": 30, "rsi": 20, "volume": 25, "pattern": 10
            },
        }

        return weights.get(regime, {
            "momentum": 25, "acceleration": 20, "rsi": 25, "volume": 15, "pattern": 15
        })

    def get_regime_adjustments(self) -> dict:
        """Return trading adjustments based on current regime."""
        regime = self._last_regime.regime

        if regime == MarketRegime.TRENDING_BULL:
            return {
                "favor_direction": 1,
                "counter_trend_min_score": 85,
                "lot_adjustment": 1.0,
                "sl_adjustment": 1.0,
                "threshold_adjustment": 0,
            }
        elif regime == MarketRegime.TRENDING_BEAR:
            return {
                "favor_direction": -1,
                "counter_trend_min_score": 85,
                "lot_adjustment": 1.0,
                "sl_adjustment": 1.0,
                "threshold_adjustment": 0,
            }
        elif regime == MarketRegime.RANGING:
            return {
                "favor_direction": 0,
                "counter_trend_min_score": 57,
                "lot_adjustment": 1.0,
                "sl_adjustment": 1.0,
                "threshold_adjustment": 2,
            }
        elif regime == MarketRegime.VOLATILE_CHAOS:
            return {
                "favor_direction": 0,
                "counter_trend_min_score": 60,
                "lot_adjustment": 0.6,
                "sl_adjustment": 1.25,
                "threshold_adjustment": 3,
            }
        return {
            "favor_direction": 0,
            "counter_trend_min_score": 57,
            "lot_adjustment": 1.0,
            "sl_adjustment": 1.0,
            "threshold_adjustment": 0,
        }
