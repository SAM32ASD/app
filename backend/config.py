from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "XAUUSD Trading Backend v9.7"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://trader:changeme@localhost:5432/trading_db"
    redis_url: str = "redis://localhost:6379"

    firebase_project_id: str = ""
    firebase_credentials_path: str = ""

    metaapi_token: str = ""
    metaapi_account_id: str = ""

    magic_number: int = 298347
    symbol: str = "XAUUSD"

    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    jwt_refresh_secret: str = "dev-refresh-secret-change-in-production"
    jwt_refresh_expire_days: int = 7

    encryption_key: str = ""

    cors_origins: list[str] = ["*"]

    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
