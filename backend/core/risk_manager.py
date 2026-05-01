import logging

logger = logging.getLogger(__name__)

XAUUSD_MIN_LOT = 0.01
XAUUSD_LOT_STEP = 0.01


class RiskManager:
    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.risk_percent: float = cfg.get("risk_percent", 0.5)
        self.use_current_balance: bool = cfg.get("use_current_balance_for_risk", True)
        self.max_daily_loss_percent: float = cfg.get("max_daily_loss_percent", 3.0)
        self.max_consecutive_losses: int = cfg.get("max_consecutive_losses", 8)
        self.max_trades_per_day: int = cfg.get("max_trades_per_day", 500)
        self.max_positions_per_direction: int = cfg.get("max_positions_per_direction", 1)
        self.max_total_positions: int = cfg.get("max_total_positions", 2)
        self.allow_hedging: bool = cfg.get("allow_hedging", False)
        self.use_pyramiding: bool = cfg.get("use_pyramiding_lots", False)
        self.lot_multiplier: float = cfg.get("lot_multiplier", 0.5)
        self.max_spread_points: int = cfg.get("max_spread_points", 300)
        self.max_margin_usage: float = cfg.get("max_margin_usage", 60.0)
        self.max_gap_points: float = cfg.get("max_gap_points", 150.0)
        self.min_risk_reward: float = cfg.get("min_risk_reward_ratio", 2.0)
        self.high_vol_risk_factor: float = cfg.get("high_volatility_risk_factor", 0.5)
        self.trade_cooldown_minutes: int = cfg.get("trade_cooldown_minutes", 1)

    def calculate_lots(
        self,
        sl_distance: float,
        balance: float,
        current_volatility: float = 0.0,
        average_volatility: float = 0.0,
        tick_size: float = 0.01,
        tick_value: float = 0.01,
        min_lot: float = XAUUSD_MIN_LOT,
        max_lot: float = 100.0,
        lot_step: float = XAUUSD_LOT_STEP,
    ) -> float:
        if sl_distance <= 0 or balance <= 0:
            return min_lot

        risk_money = balance * self.risk_percent / 100.0

        if average_volatility > 0:
            if current_volatility > average_volatility * 2.0:
                risk_money *= 0.7
            elif current_volatility > average_volatility * 1.5:
                risk_money *= 0.85

        if tick_size <= 0:
            tick_size = 0.01
        money_risk_per_lot = (sl_distance / tick_size) * tick_value
        if money_risk_per_lot <= 0:
            return min_lot

        lots = risk_money / money_risk_per_lot
        lots = int(lots / lot_step) * lot_step

        lots = max(lots, min_lot)
        lots = min(lots, max_lot)

        return round(lots, 2)

    def calculate_grid_lot(self, grid_index: int, base_lots: float) -> float:
        if not self.use_pyramiding or grid_index == 0:
            return base_lots
        multiplier = self.lot_multiplier ** grid_index
        lots = base_lots * multiplier
        lots = int(lots / XAUUSD_LOT_STEP) * XAUUSD_LOT_STEP
        return max(lots, XAUUSD_MIN_LOT)

    def can_open_more(
        self, is_buy: bool, buy_count: int, sell_count: int
    ) -> bool:
        total = buy_count + sell_count
        if total >= self.max_total_positions:
            return False
        if is_buy and buy_count >= self.max_positions_per_direction:
            return False
        if not is_buy and sell_count >= self.max_positions_per_direction:
            return False
        if not self.allow_hedging:
            if is_buy and sell_count > 0:
                return False
            if not is_buy and buy_count > 0:
                return False
        return True

    def check_daily_loss(
        self, daily_start_balance: float, current_equity: float
    ) -> bool:
        if daily_start_balance <= 0:
            return True
        daily_loss = daily_start_balance - current_equity
        limit = daily_start_balance * self.max_daily_loss_percent / 100.0
        return daily_loss < limit

    def adjust_risk_for_volatility(
        self, current_vol: float, average_vol: float, normalized_atr: float
    ) -> float:
        vol_ratio = current_vol / average_vol if average_vol > 0 else 1.0
        if vol_ratio > 2.0 or normalized_atr > 0.8:
            return self.high_vol_risk_factor
        elif vol_ratio > 1.5 or normalized_atr > 0.5:
            return 0.7
        elif vol_ratio < 0.5:
            return 0.8
        return 1.0
