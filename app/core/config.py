from functools import lru_cache
import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_prefix = ""
        env_file = ".env"
        fields = {
            "openai_api_key": {"env": "OPENAI_API_KEY"},
            "openai_model": {"env": "OPENAI_MODEL_NAME"},
        }


@lru_cache()
def get_settings() -> Settings:
    return Settings()

