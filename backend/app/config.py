from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Resume Analyzer & JD Matcher"
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openrouter/auto", alias="OPENROUTER_MODEL")
    openrouter_timeout_seconds: float = Field(
        default=20.0,
        alias="OPENROUTER_TIMEOUT_SECONDS",
    )
    total_request_budget_seconds: float = Field(
        default=180.0,
        alias="TOTAL_REQUEST_BUDGET_SECONDS",
    )
    openrouter_max_retries: int = Field(default=0, alias="OPENROUTER_MAX_RETRIES")
    resume_max_tokens: int = Field(default=140, alias="RESUME_MAX_TOKENS")
    match_max_tokens: int = Field(default=220, alias="MATCH_MAX_TOKENS")
    max_resume_chars: int = Field(default=3500, alias="MAX_RESUME_CHARS")
    max_jd_chars: int = Field(default=2500, alias="MAX_JD_CHARS")
    good_fit_threshold: int = Field(default=80, alias="GOOD_FIT_THRESHOLD")
    moderate_fit_threshold: int = Field(default=60, alias="MODERATE_FIT_THRESHOLD")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
