import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.auth import verify_token, require_role
from models.database import get_db
from models.trading import TradeLog, AuditLog
from models.schemas import TradingConfigUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trading", tags=["Trading"])

_engine_manager = None


def set_engine_manager(manager):
    global _engine_manager
    _engine_manager = manager


def get_manager():
    if _engine_manager is None:
        raise HTTPException(status_code=503, detail="Engine manager not initialized")
    return _engine_manager


@router.get("/status")
async def get_trading_status(user: dict = Depends(verify_token)):
    user_id = user.get("sub") or user.get("uid")
    manager = get_manager()
    status = manager.get_status(user_id)
    return status


@router.post("/start")
async def start_trading(user: dict = Depends(require_role("admin", "trader"))):
    user_id = user.get("sub") or user.get("uid")
    manager = get_manager()

    ue = manager.get_user_engine(user_id)
    if not ue:
        raise HTTPException(status_code=400, detail="No MT5 account connected. Connect first.")
    if ue.connection_status != "CONNECTED":
        raise HTTPException(status_code=400, detail="MT5 account not connected")
    if ue.engine.status.value == "RUNNING":
        raise HTTPException(status_code=400, detail="Trading engine already running")

    success = await manager.start_trading(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start trading engine")

    return {"status": "started", "robot_status": "RUNNING"}


@router.post("/stop")
async def stop_trading(user: dict = Depends(require_role("admin", "trader"))):
    user_id = user.get("sub") or user.get("uid")
    manager = get_manager()

    success = await manager.stop_trading(user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Engine not running or not found")

    return {"status": "stopped", "robot_status": "STOPPED"}


@router.post("/emergency-stop")
async def emergency_stop(
    user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    user_id = user.get("sub") or user.get("uid")
    manager = get_manager()

    result = await manager.emergency_stop(user_id)

    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id) if user_id else None,
        action="EMERGENCY_STOP",
        details={"closed_positions": result.get("closed_positions", 0)},
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)

    logger.warning(f"Emergency stop triggered by {user.get('email', 'unknown')}")
    return {"status": "emergency", "robot_status": "EMERGENCY", "result": result}


@router.get("/config")
async def get_config(user: dict = Depends(verify_token)):
    user_id = user.get("sub") or user.get("uid")
    manager = get_manager()
    ue = manager.get_user_engine(user_id)
    if ue:
        return ue.engine.config
    return {}


@router.put("/config")
async def update_config(
    update: TradingConfigUpdate,
    user: dict = Depends(require_role("admin", "trader")),
):
    user_id = user.get("sub") or user.get("uid")
    manager = get_manager()

    changes = update.model_dump(exclude_none=True)
    if not changes:
        return {"status": "no_changes", "changes": {}}

    ue = manager.get_user_engine(user_id)
    if ue:
        ue.engine.update_config(changes)

    return {"status": "updated", "changes": changes}


@router.get("/positions")
async def get_positions(user: dict = Depends(verify_token)):
    user_id = user.get("sub") or user.get("uid")
    manager = get_manager()
    ue = manager.get_user_engine(user_id)
    if not ue:
        return {"positions": [], "buy_count": 0, "sell_count": 0}
    return {
        "positions": ue.engine._open_positions,
        "buy_count": ue.engine._buy_positions,
        "sell_count": ue.engine._sell_positions,
    }


@router.get("/history")
async def get_trade_history(
    page: int = 1,
    per_page: int = 50,
    user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    user_id = user.get("sub") or user.get("uid")

    total_result = await db.execute(
        select(func.count(TradeLog.id)).where(TradeLog.user_id == user_id)
    )
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        select(TradeLog)
        .where(TradeLog.user_id == user_id)
        .order_by(TradeLog.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    trades = result.scalars().all()

    return {
        "trades": [
            {
                "id": str(t.id),
                "ticket": t.ticket,
                "symbol": t.symbol,
                "order_type": t.order_type,
                "entry_price": float(t.entry_price) if t.entry_price else None,
                "sl_price": float(t.sl_price) if t.sl_price else None,
                "lots": float(t.lots) if t.lots else None,
                "profit": float(t.profit) if t.profit else None,
                "entry_source": t.entry_source,
                "grid_index": t.grid_index,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "closed_at": t.closed_at.isoformat() if t.closed_at else None,
            }
            for t in trades
        ],
        "page": page,
        "per_page": per_page,
        "total": total,
    }
