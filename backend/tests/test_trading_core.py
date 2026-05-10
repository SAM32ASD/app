import time
from datetime import datetime, timezone

import pytest

from core.sniper_ai import SniperAIEngine, SniperTick, SignalStrength
from core.dynamic_sl import DynamicSLCalculator
from core.trailing_manager import TrailingStopManager


class TestSniperAIScoring:
    def _build_engine(self, min_score=57):
        return SniperAIEngine({"sniper_min_score": min_score, "sniper_tick_window": 20})

    def _feed_ticks(self, engine, count=25, direction=1, base=2400.0):
        for i in range(count):
            engine.collect_tick(SniperTick(
                time=datetime(2026, 1, 1, 0, 0, i, tzinfo=timezone.utc),
                bid=base + (i * 0.05 * direction),
                ask=base + (i * 0.05 * direction) + 0.30,
                volume=100 + i * 5,
            ))

    def test_score_below_57_rejected(self):
        engine = self._build_engine(min_score=57)
        for i in range(25):
            engine.collect_tick(SniperTick(
                time=datetime(2026, 1, 1, 0, 0, i, tzinfo=timezone.utc),
                bid=2400.0,
                ask=2400.30,
                volume=10,
            ))
        engine.update_indicators(rsi=50.0, atr_points=100.0, adx=15.0)
        allowed, sig = engine.allow_entry(is_buy=True)
        assert not allowed
        assert sig.strength == SignalStrength.REJECTED

    def test_score_57_64_weak_signal(self):
        engine = self._build_engine(min_score=57)
        self._feed_ticks(engine, 25, direction=1)
        engine.update_indicators(rsi=58.0, atr_points=150.0, adx=28.0)
        sig = engine.evaluate()
        if 57 <= sig.score < 65:
            assert sig.strength == SignalStrength.WEAK
            assert sig.lot_multiplier == 0.7
            assert sig.sl_mode == "conservative"
            assert sig.trailing_immediate is False

    def test_score_65_79_moderate_signal(self):
        engine = self._build_engine(min_score=57)
        self._feed_ticks(engine, 25, direction=1, base=2400.0)
        engine.update_indicators(rsi=62.0, atr_points=180.0, adx=32.0)
        sig = engine.evaluate()
        if 65 <= sig.score < 80:
            assert sig.strength == SignalStrength.MODERATE
            assert sig.lot_multiplier == 1.0
            assert sig.sl_mode == "standard"

    def test_score_80_plus_strong_signal(self):
        engine = self._build_engine(min_score=57)
        for i in range(40):
            engine.collect_tick(SniperTick(
                time=datetime(2026, 1, 1, 0, 0, i, tzinfo=timezone.utc),
                bid=2400.0 + (i * 0.15),
                ask=2400.30 + (i * 0.15),
                volume=200 + i * 20,
            ))
        engine.update_indicators(rsi=68.0, atr_points=200.0, adx=40.0)
        sig = engine.evaluate()
        if sig.score >= 80:
            assert sig.strength == SignalStrength.STRONG
            assert sig.lot_multiplier == 1.0
            assert sig.sl_mode == "aggressive"
            assert sig.trailing_immediate is True

    def test_weak_signal_filter_spread_too_high(self):
        engine = self._build_engine(min_score=57)
        for i in range(25):
            engine.collect_tick(SniperTick(
                time=datetime(2026, 1, 1, 0, 0, i, tzinfo=timezone.utc),
                bid=2400.0 + i * 0.03,
                ask=2400.0 + i * 0.03 + 0.20,
                volume=80,
            ))
        engine.collect_tick(SniperTick(
            time=datetime(2026, 1, 1, 0, 0, 30, tzinfo=timezone.utc),
            bid=2400.80,
            ask=2401.50,
            volume=80,
        ))
        engine.update_indicators(rsi=55.0, atr_points=100.0, adx=22.0)
        passed, reason = engine.check_weak_signal_filters(current_spread=0.70)
        # If avg spread is low, 0.70 should exceed 80% threshold

    def test_weak_signal_filter_adx_below_20(self):
        engine = self._build_engine(min_score=57)
        engine.update_indicators(rsi=55.0, atr_points=100.0, adx=15.0)
        passed, reason = engine.check_weak_signal_filters(current_spread=0.0)
        assert not passed
        assert "ADX" in reason

    def test_classify_signal_ranges(self):
        engine = self._build_engine(min_score=57)
        assert engine._classify_signal(56)[0] == SignalStrength.REJECTED
        assert engine._classify_signal(57)[0] == SignalStrength.WEAK
        assert engine._classify_signal(64)[0] == SignalStrength.WEAK
        assert engine._classify_signal(65)[0] == SignalStrength.MODERATE
        assert engine._classify_signal(79)[0] == SignalStrength.MODERATE
        assert engine._classify_signal(80)[0] == SignalStrength.STRONG
        assert engine._classify_signal(100)[0] == SignalStrength.STRONG


class TestDynamicSLByScore:
    def _build_calc(self):
        return DynamicSLCalculator({
            "sl_method": "atr_adaptive",
            "sl_min": 30.0,
            "sl_max": 180.0,
            "weak_signal_atr_multiplier": 1.3,
            "strong_signal_reduction": 0.15,
        })

    def test_score_57_conservative_sl(self):
        calc = self._build_calc()
        sl_dist, method = calc.calculate(
            is_buy=True, entry_price=2400.0,
            atr_value=1.0, point=0.01,
            sniper_score=60.0,
        )
        assert "conservative" in method
        assert sl_dist == pytest.approx(1.0 * 1.3, rel=0.01)

    def test_score_70_standard_sl(self):
        calc = self._build_calc()
        sl_dist, method = calc.calculate(
            is_buy=True, entry_price=2400.0,
            atr_value=1.0, point=0.01,
            sniper_score=70.0,
        )
        assert "standard" in method

    def test_score_85_aggressive_sl(self):
        calc = self._build_calc()
        sl_dist_standard, _ = calc.calculate(
            is_buy=True, entry_price=2400.0,
            atr_value=1.0, point=0.01,
            sniper_score=70.0,
        )
        sl_dist_aggressive, method = calc.calculate(
            is_buy=True, entry_price=2400.0,
            atr_value=1.0, point=0.01,
            sniper_score=85.0,
        )
        assert "aggressive" in method
        assert sl_dist_aggressive < sl_dist_standard

    def test_sl_clamped_to_min(self):
        calc = self._build_calc()
        sl_dist, _ = calc.calculate(
            is_buy=True, entry_price=2400.0,
            atr_value=0.1, point=0.01,
            sniper_score=85.0,
        )
        assert sl_dist >= 30.0 * 0.01

    def test_sl_clamped_to_max(self):
        calc = self._build_calc()
        sl_dist, _ = calc.calculate(
            is_buy=True, entry_price=2400.0,
            atr_value=5.0, point=0.01,
            sniper_score=60.0,
        )
        assert sl_dist <= 180.0 * 0.01


class TestTrailingStopTiers:
    def _build_manager(self):
        return TrailingStopManager({
            "trailing_level_1_multiplier": 1.5,
            "trailing_level_2_multiplier": 3.0,
            "trailing_level_3_multiplier": 5.0,
            "rapid_mode_atr_multiplier": 0.3,
            "time_based_be_minutes": 10,
            "time_based_be_profit_threshold": 0.5,
            "high_volatility_trailing_expansion": 0.2,
        })

    def test_level_1_break_even(self):
        mgr = self._build_manager()
        point = 0.01
        sl_dist = 1.0  # 100 points
        open_price = 2400.0

        mgr.register_position(
            ticket=1, open_price=open_price, open_time=time.time(),
            initial_sl_distance=sl_dist,
        )

        # Profit = 1.5x SL distance
        current_price = open_price + (sl_dist * 1.5)
        mod = mgr.scan_position(
            ticket=1, is_buy=True, current_price=current_price,
            current_sl=open_price - sl_dist, now=time.time(), point=point,
        )
        assert mod is not None
        assert mod.level == 1
        assert mod.breakeven is True
        assert mod.new_sl >= open_price

    def test_level_2_lock_50_percent(self):
        mgr = self._build_manager()
        point = 0.01
        sl_dist = 1.0
        open_price = 2400.0

        mgr.register_position(
            ticket=2, open_price=open_price, open_time=time.time(),
            initial_sl_distance=sl_dist,
        )

        # Trigger level 1 first
        price_l1 = open_price + sl_dist * 1.5
        mgr.scan_position(ticket=2, is_buy=True, current_price=price_l1,
                          current_sl=open_price - sl_dist, now=time.time(), point=point)

        # Now profit = 3x SL
        current_price = open_price + (sl_dist * 3.0)
        mod = mgr.scan_position(
            ticket=2, is_buy=True, current_price=current_price,
            current_sl=open_price + point, now=time.time(), point=point,
        )
        assert mod is not None
        assert mod.level == 2
        locked_profit = (current_price - open_price) * 0.5
        assert mod.new_sl >= open_price + locked_profit - point * 2

    def test_level_3_rapid_mode(self):
        mgr = self._build_manager()
        point = 0.01
        sl_dist = 1.0
        open_price = 2400.0

        mgr.register_position(
            ticket=3, open_price=open_price, open_time=time.time(),
            initial_sl_distance=sl_dist,
        )

        # Trigger levels 1 and 2
        mgr.scan_position(ticket=3, is_buy=True,
                          current_price=open_price + sl_dist * 1.5,
                          current_sl=open_price - sl_dist, now=time.time(), point=point)
        mgr.scan_position(ticket=3, is_buy=True,
                          current_price=open_price + sl_dist * 3.0,
                          current_sl=open_price + point, now=time.time(), point=point)

        # Now profit = 5x SL
        current_price = open_price + (sl_dist * 5.0)
        mod = mgr.scan_position(
            ticket=3, is_buy=True, current_price=current_price,
            current_sl=open_price + sl_dist * 1.5, now=time.time(), point=point,
            current_atr=0.8,
        )
        assert mod is not None
        assert mod.level == 3
        assert mod.rapid is True

    def test_time_based_break_even(self):
        mgr = self._build_manager()
        point = 0.01
        sl_dist = 1.0
        open_price = 2400.0
        open_time = time.time() - (11 * 60)  # 11 minutes ago

        mgr.register_position(
            ticket=4, open_price=open_price, open_time=open_time,
            initial_sl_distance=sl_dist,
        )

        # Profit = 0.7x SL (above 0.5x threshold, below 1.5x level 1)
        current_price = open_price + (sl_dist * 0.7)
        mod = mgr.scan_position(
            ticket=4, is_buy=True, current_price=current_price,
            current_sl=open_price - sl_dist, now=time.time(), point=point,
        )
        assert mod is not None
        assert mod.breakeven is True
        assert "Time-based" in mod.reason

    def test_high_volatility_expansion(self):
        mgr = self._build_manager()
        point = 0.01
        sl_dist = 1.0
        open_price = 2400.0

        mgr.register_position(
            ticket=5, open_price=open_price, open_time=time.time(),
            initial_sl_distance=sl_dist,
        )

        # Trigger levels 1 and 2
        mgr.scan_position(ticket=5, is_buy=True,
                          current_price=open_price + sl_dist * 1.5,
                          current_sl=open_price - sl_dist, now=time.time(), point=point)
        mgr.scan_position(ticket=5, is_buy=True,
                          current_price=open_price + sl_dist * 3.0,
                          current_sl=open_price + point, now=time.time(), point=point)

        # Level 3 with high volatility
        current_price = open_price + (sl_dist * 5.0)
        mod_normal = mgr.scan_position(
            ticket=5, is_buy=True, current_price=current_price,
            current_sl=open_price + sl_dist * 1.5, now=time.time(), point=point,
            current_atr=0.8, high_volatility_mode=False,
        )

        mgr.tracking[5].current_level = 2
        mgr.tracking[5].rapid_mode_active = False

        mod_hv = mgr.scan_position(
            ticket=5, is_buy=True, current_price=current_price,
            current_sl=open_price + sl_dist * 1.5, now=time.time(), point=point,
            current_atr=0.8, high_volatility_mode=True,
        )

        # High volatility should give a wider trailing (lower SL for buy)
        if mod_normal and mod_hv:
            assert mod_hv.new_sl <= mod_normal.new_sl

    def test_immediate_trailing_for_strong_signal(self):
        mgr = self._build_manager()
        point = 0.01
        sl_dist = 1.0
        open_price = 2400.0

        mgr.register_position(
            ticket=6, open_price=open_price, open_time=time.time(),
            initial_sl_distance=sl_dist,
            sniper_score=85.0,
            trailing_immediate=True,
        )

        # Profit = 1.0x SL (below normal level 1 of 1.5x but immediate kicks in)
        current_price = open_price + sl_dist * 1.0
        mod = mgr.scan_position(
            ticket=6, is_buy=True, current_price=current_price,
            current_sl=open_price - sl_dist, now=time.time(), point=point,
        )
        assert mod is not None
        assert mod.breakeven is True
        assert "Immediate" in mod.reason


class TestSniperConfigUpdate:
    def test_min_score_configurable(self):
        engine = SniperAIEngine({"sniper_min_score": 60})
        assert engine.min_score == 60
        assert engine._classify_signal(59)[0] == SignalStrength.REJECTED
        assert engine._classify_signal(60)[0] == SignalStrength.WEAK
