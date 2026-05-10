"""Add adaptive learning tables

Revision ID: 003
Revises: 002
Create Date: 2026-05-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_regime_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("regime", sa.String(30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("adx", sa.Float(), nullable=False),
        sa.Column("atr_ratio", sa.Float(), nullable=False),
        sa.Column("trend_direction", sa.Float(), nullable=False),
        sa.Column("triggers", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "sniper_learning_log",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("regime_detected", sa.String(30), nullable=False),
        sa.Column("total_trades", sa.Integer(), server_default="0"),
        sa.Column("winning_trades", sa.Integer(), server_default="0"),
        sa.Column("losing_trades", sa.Integer(), server_default="0"),
        sa.Column("win_rate", sa.Float(), server_default="0"),
        sa.Column("profit_factor", sa.Float(), server_default="0"),
        sa.Column("avg_profit_pips", sa.Float(), server_default="0"),
        sa.Column("avg_loss_pips", sa.Float(), server_default="0"),
        sa.Column("max_drawdown_pips", sa.Float(), server_default="0"),
        sa.Column("threshold_before", sa.Integer(), nullable=True),
        sa.Column("threshold_after", sa.Integer(), nullable=True),
        sa.Column("weights_snapshot", sa.Text(), nullable=True),
        sa.Column("safe_mode_triggered", sa.Boolean(), server_default="false"),
        sa.Column("circuit_breaker_triggered", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "date", name="uq_user_learning_date"),
    )


def downgrade() -> None:
    op.drop_table("sniper_learning_log")
    op.drop_table("market_regime_history")
