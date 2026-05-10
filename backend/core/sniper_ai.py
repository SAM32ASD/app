import numpy as np
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalStrength(str, Enum):
    REJECTED = "REJECTED"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


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
    strength: SignalStrength = SignalStrength.REJECTED
    momentum: float = 0.0
    acceleration: float = 0.0
    rsi_score: float = 0.0
    vol_score: float = 0.0
    confluence_score: float = 0.0
    volume_score: float = 0.0
    reason: str = ""
    lot_multiplier: float = 1.0
    sl_mode: str = "standard"
    trailing_immediate: bool = False


class SniperAIEngine:
    BUFFER_SIZE = 200

    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.tick_buffer: deque[SniperTick] = deque(maxlen=self.BUFFER_SIZE)
        self.tick_window: int = cfg.get("sniper_tick_window", 40)
        self.min_score: int = cfg.get("sniper_min_score", 57)
        self.require_alignment: bool = cfg.get("sniper_require_alignment", True)

        self.w_momentum: float = cfg.get("sniper_w_momentum", 25.0)
        self.w_acceleration: float = cfg.get("sniper_w_acceleration", 20.0)
        self.w_rsi: float = cfg.get("sniper_w_rsi", 25.0)
        self.w_volatility: float = cfg.get("sniper_w_volatility", 10.0)
        self.w_confluence: float = cfg.get("sniper_w_confluence", 15.0)
        self.w_volume: float = cfg.get("sniper_w_volume", 15.0)

        self.weak_signal_lot_reduction: float = cfg.get("weak_signal_lot_reduction", 0.7)

        self.last_signal = SniperSignal()
        self.last_eval_time: datetime | None = None

        self._current_rsi: float = 50.0
        self._current_adx: float = 0.0
        self._current_atr_points: float = 0.0
        self._rsi_overbought: float = cfg.get("rsi_overbought", 72.0)
        self._rsi_oversold: float = cfg.get("rsi_oversold", 28.0)

        self._spread_buffer: deque[float] = deque(maxlen=50)

    def collect_tick(self, tick: SniperTick):
        if self.tick_buffer:
            last = self.tick_buffer[-1]
            if last.time == tick.time and last.bid == tick.bid:
                return
        self.tick_buffer.append(tick)
        spread = tick.ask - tick.bid
        self._spread_buffer.append(spread)

    def update_indicators(self, rsi: float, atr_points: float, adx: float = 0.0):
        self._current_rsi = rsi
        self._current_atr_points = atr_points
        self._current_adx = adx

    def _get_tick(self, n_back: int) -> SniperTick | None:
        idx = len(self.tick_buffer) - 1 - n_back
        if idx < 0 or idx >= len(self.tick_buffer):
            return None
        return self.tick_buffer[idx]

    def _classify_signal(self, score: float) -> tuple[SignalStrength, float, str, bool]:
        if score < self.min_score:
            return SignalStrength.REJECTED, 0.0, "rejected", False
        elif score < 65:
            return SignalStrength.WEAK, self.weak_signal_lot_reduction, "conservative", False
        elif score < 80:
            return SignalStrength.MODERATE, 1.0, "standard", False
        else:
            return SignalStrength.STRONG, 1.0, "aggressive", True

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

        # 5) CONFLUENCE (RSI + ADX weighting increased for score compensation)
        confluence_norm = 0.0
        if dir_momentum != 0 and dir_accel == dir_momentum:
            confluence_norm += 0.4
        if dir_rsi != 0 and dir_rsi == dir_momentum:
            confluence_norm += 0.35
        if self._current_adx > 25:
            confluence_norm += 0.25
        confluence_norm = min(1.0, confluence_norm)
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

        # CLASSIFY SIGNAL STRENGTH
        strength, lot_mult, sl_mode, trailing_imm = self._classify_signal(sig.score)
        sig.strength = strength
        sig.lot_multiplier = lot_mult
        sig.sl_mode = sl_mode
        sig.trailing_immediate = trailing_imm

        sig.reason = (
            f"score={sig.score:.1f} [{sig.strength.value}] "
            f"mom={sig.momentum:.1f} acc={sig.acceleration:.1f} "
            f"rsi={sig.rsi_score:.1f}({rsi_val:.0f}) adx={self._current_adx:.0f} "
            f"vol={sig.vol_score:.1f}(atr{atr_pts:.0f}) "
            f"conf={sig.confluence_score:.1f} volT={sig.volume_score:.1f} "
            f"dir={sig.direction} lot_mult={lot_mult} sl={sl_mode}"
        )

        self.last_signal = sig
        self.last_eval_time = datetime.utcnow()
        return sig

    def get_avg_spread(self) -> float:
        if not self._spread_buffer:
            return 0.0
        return sum(self._spread_buffer) / len(self._spread_buffer)

    def check_weak_signal_filters(self, current_spread: float) -> tuple[bool, str]:
        """Pre-execution filters for scores 57-64. Returns (passed, reason)."""
        avg_spread = self.get_avg_spread()
        if avg_spread > 0 and current_spread > avg_spread * 0.8:
            return False, f"spread {current_spread:.2f} > 80% avg ({avg_spread:.2f})"

        if self._current_adx < 20:
            return False, f"ADX {self._current_adx:.1f} < 20 (no trend)"

        if self._current_atr_points > 0:
            normalized_atr = self._current_atr_points / 100.0
            if normalized_atr > 3.0:
                return False, f"explosive volatility (normalized ATR={normalized_atr:.1f})"

        return True, "all filters passed"

    def update_weights(self, weights: dict[str, float]):
        if "momentum" in weights:
            self.w_momentum = weights["momentum"]
        if "acceleration" in weights:
            self.w_acceleration = weights["acceleration"]
        if "rsi" in weights:
            self.w_rsi = weights["rsi"]
        if "volume" in weights:
            self.w_volume = weights["volume"]
        if "confluence" in weights:
            self.w_confluence = weights["confluence"]

    def allow_entry(self, is_buy: bool, min_score_override: int | None = None) -> tuple[bool, SniperSignal]:
        sig = self.evaluate()

        effective_min = min_score_override if min_score_override is not None else self.min_score
        if sig.score < effective_min:
            sig.strength = SignalStrength.REJECTED
            logger.debug(f"[Sniper] NEUTRE: score={sig.score:.1f} < {effective_min}")
            return False, sig

        if sig.strength == SignalStrength.REJECTED:
            logger.debug(f"[Sniper] NEUTRE: score={sig.score:.1f} < {self.min_score}")
            return False, sig

        if self.require_alignment:
            if is_buy and sig.direction != 1:
                logger.debug(f"[Sniper] REJECT BUY: direction={sig.direction}")
                sig.strength = SignalStrength.REJECTED
                return False, sig
            if not is_buy and sig.direction != -1:
                logger.debug(f"[Sniper] REJECT SELL: direction={sig.direction}")
                sig.strength = SignalStrength.REJECTED
                return False, sig

        if sig.strength == SignalStrength.WEAK:
            current_spread = 0.0
            t0 = self._get_tick(0)
            if t0:
                current_spread = t0.ask - t0.bid
            passed, reason = self.check_weak_signal_filters(current_spread)
            if not passed:
                logger.info(f"[Sniper] REJECT WEAK: score={sig.score:.1f} filter_fail={reason}")
                sig.strength = SignalStrength.REJECTED
                return False, sig

        logger.info(
            f"[Sniper] ACCEPT: score={sig.score:.1f} strength={sig.strength.value} "
            f"dir={sig.direction} lot_mult={sig.lot_multiplier}"
        )
        return True, sig
