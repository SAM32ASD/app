"""Initial schema - users, refresh_tokens, trading_configs, trade_logs, active_positions, audit_logs

Revision ID: 001
Revises: None
Create Date: 2026-05-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("firebase_uid", sa.String(128), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("role", sa.String(50), server_default="viewer"),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("is_online", sa.Boolean(), server_default="false"),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "trading_configs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False, unique=True, index=True),
        sa.Column("risk_percent", sa.Float(), server_default="1.0"),
        sa.Column("max_daily_loss_percent", sa.Float(), server_default="5.0"),
        sa.Column("max_consecutive_losses", sa.Integer(), server_default="5"),
        sa.Column("max_trades_per_day", sa.Integer(), server_default="20"),
        sa.Column("sl_method", sa.String(50), server_default="hybrid"),
        sa.Column("sl_min", sa.Float(), server_default="30.0"),
        sa.Column("sl_max", sa.Float(), server_default="180.0"),
        sa.Column("sniper_enabled", sa.Boolean(), server_default="true"),
        sa.Column("sniper_min_score", sa.Integer(), server_default="57"),
        sa.Column("micro_timeframes_enabled", sa.Boolean(), server_default="true"),
        sa.Column("max_positions_per_direction", sa.Integer(), server_default="3"),
        sa.Column("max_positions_total", sa.Integer(), server_default="6"),
        sa.Column("hedging_enabled", sa.Boolean(), server_default="false"),
        sa.Column("scheduled_start_time", sa.String(5), nullable=True),
        sa.Column("scheduled_stop_time", sa.String(5), nullable=True),
        sa.Column("trailing_level_1_multiplier", sa.Float(), server_default="1.5"),
        sa.Column("trailing_level_2_multiplier", sa.Float(), server_default="3.0"),
        sa.Column("trailing_level_3_multiplier", sa.Float(), server_default="5.0"),
        sa.Column("rapid_mode_atr_multiplier", sa.Float(), server_default="0.3"),
        sa.Column("time_based_be_minutes", sa.Integer(), server_default="10"),
        sa.Column("time_based_be_profit_threshold", sa.Float(), server_default="0.5"),
        sa.Column("weak_signal_lot_reduction", sa.Float(), server_default="0.7"),
        sa.Column("weak_signal_spread_threshold", sa.Float(), server_default="0.8"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "trade_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("ticket", sa.BigInteger(), nullable=False),
        sa.Column("symbol", sa.String(20), server_default="XAUUSD"),
        sa.Column("trade_type", sa.String(10), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("sl", sa.Float(), nullable=True),
        sa.Column("tp", sa.Float(), nullable=True),
        sa.Column("lots", sa.Float(), nullable=False),
        sa.Column("profit", sa.Float(), nullable=True),
        sa.Column("commission", sa.Float(), server_default="0"),
        sa.Column("swap", sa.Float(), server_default="0"),
        sa.Column("entry_source", sa.String(50), nullable=True),
        sa.Column("sniper_score", sa.Integer(), nullable=True),
        sa.Column("sl_method", sa.String(50), nullable=True),
        sa.Column("sl_distance_pips", sa.Float(), nullable=True),
        sa.Column("grid_index", sa.Integer(), server_default="0"),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "active_positions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("ticket", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("symbol", sa.String(20), server_default="XAUUSD"),
        sa.Column("trade_type", sa.String(10), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("current_sl", sa.Float(), nullable=True),
        sa.Column("current_tp", sa.Float(), nullable=True),
        sa.Column("profit", sa.Float(), server_default="0"),
        sa.Column("grid_index", sa.Integer(), server_default="0"),
        sa.Column("trailing_step", sa.Integer(), server_default="0"),
        sa.Column("rapid_mode", sa.Boolean(), server_default="false"),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("active_positions")
    op.drop_table("trade_logs")
    op.drop_table("trading_configs")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
