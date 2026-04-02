# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

# print(f"DEBUG: Looking for .env at {ENV_FILE}"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DB_URL: str | None = None

    # JWT
    JWT_SECRET: str | None = None
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- Google OAuth ---
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # --- LLM models and API configuration ---
    DEEPSEEK_API_KEY: str | None = None
    DEEPSEEK_BASE_URL: str | None = None

    OPENAI_API_KEY: str | None = None
    OPENAI_API_BASE: str | None = None

    ZHIPU_API_KEY: str | None = None
    ZHIPU_API_BASE: str | None = None

    ALIBABA_API_KEY: str | None = None
    ALIBABA_API_BASE: str | None = None

    LOCAL_BASE_URL: str | None = None

    # --- Embedding ---
    QWEN_EMB_KEY: str | None = None
    QWEN_EMB_BASE: str | None = None

    # --- LangSmith & SerpApi ---
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_ENDPOINT: str | None = None
    SERPAPI_KEY: str | None = None

settings = Settings()
