from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PositionSLData:
    ticket: int
    open_price: float
    open_time: float
    last_sl: float = 0.0
    current_step: int = 0
    breakeven_reached: bool = False
    rapid_mode_active: bool = False
    grid_index: int = 0
    original_sl: float = 0.0
    entry_source: str = ""


@dataclass
class SLModification:
    ticket: int
    new_sl: float
    step: int
    breakeven: bool
    rapid: bool


class TrailingManager:
    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.use_trailing: bool = cfg.get("use_trailing_stop", True)
        self.use_breakeven: bool = cfg.get("use_break_even", True)
        self.use_rapid_sl: bool = cfg.get("use_rapid_sl_movement", True)
        self.use_stepped: bool = cfg.get("use_stepped_trailing", True)
        self.use_time_protection: bool = cfg.get("use_time_based_protection", True)

        self.rapid_trigger: int = cfg.get("rapid_sl_trigger", 30)
        self.rapid_step: int = cfg.get("rapid_sl_step", 20)

        self.step_trigger1: int = cfg.get("step_trigger1", 40)
        self.step_move1: int = cfg.get("step_move1", 20)
        self.step_trigger2: int = cfg.get("step_trigger2", 80)
        self.step_move2: int = cfg.get("step_move2", 50)
        self.step_trigger3: int = cfg.get("step_trigger3", 150)
        self.step_move3: int = cfg.get("step_move3", 100)

        self.be_trigger: int = cfg.get("break_even_trigger", 40)
        self.be_buffer: int = cfg.get("break_even_buffer", 8)
        self.seconds_to_force_be: int = cfg.get("seconds_to_force_be", 60)

        self.trail_start: int = cfg.get("trail_start", 80)
        self.trail_step: int = cfg.get("trail_step", 40)

        self.grid_be_after_n: int = cfg.get("grid_breakeven_after_n", 2)

        self.tracking: dict[int, PositionSLData] = {}

    def register_position(
        self, ticket: int, open_price: float, open_time: float,
        grid_index: int = 0, entry_source: str = ""
    ):
        self.tracking[ticket] = PositionSLData(
            ticket=ticket, open_price=open_price, open_time=open_time,
            grid_index=grid_index, entry_source=entry_source
        )

    def remove_position(self, ticket: int):
        self.tracking.pop(ticket, None)

    def scan_position(
        self, ticket: int, is_buy: bool, current_price: float,
        current_sl: float, current_tp: float, now: float, point: float
    ) -> SLModification | None:
        data = self.tracking.get(ticket)
        if not data:
            return None

        open_price = data.open_price
        profit_points = (
            (current_price - open_price) / point if is_buy
            else (open_price - current_price) / point
        )

        new_sl = current_sl
        should_modify = False
        current_step = data.current_step
        is_be = data.breakeven_reached
        is_rapid = data.rapid_mode_active

        # Rapid SL movement
        if self.use_rapid_sl and profit_points >= self.rapid_trigger and not is_rapid:
            if is_buy:
                rapid_level = open_price + (profit_points - self.rapid_step) * point
                if rapid_level > new_sl + point:
                    new_sl = rapid_level
                    should_modify = True
                    is_rapid = True
            else:
                rapid_level = open_price - (profit_points - self.rapid_step) * point
                if rapid_level < new_sl - point or new_sl == 0:
                    new_sl = rapid_level
                    should_modify = True
                    is_rapid = True

        # Stepped trailing
        if self.use_stepped and profit_points >= self.step_trigger1:
            target_step = 0
            if profit_points >= self.step_trigger3:
                target_step = 3
            elif profit_points >= self.step_trigger2:
                target_step = 2
            elif profit_points >= self.step_trigger1:
                target_step = 1

            if target_step > current_step:
                step_buffer = {
                    1: self.step_move1, 2: self.step_move2, 3: self.step_move3
                }.get(target_step, 0) * point

                if is_buy:
                    step_level = open_price + step_buffer
                    if step_level > new_sl + point:
                        new_sl = step_level
                        should_modify = True
                        current_step = target_step
                else:
                    step_level = open_price - step_buffer
                    if step_level < new_sl - point or new_sl == 0:
                        new_sl = step_level
                        should_modify = True
                        current_step = target_step

        # Break-even
        if self.use_breakeven and profit_points >= self.be_trigger and not is_be:
            if is_buy:
                be_level = open_price + self.be_buffer * point
                if be_level > new_sl + point:
                    new_sl = be_level
                    should_modify = True
                    is_be = True
            else:
                be_level = open_price - self.be_buffer * point
                if be_level < new_sl - point or new_sl == 0:
                    new_sl = be_level
                    should_modify = True
                    is_be = True

        # Time-based BE
        if self.use_time_protection and not is_be and profit_points > 20:
            seconds_open = now - data.open_time
            if seconds_open >= self.seconds_to_force_be:
                if is_buy:
                    be_level = open_price + self.be_buffer * point
                    if be_level > new_sl + point:
                        new_sl = be_level
                        should_modify = True
                        is_be = True
                else:
                    be_level = open_price - self.be_buffer * point
                    if be_level < new_sl - point or new_sl == 0:
                        new_sl = be_level
                        should_modify = True
                        is_be = True

        # Classic trailing
        if self.use_trailing and profit_points >= self.trail_start:
            if is_buy:
                trail_level = current_price - self.trail_step * point
                if trail_level > new_sl + point:
                    new_sl = trail_level
                    should_modify = True
            else:
                trail_level = current_price + self.trail_step * point
                if trail_level < new_sl - point or new_sl == 0:
                    new_sl = trail_level
                    should_modify = True

        if should_modify and abs(new_sl - current_sl) > point / 2:
            data.last_sl = new_sl
            data.current_step = current_step
            data.breakeven_reached = is_be
            data.rapid_mode_active = is_rapid
            return SLModification(
                ticket=ticket, new_sl=new_sl,
                step=current_step, breakeven=is_be, rapid=is_rapid
            )

        return None

    def cleanup(self, active_tickets: set[int]):
        removed = [t for t in self.tracking if t not in active_tickets]
        for t in removed:
            del self.tracking[t]

    def reset(self):
        self.tracking.clear()
