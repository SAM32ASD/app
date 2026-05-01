import numpy as np
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SniperTick:
    time: datetime
    bid: float
    ask: float
    volume: int = 0


@dataclass
class SniperSignal:
    score: float = 0.0
    direction: int = 0
    momentum: float = 0.0
    acceleration: float = 0.0
    rsi_score: float = 0.0
    vol_score: float = 0.0
    confluence_score: float = 0.0
    volume_score: float = 0.0
    reason: str = ""


class SniperAIEngine:
    BUFFER_SIZE = 200

    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.tick_buffer: deque[SniperTick] = deque(maxlen=self.BUFFER_SIZE)
        self.tick_window: int = cfg.get("sniper_tick_window", 40)
        self.min_score: int = cfg.get("sniper_min_score", 70)
        self.require_alignment: bool = cfg.get("sniper_require_alignment", True)

        self.w_momentum: float = cfg.get("sniper_w_momentum", 25.0)
        self.w_acceleration: float = cfg.get("sniper_w_acceleration", 20.0)
        self.w_rsi: float = cfg.get("sniper_w_rsi", 15.0)
        self.w_volatility: float = cfg.get("sniper_w_volatility", 10.0)
        self.w_confluence: float = cfg.get("sniper_w_confluence", 15.0)
        self.w_volume: float = cfg.get("sniper_w_volume", 15.0)

        self.last_signal = SniperSignal()
        self.last_eval_time: datetime | None = None

        self._current_rsi: float = 50.0
        self._current_atr_points: float = 0.0
        self._rsi_overbought: float = cfg.get("rsi_overbought", 72.0)
        self._rsi_oversold: float = cfg.get("rsi_oversold", 28.0)

    def collect_tick(self, tick: SniperTick):
        if self.tick_buffer:
            last = self.tick_buffer[-1]
            if last.time == tick.time and last.bid == tick.bid:
                return
        self.tick_buffer.append(tick)

    def update_indicators(self, rsi: float, atr_points: float):
        self._current_rsi = rsi
        self._current_atr_points = atr_points

    def _get_tick(self, n_back: int) -> SniperTick | None:
        idx = len(self.tick_buffer) - 1 - n_back
        if idx < 0 or idx >= len(self.tick_buffer):
            return None
        return self.tick_buffer[idx]

    def evaluate(self, point: float = 0.01) -> SniperSignal:
        sig = SniperSignal()
        buf_count = len(self.tick_buffer)
        window = min(self.tick_window, buf_count)

        if window < 10:
            sig.reason = "buffer insuffisant"
            self.last_signal = sig
            return sig

        t0 = self._get_tick(0)
        t_mid = self._get_tick(window // 2)
        t_end = self._get_tick(window - 1)

        if not t0 or not t_mid or not t_end:
            sig.reason = "ticks manquants"
            self.last_signal = sig
            return sig

        if point <= 0:
            point = 0.01

        # 1) MOMENTUM
        delta_full = (t0.bid - t_end.bid) / point
        momentum_norm = min(1.0, abs(delta_full) / 30.0)
        sig.momentum = momentum_norm * self.w_momentum
        dir_momentum = 1 if delta_full > 0 else (-1 if delta_full < 0 else 0)

        # 2) ACCELERATION
        v1 = (t0.bid - t_mid.bid) / point
        v2 = (t_mid.bid - t_end.bid) / point
        accel = v1 - v2
        accel_norm = min(1.0, abs(accel) / 15.0)
        sig.acceleration = accel_norm * self.w_acceleration
        dir_accel = 1 if accel > 0 else (-1 if accel < 0 else 0)

        # 3) RSI
        dir_rsi = 0
        rsi_val = self._current_rsi
        if rsi_val < self._rsi_overbought and rsi_val > 50:
            dir_rsi = 1
            sig.rsi_score = self.w_rsi * ((rsi_val - 50) / (self._rsi_overbought - 50))
        elif rsi_val > self._rsi_oversold and rsi_val < 50:
            dir_rsi = -1
            sig.rsi_score = self.w_rsi * ((50 - rsi_val) / (50 - self._rsi_oversold))
        else:
            sig.rsi_score = 0

        # 4) VOLATILITY REGIME
        atr_pts = self._current_atr_points
        vol_target = 200.0
        vol_score_raw = 0.0
        if atr_pts > 0:
            vol_score_raw = 1.0 - min(1.0, abs(atr_pts - vol_target) / vol_target)
        sig.vol_score = vol_score_raw * self.w_volatility

        # 5) CONFLUENCE
        confluence_norm = 0.0
        if dir_momentum != 0 and dir_accel == dir_momentum:
            confluence_norm += 0.5
        if dir_rsi != 0 and dir_rsi == dir_momentum:
            confluence_norm += 0.5
        sig.confluence_score = confluence_norm * self.w_confluence

        # 6) TICK VOLUME
        half = window // 2
        vol_recent = sum(
            (self._get_tick(i).volume if self._get_tick(i) else 0) for i in range(half)
        )
        vol_older = sum(
            (self._get_tick(i).volume if self._get_tick(i) else 0) for i in range(half, window)
        )
        vol_ratio = (vol_recent / vol_older) if vol_older > 0 else 1.0
        vol_ratio_norm = min(1.0, max(0.0, (vol_ratio - 0.8) / 1.2))
        sig.volume_score = vol_ratio_norm * self.w_volume

        # DIRECTION by weighted vote
        vote_buy = 0.0
        vote_sell = 0.0
        if dir_momentum > 0:
            vote_buy += self.w_momentum
        elif dir_momentum < 0:
            vote_sell += self.w_momentum
        if dir_accel > 0:
            vote_buy += self.w_acceleration
        elif dir_accel < 0:
            vote_sell += self.w_acceleration
        if dir_rsi > 0:
            vote_buy += self.w_rsi
        elif dir_rsi < 0:
            vote_sell += self.w_rsi

        if vote_buy > vote_sell:
            sig.direction = 1
        elif vote_sell > vote_buy:
            sig.direction = -1
        else:
            sig.direction = 0

        # TOTAL SCORE
        sig.score = (
            sig.momentum + sig.acceleration + sig.rsi_score
            + sig.vol_score + sig.confluence_score + sig.volume_score
        )
        sig.score = min(100.0, sig.score)

        sig.reason = (
            f"mom={sig.momentum:.1f} acc={sig.acceleration:.1f} "
            f"rsi={sig.rsi_score:.1f}({rsi_val:.0f}) "
            f"vol={sig.vol_score:.1f}(atr{atr_pts:.0f}) "
            f"conf={sig.confluence_score:.1f} volT={sig.volume_score:.1f} "
            f"dir={sig.direction}"
        )

        self.last_signal = sig
        self.last_eval_time = datetime.utcnow()
        return sig

    def allow_entry(self, is_buy: bool) -> bool:
        sig = self.evaluate()

        if sig.score < self.min_score:
            logger.debug(f"[Sniper] REJECT: score={sig.score:.1f} < {self.min_score} | {sig.reason}")
            return False

        if self.require_alignment:
            if is_buy and sig.direction != 1:
                logger.debug(f"[Sniper] REJECT BUY: direction={sig.direction}")
                return False
            if not is_buy and sig.direction != -1:
                logger.debug(f"[Sniper] REJECT SELL: direction={sig.direction}")
                return False

        logger.info(f"[Sniper] OK: score={sig.score:.1f} dir={sig.direction} | {sig.reason}")
        return True
