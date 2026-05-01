import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from models.database import init_db
from services.redis_service import close_redis
from services.websocket_manager import ws_manager
from services.mt5_connector import MT5Connector
from core.trading_engine import TradingEngine
from routers import trading, admin, auth, websocket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

settings = get_settings()

connector = MT5Connector()
engine = TradingEngine(connector=connector)


async def engine_event_handler(event: str, data: dict):
    await ws_manager.broadcast(event, data)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}")
    await init_db()
    await connector.connect()
    engine.on_event(engine_event_handler)
    trading.set_engine(engine)
    logger.info("Backend ready")
    yield
    logger.info("Shutting down...")
    if engine.status.value == "RUNNING":
        await engine.stop()
    await connector.disconnect()
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
app.include_router(websocket.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "engine": engine.status.value,
        "connections": ws_manager.connection_count,
    }


@app.get("/api/v1/market/indicators")
async def market_indicators():
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
