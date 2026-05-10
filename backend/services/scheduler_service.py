import logging
import json
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from services.redis_service import get_redis

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

_engine_manager = None


def set_engine_manager(manager):
    global _engine_manager
    _engine_manager = manager


async def _daily_learning_analysis():
    if not _engine_manager:
        return

    logger.info("[Scheduler] Running daily learning analysis for all active engines")

    for user_id, user_engine in _engine_manager.engines.items():
        try:
            engine = user_engine.engine
            if not hasattr(engine, "adaptive"):
                continue

            adaptive = engine.adaptive
            regime_classifier = engine.regime_classifier

            adaptive.check_safe_mode_expiry()
            adaptive.apply_feedback_decay()

            trades_today = await _get_user_trades_today(user_id)
            current_regime = regime_classifier.current_regime.regime.value

            threshold_before = adaptive.state.current_threshold
            adaptive.daily_analysis(trades_today, current_regime, engine._account_balance)
            threshold_after = adaptive.state.current_threshold

            await _persist_adaptive_state(user_id, adaptive)
            await _log_learning_entry(
                user_id, current_regime, trades_today,
                threshold_before, threshold_after, adaptive
            )

            logger.info(
                f"[Scheduler] User {user_id}: daily analysis done "
                f"(regime={current_regime}, threshold={threshold_after})"
            )
        except Exception as e:
            logger.error(f"[Scheduler] Daily analysis error for user {user_id}: {e}", exc_info=True)


async def _get_user_trades_today(user_id: str) -> list[dict]:
    r = await get_redis()
    key = f"user:{user_id}:trades_today"
    data = await r.get(key)
    if data:
        return json.loads(data)
    return []


async def _persist_adaptive_state(user_id: str, adaptive):
    r = await get_redis()
    key = f"user:{user_id}:adaptive_state"
    await r.set(key, json.dumps(adaptive.to_dict()))


async def _load_adaptive_state(user_id: str) -> dict | None:
    r = await get_redis()
    key = f"user:{user_id}:adaptive_state"
    data = await r.get(key)
    if data:
        return json.loads(data)
    return None


async def _log_learning_entry(
    user_id: str, regime: str, trades: list[dict],
    threshold_before: int, threshold_after: int, adaptive
):
    r = await get_redis()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = {
        "user_id": user_id,
        "date": today,
        "regime_detected": regime,
        "total_trades": len(trades),
        "winning_trades": sum(1 for t in trades if t.get("profit", 0) > 0),
        "losing_trades": sum(1 for t in trades if t.get("profit", 0) <= 0),
        "threshold_before": threshold_before,
        "threshold_after": threshold_after,
        "weights_snapshot": json.dumps(adaptive.state.current_weights),
        "safe_mode_triggered": adaptive.state.safe_mode,
        "circuit_breaker_triggered": adaptive.state.circuit_breaker_active,
    }
    key = f"user:{user_id}:learning_log:{today}"
    await r.set(key, json.dumps(entry), ex=86400 * 30)


async def record_closed_trade(user_id: str, trade: dict):
    r = await get_redis()
    key = f"user:{user_id}:trades_today"
    data = await r.get(key)
    trades = json.loads(data) if data else []
    trades.append(trade)
    await r.set(key, json.dumps(trades), ex=86400)


async def reset_daily_trades():
    if not _engine_manager:
        return
    r = await get_redis()
    for user_id in _engine_manager.engines:
        key = f"user:{user_id}:trades_today"
        await r.delete(key)
    logger.info("[Scheduler] Daily trades reset for all users")


def start_scheduler():
    scheduler.add_job(
        _daily_learning_analysis,
        CronTrigger(hour=0, minute=0, timezone="UTC"),
        id="daily_learning_analysis",
        replace_existing=True,
    )

    scheduler.add_job(
        reset_daily_trades,
        CronTrigger(hour=0, minute=5, timezone="UTC"),
        id="reset_daily_trades",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("[Scheduler] APScheduler started (daily analysis @ 00:00 UTC, reset @ 00:05 UTC)")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] APScheduler stopped")
