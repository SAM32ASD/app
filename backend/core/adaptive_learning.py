import logging
import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from collections import deque

from core.market_regime import MarketRegime

logger = logging.getLogger(__name__)


@dataclass
class DailyMetrics:
    date: str
    regime_detected: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_profit_pips: float = 0.0
    avg_loss_pips: float = 0.0
    max_drawdown_pips: float = 0.0
    avg_score_of_wins: float = 0.0
    avg_score_of_losses: float = 0.0
    best_performing_indicator: str = ""
    worst_performing_indicator: str = ""


@dataclass
class TradeFeedback:
    timestamp: float
    score: float
    direction: int
    profit_pips: float
    won: bool
    regime: str
    momentum_score: float = 0.0
    acceleration_score: float = 0.0
    rsi_score: float = 0.0
    volume_score: float = 0.0
    confluence_score: float = 0.0


@dataclass
class AdaptiveState:
    current_threshold: int = 57
    current_weights: dict = field(default_factory=lambda: {
        "momentum": 25.0, "acceleration": 20.0, "rsi": 25.0,
        "volume": 15.0, "confluence": 15.0
    })
    safe_mode: bool = False
    safe_mode_until: float = 0.0
    last_adjustment_date: str = ""
    circuit_breaker_active: bool = False


class AdaptiveLearningEngine:
    WEIGHT_MIN = 5.0
    WEIGHT_MAX = 50.0
    WEIGHT_SUM = 100.0
    MAX_DAILY_ADJUSTMENT = 5.0
    THRESHOLD_MIN = 55
    THRESHOLD_MAX = 62
    THRESHOLD_BASE = 57
    LEARNING_WINDOW_DAYS = 10
    FEEDBACK_BUFFER_SIZE = 100
    FEEDBACK_DECAY_DAYS = 5

    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.THRESHOLD_MIN = cfg.get("adaptive_threshold_min", 55)
        self.THRESHOLD_MAX = cfg.get("adaptive_threshold_max", 62)
        self.THRESHOLD_BASE = cfg.get("adaptive_threshold_base", 57)
        self.LEARNING_WINDOW_DAYS = cfg.get("learning_window_days", 10)
        self.MAX_DAILY_ADJUSTMENT = cfg.get("weight_adjustment_max_daily", 5.0)
        self.drawdown_threshold = cfg.get("drawdown_threshold_for_safe_mode", 5.0)
        self.circuit_breaker_win_rate = cfg.get("circuit_breaker_win_rate", 30.0)
        self.lot_floor = cfg.get("adaptive_lot_floor", 0.3)

        self.state = AdaptiveState()
        self.feedback_buffer: deque[TradeFeedback] = deque(maxlen=self.FEEDBACK_BUFFER_SIZE)
        self.daily_metrics_history: list[DailyMetrics] = []

        self._regime_weights: dict[str, dict[str, float]] = {
            MarketRegime.TRENDING_BULL.value: {"momentum": 35, "acceleration": 25, "rsi": 15, "volume": 10, "confluence": 15},
            MarketRegime.TRENDING_BEAR.value: {"momentum": 35, "acceleration": 25, "rsi": 15, "volume": 10, "confluence": 15},
            MarketRegime.RANGING.value: {"momentum": 10, "acceleration": 10, "rsi": 35, "volume": 15, "confluence": 30},
            MarketRegime.VOLATILE_CHAOS.value: {"momentum": 15, "acceleration": 30, "rsi": 20, "volume": 25, "confluence": 10},
        }

        self._indicator_false_signals: dict[str, list[float]] = {
            "momentum": [], "acceleration": [], "rsi": [], "volume": [], "confluence": []
        }
        self._indicator_cooldowns: dict[str, float] = {}

    def record_trade_feedback(self, feedback: TradeFeedback):
        self.feedback_buffer.append(feedback)
        if not feedback.won:
            self._record_false_signal(feedback)

    def _record_false_signal(self, feedback: TradeFeedback):
        scores = {
            "momentum": feedback.momentum_score,
            "acceleration": feedback.acceleration_score,
            "rsi": feedback.rsi_score,
            "volume": feedback.volume_score,
            "confluence": feedback.confluence_score,
        }
        dominant = max(scores, key=scores.get)
        self._indicator_false_signals[dominant].append(feedback.timestamp)

        recent = [t for t in self._indicator_false_signals[dominant] if feedback.timestamp - t < 3600]
        self._indicator_false_signals[dominant] = recent

        if len(recent) >= 3:
            self._indicator_cooldowns[dominant] = feedback.timestamp + 7200
            logger.warning(
                f"[Adaptive] {dominant} cooldown activated: 3 false signals in 1h, "
                f"weight reduced for 2h"
            )

    def get_effective_weights(self, regime: str, now: float) -> dict[str, float]:
        base_weights = self._regime_weights.get(regime, self.state.current_weights).copy()

        for indicator, cooldown_until in self._indicator_cooldowns.items():
            if now < cooldown_until:
                base_weights[indicator] *= 0.5

        total = sum(base_weights.values())
        if total > 0:
            factor = self.WEIGHT_SUM / total
            base_weights = {k: v * factor for k, v in base_weights.items()}

        return base_weights

    def get_effective_threshold(self) -> int:
        if self.state.safe_mode:
            return max(self.state.current_threshold, 58)
        return self.state.current_threshold

    def get_lot_multiplier(self, score: float) -> float:
        if self.state.safe_mode:
            return max(self.lot_floor, 0.5)

        recent_3d = self._get_metrics_last_n_days(3)
        if recent_3d:
            avg_pf = self._avg_profit_factor(recent_3d)
            if avg_pf < 1.0:
                return max(self.lot_floor, 0.5)

            avg_wr = self._avg_win_rate(recent_3d)
            if avg_wr < 45 and score < 57:
                return max(self.lot_floor, 0.6)

        return 1.0

    def daily_analysis(self, trades: list[dict], current_regime: str, account_balance: float):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if not trades:
            return

        metrics = self._compute_daily_metrics(trades, current_regime, today)
        self.daily_metrics_history.append(metrics)

        if len(self.daily_metrics_history) > self.LEARNING_WINDOW_DAYS:
            self.daily_metrics_history = self.daily_metrics_history[-self.LEARNING_WINDOW_DAYS:]

        self._adjust_weights(metrics, current_regime)
        self._adjust_threshold()
        self._check_circuit_breaker()

        self.state.last_adjustment_date = today

        logger.info(
            f"[Adaptive] Daily analysis complete: "
            f"threshold={self.state.current_threshold} "
            f"safe_mode={self.state.safe_mode} "
            f"metrics={metrics.win_rate:.1f}%WR PF={metrics.profit_factor:.2f}"
        )

    def _compute_daily_metrics(self, trades: list[dict], regime: str, date: str) -> DailyMetrics:
        wins = [t for t in trades if t.get("profit", 0) > 0]
        losses = [t for t in trades if t.get("profit", 0) <= 0]

        total_profit = sum(t.get("profit", 0) for t in wins)
        total_loss = abs(sum(t.get("profit", 0) for t in losses))

        win_scores = [t.get("sniper_score", 0) for t in wins if t.get("sniper_score")]
        loss_scores = [t.get("sniper_score", 0) for t in losses if t.get("sniper_score")]

        profits_pips = [t.get("profit_pips", 0) for t in wins]
        losses_pips = [abs(t.get("profit_pips", 0)) for t in losses]

        return DailyMetrics(
            date=date,
            regime_detected=regime,
            total_trades=len(trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=(len(wins) / len(trades) * 100) if trades else 0,
            profit_factor=(total_profit / total_loss) if total_loss > 0 else (10.0 if total_profit > 0 else 0),
            avg_profit_pips=sum(profits_pips) / len(profits_pips) if profits_pips else 0,
            avg_loss_pips=sum(losses_pips) / len(losses_pips) if losses_pips else 0,
            max_drawdown_pips=max(losses_pips) if losses_pips else 0,
            avg_score_of_wins=sum(win_scores) / len(win_scores) if win_scores else 0,
            avg_score_of_losses=sum(loss_scores) / len(loss_scores) if loss_scores else 0,
        )

    def _adjust_weights(self, metrics: DailyMetrics, regime: str):
        if regime not in self._regime_weights:
            return

        weights = self._regime_weights[regime]

        if metrics.win_rate > 60:
            best = self._identify_best_indicator()
            worst = self._identify_worst_indicator()
            if best and worst and best != worst:
                adj = min(2.0, self.MAX_DAILY_ADJUSTMENT)
                weights[best] = min(self.WEIGHT_MAX, weights[best] + adj)
                weights[worst] = max(self.WEIGHT_MIN, weights[worst] - adj)
                metrics.best_performing_indicator = best
                metrics.worst_performing_indicator = worst
        elif metrics.win_rate < 40:
            worst = self._identify_worst_indicator()
            best = self._identify_best_indicator()
            if best and worst and best != worst:
                adj = min(2.0, self.MAX_DAILY_ADJUSTMENT)
                weights[worst] = max(self.WEIGHT_MIN, weights[worst] - adj)
                weights[best] = min(self.WEIGHT_MAX, weights[best] + adj)

        self._normalize_weights(weights)
        self._regime_weights[regime] = weights
        self.state.current_weights = weights.copy()

    def _adjust_threshold(self):
        recent_3d = self._get_metrics_last_n_days(3)
        if not recent_3d:
            return

        avg_wr = self._avg_win_rate(recent_3d)
        avg_pf = self._avg_profit_factor(recent_3d)
        max_dd = max(m.max_drawdown_pips for m in recent_3d)

        old_threshold = self.state.current_threshold
        new_threshold = old_threshold

        if avg_wr > 65:
            new_threshold = min(old_threshold + 1, self.THRESHOLD_MAX)
        elif avg_wr < 45:
            new_threshold = max(old_threshold - 1, self.THRESHOLD_MIN)

        if avg_pf < 1.0:
            self.state.safe_mode = True
            self.state.safe_mode_until = datetime.now(timezone.utc).timestamp() + 86400
            logger.warning(f"[Adaptive] PF < 1.0 → safe mode activated for 24h")

        if max_dd > self.drawdown_threshold * 10:
            new_threshold = max(60, new_threshold)
            self.state.safe_mode = True
            self.state.safe_mode_until = datetime.now(timezone.utc).timestamp() + 86400
            logger.warning(f"[Adaptive] Drawdown > {self.drawdown_threshold}% → threshold=60, safe mode")

        change = new_threshold - old_threshold
        if abs(change) > 1:
            new_threshold = old_threshold + (1 if change > 0 else -1)

        self.state.current_threshold = new_threshold

        if new_threshold != old_threshold:
            logger.info(
                f"[Adaptive] Threshold: {old_threshold} -> {new_threshold} "
                f"(WR_3d={avg_wr:.1f}%, PF_3d={avg_pf:.2f})"
            )

    def _check_circuit_breaker(self):
        recent_2d = self._get_metrics_last_n_days(2)
        if len(recent_2d) < 2:
            return

        if all(m.win_rate < self.circuit_breaker_win_rate for m in recent_2d):
            logger.warning(
                f"[Adaptive] CIRCUIT BREAKER: win rate < {self.circuit_breaker_win_rate}% "
                f"for 2 consecutive days → resetting weights + threshold 58"
            )
            self._reset_to_defaults()
            self.state.current_threshold = 58
            self.state.safe_mode = True
            self.state.safe_mode_until = datetime.now(timezone.utc).timestamp() + 86400
            self.state.circuit_breaker_active = True

    def _reset_to_defaults(self):
        default_weights = {"momentum": 25, "acceleration": 20, "rsi": 25, "volume": 15, "confluence": 15}
        self.state.current_weights = default_weights.copy()
        self._regime_weights = {
            MarketRegime.TRENDING_BULL.value: {"momentum": 35, "acceleration": 25, "rsi": 15, "volume": 10, "confluence": 15},
            MarketRegime.TRENDING_BEAR.value: {"momentum": 35, "acceleration": 25, "rsi": 15, "volume": 10, "confluence": 15},
            MarketRegime.RANGING.value: {"momentum": 10, "acceleration": 10, "rsi": 35, "volume": 15, "confluence": 30},
            MarketRegime.VOLATILE_CHAOS.value: {"momentum": 15, "acceleration": 30, "rsi": 20, "volume": 25, "confluence": 10},
        }

    def _normalize_weights(self, weights: dict[str, float]):
        total = sum(weights.values())
        if total <= 0:
            return
        factor = self.WEIGHT_SUM / total
        for k in weights:
            weights[k] = round(max(self.WEIGHT_MIN, min(self.WEIGHT_MAX, weights[k] * factor)), 1)

        diff = self.WEIGHT_SUM - sum(weights.values())
        if abs(diff) > 0.1:
            max_key = max(weights, key=weights.get)
            weights[max_key] += diff

    def _identify_best_indicator(self) -> str | None:
        if not self.feedback_buffer:
            return None
        wins = [f for f in self.feedback_buffer if f.won]
        if not wins:
            return None

        avg_scores = {}
        for indicator in ["momentum", "acceleration", "rsi", "volume", "confluence"]:
            scores = [getattr(f, f"{indicator}_score") for f in wins]
            avg_scores[indicator] = sum(scores) / len(scores) if scores else 0

        return max(avg_scores, key=avg_scores.get)

    def _identify_worst_indicator(self) -> str | None:
        if not self.feedback_buffer:
            return None
        losses = [f for f in self.feedback_buffer if not f.won]
        if not losses:
            return None

        avg_scores = {}
        for indicator in ["momentum", "acceleration", "rsi", "volume", "confluence"]:
            scores = [getattr(f, f"{indicator}_score") for f in losses]
            avg_scores[indicator] = sum(scores) / len(scores) if scores else 0

        return max(avg_scores, key=avg_scores.get)

    def _get_metrics_last_n_days(self, n: int) -> list[DailyMetrics]:
        return self.daily_metrics_history[-n:]

    def _avg_win_rate(self, metrics: list[DailyMetrics]) -> float:
        if not metrics:
            return 0
        return sum(m.win_rate for m in metrics) / len(metrics)

    def _avg_profit_factor(self, metrics: list[DailyMetrics]) -> float:
        if not metrics:
            return 0
        return sum(m.profit_factor for m in metrics) / len(metrics)

    def check_safe_mode_expiry(self):
        now = datetime.now(timezone.utc).timestamp()
        if self.state.safe_mode and now >= self.state.safe_mode_until:
            self.state.safe_mode = False
            self.state.circuit_breaker_active = False
            logger.info("[Adaptive] Safe mode expired, returning to normal operation")

    def apply_feedback_decay(self):
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - (self.FEEDBACK_DECAY_DAYS * 86400)

        valid = [f for f in self.feedback_buffer if f.timestamp > cutoff]
        self.feedback_buffer = deque(valid, maxlen=self.FEEDBACK_BUFFER_SIZE)

    def to_dict(self) -> dict:
        return {
            "current_threshold": self.state.current_threshold,
            "current_weights": self.state.current_weights,
            "safe_mode": self.state.safe_mode,
            "circuit_breaker_active": self.state.circuit_breaker_active,
            "last_adjustment_date": self.state.last_adjustment_date,
            "feedback_buffer_size": len(self.feedback_buffer),
            "daily_metrics_count": len(self.daily_metrics_history),
            "regime_weights": self._regime_weights,
        }

    def from_dict(self, data: dict):
        self.state.current_threshold = data.get("current_threshold", self.THRESHOLD_BASE)
        self.state.current_weights = data.get("current_weights", self.state.current_weights)
        self.state.safe_mode = data.get("safe_mode", False)
        self.state.circuit_breaker_active = data.get("circuit_breaker_active", False)
        self.state.last_adjustment_date = data.get("last_adjustment_date", "")
        if "regime_weights" in data:
            self._regime_weights = data["regime_weights"]
