from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    llm_provider: str = "mock"  # Use "mock" for demo, "ollama" for local LLM, "lm_studio" for LM Studio
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.2:latest"
    llm_api_key: str = "ollama"
    database_url: str = "log_analyses.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
