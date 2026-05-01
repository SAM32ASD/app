import uuid
from datetime import datetime, time
from sqlalchemy import String, Boolean, DateTime, Integer, Numeric, ForeignKey, JSON, Time
from sqlalchemy.orm import Mapped, mapped_column
from models.database import Base


class TradingConfig(Base):
    __tablename__ = "trading_configs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    risk_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0.5)
    max_daily_loss_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=3.0)
    max_consecutive_losses: Mapped[int] = mapped_column(Integer, default=8)
    max_trades_per_day: Mapped[int] = mapped_column(Integer, default=500)
    sl_method: Mapped[str] = mapped_column(String(50), default="hybrid")
    use_sniper_ai: Mapped[bool] = mapped_column(Boolean, default=True)
    sniper_min_score: Mapped[int] = mapped_column(Integer, default=70)
    use_micro_timeframes: Mapped[bool] = mapped_column(Boolean, default=True)
    max_positions_per_direction: Mapped[int] = mapped_column(Integer, default=1)
    max_total_positions: Mapped[int] = mapped_column(Integer, default=2)
    allow_hedging: Mapped[bool] = mapped_column(Boolean, default=False)
    trading_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    scheduled_start_time: Mapped[time | None] = mapped_column(Time)
    scheduled_stop_time: Mapped[time | None] = mapped_column(Time)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradeLog(Base):
    __tablename__ = "trade_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket: Mapped[int] = mapped_column(Integer, nullable=False)
    deal_id: Mapped[int | None] = mapped_column(Integer)
    symbol: Mapped[str] = mapped_column(String(20), default="XAUUSD")
    order_type: Mapped[str | None] = mapped_column(String(20))
    entry_price: Mapped[float | None] = mapped_column(Numeric(12, 5))
    sl_price: Mapped[float | None] = mapped_column(Numeric(12, 5))
    tp_price: Mapped[float | None] = mapped_column(Numeric(12, 5))
    lots: Mapped[float | None] = mapped_column(Numeric(10, 2))
    profit: Mapped[float | None] = mapped_column(Numeric(12, 2))
    commission: Mapped[float | None] = mapped_column(Numeric(12, 2))
    swap: Mapped[float | None] = mapped_column(Numeric(12, 2))
    entry_source: Mapped[str | None] = mapped_column(String(50))
    grid_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)


class ActivePosition(Base):
    __tablename__ = "active_positions"

    ticket: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str | None] = mapped_column(String(20))
    position_type: Mapped[str | None] = mapped_column(String(10))
    volume: Mapped[float | None] = mapped_column(Numeric(10, 2))
    open_price: Mapped[float | None] = mapped_column(Numeric(12, 5))
    current_sl: Mapped[float | None] = mapped_column(Numeric(12, 5))
    current_tp: Mapped[float | None] = mapped_column(Numeric(12, 5))
    open_time: Mapped[datetime | None] = mapped_column(DateTime)
    current_profit: Mapped[float | None] = mapped_column(Numeric(12, 2))
    rapid_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    breakeven_reached: Mapped[bool] = mapped_column(Boolean, default=False)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    entry_source: Mapped[str | None] = mapped_column(String(50))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
