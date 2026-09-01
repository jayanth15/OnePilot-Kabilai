from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Kabilai API"
    app_version: str = "0.1.0"
    environment: Literal["local", "development", "staging", "production", "test"] = "local"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Database: prod_db=True uses DATABASE_URL (Postgres). False uses SQLite.
    prod_db: bool = False
    database_url: str = ""

    jwt_secret: str = "change-me-in-production-change-me-in-production!!"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    agent_model: str = "test"

    gupshup_api_key: str = ""
    gupshup_app_name: str = ""
    gupshup_source_number: str = ""
    gupshup_mock: bool = True
    gupshup_timeout_seconds: float = 15.0

    session_idle_minutes: int = 15
    session_max_history: int = 40
    session_sweep_seconds: int = 30
    chat_retention_days: int = 30

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
