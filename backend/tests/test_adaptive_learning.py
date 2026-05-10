import time
from datetime import datetime, timezone

import pytest

from core.market_regime import MarketRegimeClassifier, MarketRegime, RegimeResult
from core.adaptive_learning import (
    AdaptiveLearningEngine, TradeFeedback, DailyMetrics, AdaptiveState
)


class TestMarketRegimeClassifier:
    def _build_classifier(self):
        return MarketRegimeClassifier({
            "regime_adx_trend_threshold": 30.0,
            "regime_adx_range_threshold": 20.0,
            "regime_atr_chaos_multiplier": 1.5,
            "regime_lookback_bars": 20,
        })

    def test_trending_bull_high_adx(self):
        clf = self._build_classifier()
        highs = [2400 + i * 0.5 for i in range(20)]
        lows = [2399 + i * 0.5 for i in range(20)]
        closes = [2399.5 + i * 0.5 for i in range(20)]

        result = clf.classify(
            h1_highs=highs, h1_lows=lows, h1_closes=closes,
            adx=35.0, atr_current=1.0, atr_average_20=1.0,
        )
        assert result.regime in (MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR)
        assert result.confidence > 0

    def test_ranging_low_adx(self):
        clf = self._build_classifier()
        highs = [2400.5] * 20
        lows = [2399.5] * 20
        closes = [2400.0] * 20

        result = clf.classify(
            h1_highs=highs, h1_lows=lows, h1_closes=closes,
            adx=15.0, atr_current=0.5, atr_average_20=1.0,
        )
        assert result.regime == MarketRegime.RANGING

    def test_volatile_chaos_high_atr_ratio(self):
        clf = self._build_classifier()
        highs = [2410 - i * 2 if i % 2 == 0 else 2390 + i * 2 for i in range(20)]
        lows = [2380 + i if i % 2 == 0 else 2370 - i for i in range(20)]
        closes = [(h + l) / 2 for h, l in zip(highs, lows)]

        result = clf.classify(
            h1_highs=highs, h1_lows=lows, h1_closes=closes,
            adx=22.0, atr_current=3.0, atr_average_20=1.5,
        )
        assert result.regime == MarketRegime.VOLATILE_CHAOS

    def test_consistency_bonus(self):
        clf = self._build_classifier()
        highs = [2400.5] * 20
        lows = [2399.5] * 20
        closes = [2400.0] * 20

        for _ in range(4):
            result = clf.classify(
                h1_highs=highs, h1_lows=lows, h1_closes=closes,
                adx=15.0, atr_current=0.5, atr_average_20=1.0,
            )
        assert result.confidence > 50
        assert "3x consistent" in result.triggers

    def test_regime_adjustments_trending(self):
        clf = self._build_classifier()
        highs = [2400 + i * 0.5 for i in range(20)]
        lows = [2399 + i * 0.5 for i in range(20)]
        closes = [2399.5 + i * 0.5 for i in range(20)]

        clf.classify(
            h1_highs=highs, h1_lows=lows, h1_closes=closes,
            adx=35.0, atr_current=1.0, atr_average_20=1.0,
        )
        adj = clf.get_regime_adjustments()
        assert adj["lot_adjustment"] >= 0.6
        assert "favor_direction" in adj

    def test_volatile_chaos_adjustments(self):
        clf = self._build_classifier()
        clf._last_regime = RegimeResult(
            regime=MarketRegime.VOLATILE_CHAOS, confidence=80.0,
            adx=22.0, atr_ratio=2.0, trend_direction=0.0, triggers=[]
        )
        adj = clf.get_regime_adjustments()
        assert adj["lot_adjustment"] == 0.6
        assert adj["sl_adjustment"] == 1.25
        assert adj["threshold_adjustment"] == 3


class TestAdaptiveLearningEngine:
    def _build_engine(self):
        return AdaptiveLearningEngine({
            "adaptive_threshold_min": 55,
            "adaptive_threshold_max": 62,
            "adaptive_threshold_base": 57,
            "learning_window_days": 10,
            "weight_adjustment_max_daily": 5.0,
            "drawdown_threshold_for_safe_mode": 5.0,
            "circuit_breaker_win_rate": 30.0,
            "adaptive_lot_floor": 0.3,
        })

    def test_initial_state(self):
        engine = self._build_engine()
        assert engine.state.current_threshold == 57
        assert engine.state.safe_mode is False
        assert engine.state.circuit_breaker_active is False
        assert sum(engine.state.current_weights.values()) == 100.0

    def test_effective_threshold_normal(self):
        engine = self._build_engine()
        assert engine.get_effective_threshold() == 57

    def test_effective_threshold_safe_mode(self):
        engine = self._build_engine()
        engine.state.safe_mode = True
        assert engine.get_effective_threshold() == 58

    def test_lot_multiplier_normal(self):
        engine = self._build_engine()
        mult = engine.get_lot_multiplier(70.0)
        assert mult == 1.0

    def test_lot_multiplier_safe_mode(self):
        engine = self._build_engine()
        engine.state.safe_mode = True
        mult = engine.get_lot_multiplier(70.0)
        assert mult == 0.5

    def test_lot_multiplier_low_profit_factor(self):
        engine = self._build_engine()
        engine.daily_metrics_history = [
            DailyMetrics(date="2026-05-06", regime_detected="RANGING", profit_factor=0.8, win_rate=40),
            DailyMetrics(date="2026-05-07", regime_detected="RANGING", profit_factor=0.7, win_rate=38),
            DailyMetrics(date="2026-05-08", regime_detected="RANGING", profit_factor=0.9, win_rate=42),
        ]
        mult = engine.get_lot_multiplier(70.0)
        assert mult == 0.5

    def test_record_feedback_winning(self):
        engine = self._build_engine()
        feedback = TradeFeedback(
            timestamp=time.time(), score=72.0, direction=1,
            profit_pips=15.0, won=True, regime="TRENDING_BULL",
            momentum_score=30.0, acceleration_score=20.0,
            rsi_score=10.0, volume_score=5.0, confluence_score=7.0,
        )
        engine.record_trade_feedback(feedback)
        assert len(engine.feedback_buffer) == 1

    def test_record_feedback_losing_triggers_false_signal(self):
        engine = self._build_engine()
        now = time.time()
        for i in range(3):
            feedback = TradeFeedback(
                timestamp=now + i, score=60.0, direction=1,
                profit_pips=-10.0, won=False, regime="RANGING",
                momentum_score=35.0, acceleration_score=10.0,
                rsi_score=5.0, volume_score=5.0, confluence_score=5.0,
            )
            engine.record_trade_feedback(feedback)

        assert "momentum" in engine._indicator_cooldowns
        assert engine._indicator_cooldowns["momentum"] > now

    def test_effective_weights_with_cooldown(self):
        engine = self._build_engine()
        now = time.time()
        engine._indicator_cooldowns["momentum"] = now + 3600

        weights = engine.get_effective_weights("TRENDING_BULL", now)
        assert weights["momentum"] < 35.0
        total = sum(weights.values())
        assert abs(total - 100.0) < 0.5

    def test_daily_analysis_good_performance(self):
        engine = self._build_engine()
        trades = [
            {"profit": 10, "profit_pips": 15, "sniper_score": 72},
            {"profit": 8, "profit_pips": 12, "sniper_score": 68},
            {"profit": -5, "profit_pips": -8, "sniper_score": 58},
            {"profit": 12, "profit_pips": 18, "sniper_score": 75},
        ]
        engine.daily_analysis(trades, "TRENDING_BULL", 10000.0)
        assert len(engine.daily_metrics_history) == 1
        assert engine.daily_metrics_history[0].win_rate == 75.0

    def test_daily_analysis_bad_performance_triggers_safe_mode(self):
        engine = self._build_engine()
        for day in range(3):
            trades = [
                {"profit": -10, "profit_pips": -15, "sniper_score": 60},
                {"profit": -8, "profit_pips": -12, "sniper_score": 58},
                {"profit": 2, "profit_pips": 3, "sniper_score": 62},
            ]
            engine.daily_analysis(trades, "RANGING", 10000.0)

        assert engine.state.safe_mode is True

    def test_circuit_breaker_two_bad_days(self):
        engine = self._build_engine()
        for day in range(2):
            trades = [
                {"profit": -10, "profit_pips": -15, "sniper_score": 60},
                {"profit": -8, "profit_pips": -12, "sniper_score": 58},
                {"profit": -5, "profit_pips": -8, "sniper_score": 55},
                {"profit": 1, "profit_pips": 2, "sniper_score": 62},
            ]
            engine.daily_analysis(trades, "VOLATILE_CHAOS", 10000.0)

        assert engine.state.circuit_breaker_active is True
        assert engine.state.safe_mode is True
        assert engine.state.current_threshold == 58

    def test_threshold_adjustment_capped_at_1(self):
        engine = self._build_engine()
        engine.state.current_threshold = 57
        engine.daily_metrics_history = [
            DailyMetrics(date="2026-05-06", regime_detected="TRENDING_BULL", win_rate=70, profit_factor=2.5),
            DailyMetrics(date="2026-05-07", regime_detected="TRENDING_BULL", win_rate=72, profit_factor=2.8),
            DailyMetrics(date="2026-05-08", regime_detected="TRENDING_BULL", win_rate=68, profit_factor=2.2),
        ]
        engine._adjust_threshold()
        assert engine.state.current_threshold == 58

    def test_threshold_bounded_by_min_max(self):
        engine = self._build_engine()
        engine.state.current_threshold = 62
        engine.daily_metrics_history = [
            DailyMetrics(date="2026-05-06", regime_detected="TRENDING_BULL", win_rate=80, profit_factor=3.0),
            DailyMetrics(date="2026-05-07", regime_detected="TRENDING_BULL", win_rate=82, profit_factor=3.2),
            DailyMetrics(date="2026-05-08", regime_detected="TRENDING_BULL", win_rate=78, profit_factor=2.8),
        ]
        engine._adjust_threshold()
        assert engine.state.current_threshold <= 62

    def test_safe_mode_expiry(self):
        engine = self._build_engine()
        engine.state.safe_mode = True
        engine.state.safe_mode_until = time.time() - 100
        engine.check_safe_mode_expiry()
        assert engine.state.safe_mode is False

    def test_feedback_decay(self):
        engine = self._build_engine()
        old_ts = time.time() - (6 * 86400)
        recent_ts = time.time() - 3600

        engine.feedback_buffer.append(TradeFeedback(
            timestamp=old_ts, score=70, direction=1,
            profit_pips=10, won=True, regime="TRENDING_BULL",
        ))
        engine.feedback_buffer.append(TradeFeedback(
            timestamp=recent_ts, score=65, direction=-1,
            profit_pips=-5, won=False, regime="RANGING",
        ))

        engine.apply_feedback_decay()
        assert len(engine.feedback_buffer) == 1
        assert engine.feedback_buffer[0].timestamp == recent_ts

    def test_to_dict_from_dict_roundtrip(self):
        engine = self._build_engine()
        engine.state.current_threshold = 59
        engine.state.safe_mode = True
        engine.state.current_weights = {"momentum": 30, "acceleration": 20, "rsi": 20, "volume": 15, "confluence": 15}

        data = engine.to_dict()
        new_engine = self._build_engine()
        new_engine.from_dict(data)

        assert new_engine.state.current_threshold == 59
        assert new_engine.state.safe_mode is True
        assert new_engine.state.current_weights["momentum"] == 30

    def test_weight_normalization(self):
        engine = self._build_engine()
        weights = {"momentum": 50, "acceleration": 50, "rsi": 50, "volume": 50, "confluence": 50}
        engine._normalize_weights(weights)
        total = sum(weights.values())
        assert abs(total - 100.0) < 0.5

    def test_no_analysis_on_empty_trades(self):
        engine = self._build_engine()
        engine.daily_analysis([], "TRENDING_BULL", 10000.0)
        assert len(engine.daily_metrics_history) == 0


class TestSniperUpdateWeights:
    def test_update_weights_changes_scoring(self):
        from core.sniper_ai import SniperAIEngine, SniperTick
        engine = SniperAIEngine({"sniper_min_score": 57, "sniper_tick_window": 20})

        engine.update_weights({
            "momentum": 40.0,
            "acceleration": 10.0,
            "rsi": 20.0,
            "volume": 15.0,
            "confluence": 15.0,
        })
        assert engine.w_momentum == 40.0
        assert engine.w_acceleration == 10.0

    def test_allow_entry_with_min_score_override(self):
        from core.sniper_ai import SniperAIEngine, SniperTick, SignalStrength
        engine = SniperAIEngine({"sniper_min_score": 57, "sniper_tick_window": 20})

        for i in range(25):
            engine.collect_tick(SniperTick(
                time=datetime(2026, 1, 1, 0, 0, i, tzinfo=timezone.utc),
                bid=2400.0 + i * 0.03,
                ask=2400.30 + i * 0.03,
                volume=100,
            ))
        engine.update_indicators(rsi=55.0, atr_points=150.0, adx=25.0)

        allowed_57, sig_57 = engine.allow_entry(is_buy=True, min_score_override=57)
        allowed_90, sig_90 = engine.allow_entry(is_buy=True, min_score_override=90)

        if sig_57.score >= 57:
            pass
        assert not allowed_90
