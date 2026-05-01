from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)

MAX_MICRO_BARS = 2000


@dataclass
class SyntheticBar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int = 1


class MicroTimeframeBuilder:
    def __init__(self, interval_seconds: int, max_bars: int = MAX_MICRO_BARS):
        self.interval = interval_seconds
        self.max_bars = max_bars
        self.bars: list[SyntheticBar] = []

    @property
    def count(self) -> int:
        return len(self.bars)

    def _bar_time(self, ts: float) -> float:
        return ts - (ts % self.interval)

    def update(self, timestamp: float, price: float):
        bar_ts = self._bar_time(timestamp)
        bar_dt = datetime.utcfromtimestamp(bar_ts)

        if not self.bars or self.bars[-1].time != bar_dt:
            if len(self.bars) >= self.max_bars:
                self.bars.pop(0)
            self.bars.append(SyntheticBar(
                time=bar_dt, open=price, high=price, low=price, close=price, tick_volume=1
            ))
        else:
            bar = self.bars[-1]
            if price > bar.high:
                bar.high = price
            if price < bar.low:
                bar.low = price
            bar.close = price
            bar.tick_volume += 1

    def reset(self):
        self.bars.clear()


class MicroTimeframeManager:
    INTERVALS = {
        "5s": 5,
        "10s": 10,
        "15s": 15,
        "20s": 20,
        "30s": 30,
    }

    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.enabled: bool = cfg.get("use_micro_timeframes", True)
        self.enabled_tfs: dict[str, bool] = {
            "5s": cfg.get("use_micro_5s", True),
            "10s": cfg.get("use_micro_10s", True),
            "15s": cfg.get("use_micro_15s", True),
            "20s": cfg.get("use_micro_20s", True),
            "30s": cfg.get("use_micro_30s", True),
        }
        self.builders: dict[str, MicroTimeframeBuilder] = {}
        for label, secs in self.INTERVALS.items():
            self.builders[label] = MicroTimeframeBuilder(secs)

        self.cooldown_sec: int = cfg.get("micro_cooldown_sec", 3)
        self._last_trade_time: dict[str, float] = {k: 0.0 for k in self.INTERVALS}
        self._trade_counts: dict[str, int] = {k: 0 for k in self.INTERVALS}

    def update_all(self, timestamp: float, price: float):
        if not self.enabled:
            return
        for label, builder in self.builders.items():
            if self.enabled_tfs.get(label, False):
                builder.update(timestamp, price)

    def get_bars(self, label: str) -> list[SyntheticBar]:
        if label in self.builders:
            return self.builders[label].bars
        return []

    def check_cooldown(self, label: str, now: float) -> bool:
        last = self._last_trade_time.get(label, 0.0)
        if now - last < self.cooldown_sec:
            return False
        self._last_trade_time[label] = now
        return True

    def record_trade(self, label: str):
        self._trade_counts[label] = self._trade_counts.get(label, 0) + 1

    def reset(self):
        for builder in self.builders.values():
            builder.reset()
        self._last_trade_time = {k: 0.0 for k in self.INTERVALS}
        self._trade_counts = {k: 0 for k in self.INTERVALS}
