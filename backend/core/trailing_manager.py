from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PositionSLData:
    ticket: int
    open_price: float
    open_time: float
    initial_sl_distance: float
    last_sl: float = 0.0
    current_level: int = 0
    breakeven_reached: bool = False
    rapid_mode_active: bool = False
    grid_index: int = 0
    entry_source: str = ""
    sniper_score: float = 70.0
    trailing_immediate: bool = False


@dataclass
class SLModification:
    ticket: int
    new_sl: float
    level: int
    breakeven: bool
    rapid: bool
    reason: str = ""


class TrailingStopManager:
    def __init__(self, config: dict | None = None):
        cfg = config or {}

        self.level_1_multiplier: float = cfg.get("trailing_level_1_multiplier", 1.5)
        self.level_2_multiplier: float = cfg.get("trailing_level_2_multiplier", 3.0)
        self.level_3_multiplier: float = cfg.get("trailing_level_3_multiplier", 5.0)
        self.rapid_mode_atr_multiplier: float = cfg.get("rapid_mode_atr_multiplier", 0.3)

        self.time_based_be_minutes: int = cfg.get("time_based_be_minutes", 10)
        self.time_based_be_profit_threshold: float = cfg.get("time_based_be_profit_threshold", 0.5)

        self.high_volatility_expansion: float = cfg.get("high_volatility_trailing_expansion", 0.2)

        self.tracking: dict[int, PositionSLData] = {}

    def register_position(
        self,
        ticket: int,
        open_price: float,
        open_time: float,
        initial_sl_distance: float,
        grid_index: int = 0,
        entry_source: str = "",
        sniper_score: float = 70.0,
        trailing_immediate: bool = False,
    ):
        self.tracking[ticket] = PositionSLData(
            ticket=ticket,
            open_price=open_price,
            open_time=open_time,
            initial_sl_distance=initial_sl_distance,
            grid_index=grid_index,
            entry_source=entry_source,
            sniper_score=sniper_score,
            trailing_immediate=trailing_immediate,
        )

    def remove_position(self, ticket: int):
        self.tracking.pop(ticket, None)

    def scan_position(
        self,
        ticket: int,
        is_buy: bool,
        current_price: float,
        current_sl: float,
        now: float,
        point: float,
        current_atr: float = 0.0,
        high_volatility_mode: bool = False,
    ) -> SLModification | None:
        data = self.tracking.get(ticket)
        if not data:
            return None

        open_price = data.open_price
        sl_dist = data.initial_sl_distance

        if sl_dist <= 0:
            return None

        profit_distance = (
            (current_price - open_price) if is_buy
            else (open_price - current_price)
        )

        profit_ratio = profit_distance / sl_dist if sl_dist > 0 else 0.0

        new_sl = current_sl
        should_modify = False
        current_level = data.current_level
        is_be = data.breakeven_reached
        is_rapid = data.rapid_mode_active
        reason = ""

        # LEVEL 3: Rapid mode (profit >= 5x SL)
        if profit_ratio >= self.level_3_multiplier and current_level < 3:
            rapid_distance = current_atr * self.rapid_mode_atr_multiplier if current_atr > 0 else sl_dist * 0.2

            if high_volatility_mode:
                rapid_distance *= (1.0 + self.high_volatility_expansion)

            if is_buy:
                rapid_sl = current_price - rapid_distance
                if rapid_sl > new_sl + point:
                    new_sl = rapid_sl
                    should_modify = True
                    current_level = 3
                    is_rapid = True
                    reason = f"Level 3 rapid mode (profit {profit_ratio:.1f}x SL, trail={rapid_distance/point:.0f}pts)"
            else:
                rapid_sl = current_price + rapid_distance
                if rapid_sl < new_sl - point or new_sl == 0:
                    new_sl = rapid_sl
                    should_modify = True
                    current_level = 3
                    is_rapid = True
                    reason = f"Level 3 rapid mode (profit {profit_ratio:.1f}x SL, trail={rapid_distance/point:.0f}pts)"

        # If already in rapid mode, keep trailing tightly
        elif is_rapid and current_level == 3:
            rapid_distance = current_atr * self.rapid_mode_atr_multiplier if current_atr > 0 else sl_dist * 0.2
            if high_volatility_mode:
                rapid_distance *= (1.0 + self.high_volatility_expansion)

            if is_buy:
                rapid_sl = current_price - rapid_distance
                if rapid_sl > new_sl + point:
                    new_sl = rapid_sl
                    should_modify = True
                    reason = f"Rapid trailing (distance={rapid_distance/point:.0f}pts)"
            else:
                rapid_sl = current_price + rapid_distance
                if rapid_sl < new_sl - point:
                    new_sl = rapid_sl
                    should_modify = True
                    reason = f"Rapid trailing (distance={rapid_distance/point:.0f}pts)"

        # LEVEL 2: Lock 50% profit (profit >= 3x SL)
        elif profit_ratio >= self.level_2_multiplier and current_level < 2:
            locked_profit = profit_distance * 0.5
            if high_volatility_mode:
                trail_dist = locked_profit * (1.0 - self.high_volatility_expansion)
            else:
                trail_dist = locked_profit

            if is_buy:
                level2_sl = open_price + trail_dist
                if level2_sl > new_sl + point:
                    new_sl = level2_sl
                    should_modify = True
                    current_level = 2
                    reason = f"Level 2 lock 50% (profit {profit_ratio:.1f}x SL, locked={trail_dist/point:.0f}pts)"
            else:
                level2_sl = open_price - trail_dist
                if level2_sl < new_sl - point or new_sl == 0:
                    new_sl = level2_sl
                    should_modify = True
                    current_level = 2
                    reason = f"Level 2 lock 50% (profit {profit_ratio:.1f}x SL, locked={trail_dist/point:.0f}pts)"

        # LEVEL 1: Break-even (profit >= 1.5x SL)
        elif profit_ratio >= self.level_1_multiplier and current_level < 1:
            if is_buy:
                be_sl = open_price + point
                if be_sl > new_sl + point:
                    new_sl = be_sl
                    should_modify = True
                    current_level = 1
                    is_be = True
                    reason = f"Level 1 break-even (profit {profit_ratio:.1f}x SL)"
            else:
                be_sl = open_price - point
                if be_sl < new_sl - point or new_sl == 0:
                    new_sl = be_sl
                    should_modify = True
                    current_level = 1
                    is_be = True
                    reason = f"Level 1 break-even (profit {profit_ratio:.1f}x SL)"

        # Immediate trailing for strong signals (score >= 80)
        elif data.trailing_immediate and current_level == 0 and profit_ratio >= 1.0:
            if is_buy:
                imm_sl = open_price + point
                if imm_sl > new_sl + point:
                    new_sl = imm_sl
                    should_modify = True
                    current_level = 1
                    is_be = True
                    reason = f"Immediate trailing (strong signal, profit {profit_ratio:.1f}x SL)"
            else:
                imm_sl = open_price - point
                if imm_sl < new_sl - point or new_sl == 0:
                    new_sl = imm_sl
                    should_modify = True
                    current_level = 1
                    is_be = True
                    reason = f"Immediate trailing (strong signal, profit {profit_ratio:.1f}x SL)"

        # TIME-BASED BREAK-EVEN: position open > 10 min with small profit
        if not is_be and not should_modify:
            seconds_open = now - data.open_time
            minutes_open = seconds_open / 60.0

            if minutes_open >= self.time_based_be_minutes:
                if profit_ratio >= self.time_based_be_profit_threshold and profit_ratio < self.level_1_multiplier:
                    if is_buy:
                        time_be_sl = open_price + point
                        if time_be_sl > new_sl + point:
                            new_sl = time_be_sl
                            should_modify = True
                            is_be = True
                            reason = f"Time-based BE ({minutes_open:.0f}min, profit {profit_ratio:.1f}x SL)"
                    else:
                        time_be_sl = open_price - point
                        if time_be_sl < new_sl - point or new_sl == 0:
                            new_sl = time_be_sl
                            should_modify = True
                            is_be = True
                            reason = f"Time-based BE ({minutes_open:.0f}min, profit {profit_ratio:.1f}x SL)"

        if should_modify and abs(new_sl - current_sl) > point / 2:
            data.last_sl = new_sl
            data.current_level = current_level
            data.breakeven_reached = is_be
            data.rapid_mode_active = is_rapid

            logger.info(
                f"[Trailing] ticket={ticket} SL: {current_sl:.5f} -> {new_sl:.5f} | {reason}"
            )

            return SLModification(
                ticket=ticket,
                new_sl=new_sl,
                level=current_level,
                breakeven=is_be,
                rapid=is_rapid,
                reason=reason,
            )

        return None

    def cleanup(self, active_tickets: set[int]):
        removed = [t for t in self.tracking if t not in active_tickets]
        for t in removed:
            del self.tracking[t]

    def reset(self):
        self.tracking.clear()
