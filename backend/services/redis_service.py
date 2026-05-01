import json
import redis.asyncio as redis
from config import get_settings

settings = get_settings()

_pool: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.from_url(settings.redis_url, decode_responses=True)
    return _pool


async def close_redis():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def set_robot_status(status: str):
    r = await get_redis()
    await r.set("robot:status", status)


async def get_robot_status() -> str:
    r = await get_redis()
    return await r.get("robot:status") or "STOPPED"


async def set_last_tick(tick: dict):
    r = await get_redis()
    await r.set("market:xauusd:last_tick", json.dumps(tick))


async def get_last_tick() -> dict | None:
    r = await get_redis()
    data = await r.get("market:xauusd:last_tick")
    return json.loads(data) if data else None


async def set_volatility(value: float):
    r = await get_redis()
    await r.set("market:volatility:current", str(value))


async def get_volatility() -> float:
    r = await get_redis()
    val = await r.get("market:volatility:current")
    return float(val) if val else 0.0


async def increment_trades_count() -> int:
    r = await get_redis()
    return await r.incr("session:today:trades_count")


async def get_trades_count() -> int:
    r = await get_redis()
    val = await r.get("session:today:trades_count")
    return int(val) if val else 0


async def set_realized_pl(value: float):
    r = await get_redis()
    await r.set("session:today:realized_pl", str(value))


async def get_realized_pl() -> float:
    r = await get_redis()
    val = await r.get("session:today:realized_pl")
    return float(val) if val else 0.0


async def reset_daily_counters():
    r = await get_redis()
    await r.set("session:today:trades_count", "0")
    await r.set("session:today:consecutive_losses", "0")
    await r.set("session:today:realized_pl", "0")
