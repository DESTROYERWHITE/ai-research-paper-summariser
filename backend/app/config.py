from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "app" / "data"

load_dotenv(BACKEND_DIR / ".env")


class Settings(BaseSettings):
    app_name: str = "AI Research Paper Summariser"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    arxiv_base_url: str = "https://export.arxiv.org/api/query"
    frontend_origin: str = "http://localhost:5173"
    request_timeout_seconds: float = 25.0
    cache_ttl_hours: int = 24

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
