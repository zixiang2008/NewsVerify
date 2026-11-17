from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_allowed_user_ids: str = Field(default="", alias="TELEGRAM_ALLOWED_USER_IDS")

    # LLM
    llm_base_url: str = Field(default="http://127.0.0.1:8000/v1", alias="LLM_BASE_URL")
    llm_base_url_fallback: str = Field(default="", alias="LLM_BASE_URL_FALLBACK")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="gemini-3-flash", alias="LLM_MODEL")
    llm_judge_model: str = Field(default="gemini-3-flash", alias="LLM_JUDGE_MODEL")
    llm_timeout_seconds: int = Field(default=60, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")

    def llm_endpoints(self) -> list[str]:
        """主 API 优先，备用 API 次之；去重后返回。"""
        urls = [self.llm_base_url, self.llm_base_url_fallback]
        out: list[str] = []
        for u in urls:
            u = (u or "").strip().rstrip("/")
            if u and u not in out:
                out.append(u)
        return out

    # Search
    search_provider: str = Field(default="duckduckgo", alias="SEARCH_PROVIDER")
    brave_search_api_key: str = Field(default="", alias="BRAVE_SEARCH_API_KEY")
    google_factcheck_api_key: str = Field(default="", alias="GOOGLE_FACTCHECK_API_KEY")
    searxng_base_url: str = Field(default="", alias="SEARXNG_BASE_URL")
    # Comma-separated public RSS/Atom feed URLs for compliant open-web discovery
    custom_feed_urls: str = Field(default="", alias="CUSTOM_FEED_URLS")

    # Budgets
    per_check_budget_usd: float = Field(default=0.10, alias="PER_CHECK_BUDGET_USD")
    monthly_budget_usd: float = Field(default=1.00, alias="MONTHLY_BUDGET_USD")
    max_claims_per_check: int = Field(default=8, alias="MAX_CLAIMS_PER_CHECK")
    max_search_results: int = Field(default=8, alias="MAX_SEARCH_RESULTS")
    worker_concurrency: int = Field(default=2, alias="WORKER_CONCURRENCY")

    # Database
    database_url: str = Field(default="postgresql+asyncpg://newsverify:newsverify@db:5432/newsverify", alias="DATABASE_URL")

    # Runtime
    app_mode: str = Field(default="bot", alias="APP_MODE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    tracking_default_interval_hours: int = Field(default=24, alias="TRACKING_DEFAULT_INTERVAL_HOURS")
    tracking_fast_interval_hours: int = Field(default=6, alias="TRACKING_FAST_INTERVAL_HOURS")
    tracking_weekly_interval_hours: int = Field(default=168, alias="TRACKING_WEEKLY_INTERVAL_HOURS")
    data_retention_days: int = Field(default=90, alias="DATA_RETENTION_DAYS")
    environment: str = Field(default="production", alias="ENVIRONMENT")
    api_key: str = Field(default="", alias="API_KEY")

    @field_validator("telegram_allowed_user_ids")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    def allowed_user_ids(self) -> List[int]:
        out: List[int] = []
        for part in self.telegram_allowed_user_ids.split(","):
            part = part.strip()
            if part:
                try:
                    out.append(int(part))
                except ValueError:
                    pass
        return out

    def validate_for_bot(self) -> List[str]:
        errors: List[str] = []
        if not self.telegram_bot_token:
            errors.append("TELEGRAM_BOT_TOKEN is empty")
        if not self.allowed_user_ids():
            errors.append("TELEGRAM_ALLOWED_USER_IDS is empty")
        if not self.llm_api_key:
            errors.append("LLM_API_KEY is empty")
        return errors


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()