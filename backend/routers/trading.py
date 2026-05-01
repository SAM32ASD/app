import logging
from fastapi import APIRouter, Depends, HTTPException
from middleware.auth import verify_token, require_role
from models.schemas import (
    TradingStatusResponse, TradingConfigSchema, TradingConfigUpdate,
    PositionResponse, TradeLogResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trading", tags=["Trading"])

_engine = None


def set_engine(engine):
    global _engine
    _engine = engine


def get_engine():
    if _engine is None:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    return _engine


@router.get("/status", response_model=TradingStatusResponse)
async def get_trading_status(user: dict = Depends(verify_token)):
    engine = get_engine()
    return engine.get_status()


@router.post("/start")
async def start_trading(user: dict = Depends(require_role("admin", "trader"))):
    engine = get_engine()
    await engine.start()
    return {"status": "started", "robot_status": engine.status.value}


@router.post("/stop")
async def stop_trading(user: dict = Depends(require_role("admin", "trader"))):
    engine = get_engine()
    await engine.stop()
    return {"status": "stopped", "robot_status": engine.status.value}


@router.post("/emergency-stop")
async def emergency_stop(user: dict = Depends(require_role("admin"))):
    engine = get_engine()
    await engine.emergency_stop()
    logger.warning(f"Emergency stop triggered by {user.get('email', 'unknown')}")
    return {"status": "emergency", "robot_status": engine.status.value}


@router.get("/config")
async def get_config(user: dict = Depends(verify_token)):
    engine = get_engine()
    return engine.config


@router.put("/config")
async def update_config(
    update: TradingConfigUpdate,
    user: dict = Depends(require_role("admin")),
):
    engine = get_engine()
    changes = update.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No changes provided")
    engine.update_config(changes)
    return {"status": "updated", "changes": changes}


@router.get("/positions")
async def get_positions(user: dict = Depends(verify_token)):
    engine = get_engine()
    return {
        "positions": engine._open_positions,
        "buy_count": engine._buy_positions,
        "sell_count": engine._sell_positions,
    }


@router.get("/history")
async def get_trade_history(
    page: int = 1, per_page: int = 50,
    user: dict = Depends(verify_token),
):
    return {"trades": [], "page": page, "per_page": per_page, "total": 0}
