from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.max_daily_loss_percent: float = cfg.get("max_daily_loss_percent", 3.0)
        self.max_consecutive_losses: int = cfg.get("max_consecutive_losses", 8)
        self.max_trades_per_day: int = cfg.get("max_trades_per_day", 500)
        self.trade_cooldown_seconds: int = cfg.get("trade_cooldown_minutes", 1) * 60

        self.daily_start_balance: float = 0.0
        self.current_balance: float = 0.0
        self.today_realized_pl: float = 0.0
        self.consecutive_losses: int = 0
        self.trades_today: int = 0
        self.last_trade_time: float = 0.0
        self._last_trading_day: str = ""

    def check_daily_reset(self, account_balance: float):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._last_trading_day != today:
            self._last_trading_day = today
            self.daily_start_balance = account_balance
            self.consecutive_losses = 0
            self.trades_today = 0
            self.today_realized_pl = 0.0
            self.current_balance = account_balance
            logger.info(
                f"Daily reset - Balance: ${account_balance:.2f}"
            )

    def update_balance(self):
        self.current_balance = self.daily_start_balance + self.today_realized_pl
        if self.current_balance < 0:
            self.current_balance = max(self.current_balance, 10.0)

    def get_balance_for_risk(self, account_balance: float) -> float:
        return self.current_balance if self.current_balance > 0 else account_balance

    def record_trade_open(self):
        self.trades_today += 1
        self.last_trade_time = datetime.now(timezone.utc).timestamp()

    def record_trade_close(self, profit: float):
        self.today_realized_pl += profit
        self.update_balance()
        if profit < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

    def check_daily_loss_limit(self, current_equity: float) -> bool:
        if self.daily_start_balance <= 0:
            return True
        daily_loss = self.daily_start_balance - current_equity
        limit = self.daily_start_balance * self.max_daily_loss_percent / 100.0
        if daily_loss >= limit:
            logger.warning(
                f"DAILY LOSS LIMIT REACHED: ${daily_loss:.2f} "
                f"({daily_loss / self.daily_start_balance * 100:.1f}%)"
            )
            return False
        return True

    def check_consecutive_losses(self) -> bool:
        if self.consecutive_losses >= self.max_consecutive_losses:
            logger.warning(f"Max consecutive losses reached: {self.consecutive_losses}")
            return False
        return True

    def check_max_trades(self) -> bool:
        if self.trades_today >= self.max_trades_per_day:
            logger.warning(f"Max trades per day reached: {self.trades_today}")
            return False
        return True

    def check_cooldown(self) -> bool:
        if self.last_trade_time == 0:
            return True
        now = datetime.now(timezone.utc).timestamp()
        elapsed = now - self.last_trade_time
        return elapsed >= self.trade_cooldown_seconds

    def can_trade(self, current_equity: float) -> tuple[bool, str]:
        if not self.check_daily_loss_limit(current_equity):
            return False, "daily_loss_limit"
        if not self.check_consecutive_losses():
            return False, "consecutive_losses"
        if not self.check_max_trades():
            return False, "max_trades"
        if not self.check_cooldown():
            return False, "cooldown"
        return True, "ok"

    def reset(self):
        self.consecutive_losses = 0
        self.trades_today = 0
        self.today_realized_pl = 0.0
        self.last_trade_time = 0.0
