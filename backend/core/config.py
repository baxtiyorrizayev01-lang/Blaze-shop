"""
Blaze CS2 Marketplace — Production Config
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "Blaze CS2 Marketplace"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALLOWED_ORIGINS: List[str] = ["*"]

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    # e.g. postgresql+asyncpg://user:pass@host:5432/blaze
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_ECHO: bool = False

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # ── JWT ──────────────────────────────────────────────
    JWT_SECRET: str = Field(..., env="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # ── Telegram ─────────────────────────────────────────
    BOT_TOKEN: str = Field(..., env="BOT_TOKEN")
    BOT_USERNAME: str = Field(..., env="BOT_USERNAME")
    ADMIN_IDS: str = Field(default="", env="ADMIN_IDS")
    WEBAPP_URL: str = Field(..., env="WEBAPP_URL")
    CHANNEL_ID: str = Field(default="", env="CHANNEL_ID")
    CHANNEL_USERNAME: str = Field(default="", env="CHANNEL_USERNAME")

    @property
    def admin_id_list(self) -> List[int]:
        return [int(x) for x in self.ADMIN_IDS.split(",") if x.strip()]

    # ── Payme ────────────────────────────────────────────
    PAYME_MERCHANT_ID: str = Field(default="", env="PAYME_MERCHANT_ID")
    PAYME_SECRET_KEY: str = Field(default="", env="PAYME_SECRET_KEY")
    PAYME_TEST_KEY: str = Field(default="", env="PAYME_TEST_KEY")
    PAYME_URL: str = "https://checkout.paycom.uz"
    PAYME_API_URL: str = "https://checkout.paycom.uz/api"
    PAYME_TEST_MODE: bool = True

    # ── Click ────────────────────────────────────────────
    CLICK_MERCHANT_ID: str = Field(default="", env="CLICK_MERCHANT_ID")
    CLICK_SERVICE_ID: str = Field(default="", env="CLICK_SERVICE_ID")
    CLICK_SECRET_KEY: str = Field(default="", env="CLICK_SECRET_KEY")
    CLICK_MERCHANT_USER_ID: str = Field(default="", env="CLICK_MERCHANT_USER_ID")

    # ── Uzum Bank ────────────────────────────────────────
    UZUM_MERCHANT_ID: str = Field(default="", env="UZUM_MERCHANT_ID")
    UZUM_SECRET_KEY: str = Field(default="", env="UZUM_SECRET_KEY")
    UZUM_API_URL: str = "https://api.uzumbank.uz/open-api"

    # ── UzCard/Humo ──────────────────────────────────────
    UZCARD_MERCHANT_ID: str = Field(default="", env="UZCARD_MERCHANT_ID")
    UZCARD_TERMINAL_ID: str = Field(default="", env="UZCARD_TERMINAL_ID")
    UZCARD_SECRET: str = Field(default="", env="UZCARD_SECRET")

    # ── Steam ────────────────────────────────────────────
    STEAM_API_KEY: str = Field(default="", env="STEAM_API_KEY")
    STEAM_REALM: str = Field(default="", env="STEAM_REALM")   # https://yourdomain.com
    STEAM_RETURN_URL: str = Field(default="", env="STEAM_RETURN_URL")  # /auth/steam/callback

    # ── CS2 Market APIs ──────────────────────────────────
    CSFLOAT_API_KEY: str = Field(default="", env="CSFLOAT_API_KEY")
    SKINPORT_API_KEY: str = Field(default="", env="SKINPORT_API_KEY")
    SKINPORT_SECRET: str = Field(default="", env="SKINPORT_SECRET")
    STEAM_MARKET_RATE_LIMIT: int = 5  # requests per second

    # ── Rate Limiting ────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 20

    # ── Referral System ──────────────────────────────────
    REFERRAL_BONUS: int = 5_000        # som
    REFERRAL_PURCHASER_BONUS: int = 0  # bonus for new referral on first purchase
    DAILY_BONUS_AMOUNT: int = 2_000    # som

    # ── Business ─────────────────────────────────────────
    MIN_DEPOSIT: int = 10_000          # som
    MAX_DEPOSIT: int = 50_000_000      # som
    PLATFORM_FEE_PERCENT: float = 2.5  # % on sales

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
