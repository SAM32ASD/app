import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from models.database import init_db
from services.redis_service import close_redis
from services.websocket_manager import ws_manager
from services.engine_manager import engine_manager
from services.scheduler_service import (
    start_scheduler, stop_scheduler,
    set_engine_manager as scheduler_set_manager,
)
from routers import trading, admin, auth, websocket
from routers.mt5 import router as mt5_router, set_engine_manager as mt5_set_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}")
    await init_db()
    trading.set_engine_manager(engine_manager)
    mt5_set_manager(engine_manager)
    scheduler_set_manager(engine_manager)
    start_scheduler()
    logger.info("Backend ready")
    yield
    logger.info("Shutting down...")
    stop_scheduler()
    await engine_manager.shutdown()
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    version="9.7.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(trading.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(mt5_router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "active_engines": len(engine_manager.engines),
        "ws_connections": ws_manager.connection_count,
    }


@app.get("/api/v1/market/indicators")
async def market_indicators(user_id: str | None = None):
    if user_id:
        ue = engine_manager.get_user_engine(user_id)
        if ue:
            engine = ue.engine
            return {
                "volatility": {
                    "current": engine.volatility.state.current_volatility,
                    "average": engine.volatility.state.average_volatility,
                    "normalized_atr": engine.volatility.state.normalized_atr,
                    "true_range": engine.volatility.state.true_range_volatility,
                    "status": engine.volatility.state.status,
                    "high_volatility_mode": engine.volatility.state.high_volatility_mode,
                    "risk_multiplier": engine.volatility.state.risk_multiplier,
                },
                "sniper_ai": {
                    "score": engine.sniper.last_signal.score,
                    "direction": engine.sniper.last_signal.direction,
                    "momentum": engine.sniper.last_signal.momentum,
                    "acceleration": engine.sniper.last_signal.acceleration,
                    "rsi_score": engine.sniper.last_signal.rsi_score,
                    "reason": engine.sniper.last_signal.reason,
                },
                "last_tick": {
                    "bid": engine._last_tick_bid,
                    "ask": engine._last_tick_ask,
                },
            }
    return {
        "volatility": {},
        "sniper_ai": {},
        "last_tick": {"bid": 0, "ask": 0},
    }
