from pydantic import BaseModel, Field
from datetime import datetime, time
from uuid import UUID
from enum import Enum


class SLMethod(str, Enum):
    ATR_ADAPTIVE = "atr_adaptive"
    SWING_POINTS = "swing_points"
    SWINGS = "swings"
    SUPPORT_RESISTANCE = "support_resistance"
    SR = "sr"
    HYBRID = "hybrid"
    FIXED = "fixed"


class RobotStatus(str, Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    EMERGENCY = "EMERGENCY"
    ERROR = "ERROR"


class UserRole(str, Enum):
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"


class TradingConfigSchema(BaseModel):
    risk_percent: float = Field(0.5, ge=0.1, le=5.0)
    max_daily_loss_percent: float = Field(3.0, ge=0.5, le=10.0)
    max_consecutive_losses: int = Field(8, ge=1, le=50)
    max_trades_per_day: int = Field(500, ge=1, le=2000)
    sl_method: SLMethod = SLMethod.HYBRID
    use_sniper_ai: bool = True
    sniper_min_score: int = Field(70, ge=0, le=100)
    use_micro_timeframes: bool = True
    max_positions_per_direction: int = Field(1, ge=1, le=10)
    max_total_positions: int = Field(2, ge=1, le=20)
    allow_hedging: bool = False
    trading_enabled: bool = True
    scheduled_start_time: time | None = None
    scheduled_stop_time: time | None = None

    class Config:
        from_attributes = True


class TradingConfigUpdate(BaseModel):
    model_config = {"extra": "allow"}

    risk_percent: float | None = None
    max_daily_loss_percent: float | None = None
    max_consecutive_losses: int | None = None
    max_trades_per_day: int | None = None
    sl_method: SLMethod | None = None
    use_sniper_ai: bool | None = None
    sniper_min_score: int | None = None
    use_micro_timeframes: bool | None = None
    max_positions_per_direction: int | None = None
    max_total_positions: int | None = None
    allow_hedging: bool | None = None
    trading_enabled: bool | None = None
    scheduled_start_time: time | None = None
    scheduled_stop_time: time | None = None


class TradingStatusResponse(BaseModel):
    robot_status: RobotStatus
    balance: float
    equity: float
    daily_start_balance: float
    current_balance: float
    today_realized_pl: float
    floating_pl: float
    trades_today: int
    max_trades_per_day: int
    consecutive_losses: int
    max_consecutive_losses: int
    current_volatility: float
    average_volatility: float
    high_volatility_mode: bool
    open_positions_count: int
    buy_positions: int
    sell_positions: int
    last_tick_price: float | None = None
    spread: float | None = None
    sniper_ai_active: bool
    sniper_last_score: float | None = None
    sniper_last_direction: int | None = None


class PositionResponse(BaseModel):
    ticket: int
    symbol: str
    position_type: str
    volume: float
    open_price: float
    current_sl: float | None
    current_tp: float | None
    open_time: datetime
    current_profit: float
    rapid_mode: bool
    breakeven_reached: bool
    current_step: int
    entry_source: str | None

    class Config:
        from_attributes = True


class TradeLogResponse(BaseModel):
    id: UUID
    ticket: int
    symbol: str
    order_type: str | None
    entry_price: float | None
    sl_price: float | None
    tp_price: float | None
    lots: float | None
    profit: float | None
    commission: float | None
    swap: float | None
    entry_source: str | None
    grid_index: int
    created_at: datetime
    closed_at: datetime | None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: str
    display_name: str | None
    is_online: bool
    last_seen_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    role: UserRole


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    action: str | None
    details: dict | None
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class SniperSignalResponse(BaseModel):
    score: float
    direction: int
    momentum: float
    acceleration: float
    rsi_score: float
    vol_score: float
    confluence_score: float
    volume_score: float
    reason: str


class TickData(BaseModel):
    time: datetime
    bid: float
    ask: float
    volume: int = 0


class OHLCBar(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
