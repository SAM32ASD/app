from core.micro_timeframes import SyntheticBar
import logging

logger = logging.getLogger(__name__)


class PatternDetector:
    @staticmethod
    def detect_pattern(bars: list[SyntheticBar], point: float = 0.01) -> int:
        if len(bars) < 3:
            return 0

        idx = len(bars) - 2
        if idx < 1:
            return 0

        bar = bars[idx]
        prev = bars[idx - 1]

        o, c, h, l = bar.open, bar.close, bar.high, bar.low
        if h == l:
            return 0

        body = abs(c - o)
        rng = h - l
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l

        # Hammer (bullish)
        if lower_shadow > body * 2 and upper_shadow < body * 0.5 and c > o:
            logger.debug("Micro Hammer detected")
            return 1

        # Shooting Star (bearish)
        if upper_shadow > body * 2 and lower_shadow < body * 0.5 and c < o:
            logger.debug("Micro Shooting Star detected")
            return -1

        # Bullish Engulfing
        if (c > o and prev.close < prev.open
                and o <= prev.close and c >= prev.open):
            logger.debug("Micro Bullish Engulfing detected")
            return 1

        # Bearish Engulfing
        if (c < o and prev.close > prev.open
                and o >= prev.close and c <= prev.open):
            logger.debug("Micro Bearish Engulfing detected")
            return -1

        # Doji
        if rng > 0 and body / rng < 0.1 and rng > 2 * point:
            prev2_close = bars[idx - 2].close if idx >= 2 else prev.close
            if prev.close < prev2_close:
                logger.debug("Micro Doji bullish (after decline)")
                return 1
            else:
                logger.debug("Micro Doji bearish (after rise)")
                return -1

        return 0


class SupportResistanceDetector:
    @staticmethod
    def detect_micro_sr(
        bars: list[SyntheticBar], lookback: int = 50
    ) -> tuple[list[float], list[float]]:
        supports = []
        resistances = []
        count = len(bars)

        if count < 5:
            return supports, resistances

        start = max(0, count - lookback)
        for i in range(start + 2, count - 2):
            # Local peak = Resistance
            if (bars[i].high > bars[i - 1].high and bars[i].high > bars[i - 2].high
                    and bars[i].high > bars[i + 1].high and bars[i].high > bars[i + 2].high):
                resistances.append(bars[i].high)

            # Local trough = Support
            if (bars[i].low < bars[i - 1].low and bars[i].low < bars[i - 2].low
                    and bars[i].low < bars[i + 1].low and bars[i].low < bars[i + 2].low):
                supports.append(bars[i].low)

        return supports, resistances

    @staticmethod
    def detect_key_levels(
        highs_h4: list[float], lows_h4: list[float], point: float = 0.01, lookback: int = 100
    ) -> tuple[list[float], list[float]]:
        supports = []
        resistances = []

        limit = min(lookback, len(highs_h4))
        for i in range(2, limit - 2):
            h0 = highs_h4[i]
            if (h0 > highs_h4[i - 1] and h0 > highs_h4[i + 1]
                    and abs(h0 - highs_h4[i - 2]) / point < 100
                    and abs(h0 - highs_h4[i + 2]) / point < 100):
                resistances.append(h0)

        limit = min(lookback, len(lows_h4))
        for i in range(2, limit - 2):
            l0 = lows_h4[i]
            if (l0 < lows_h4[i - 1] and l0 < lows_h4[i + 1]
                    and abs(l0 - lows_h4[i - 2]) / point < 100
                    and abs(l0 - lows_h4[i + 2]) / point < 100):
                supports.append(l0)

        return supports, resistances
