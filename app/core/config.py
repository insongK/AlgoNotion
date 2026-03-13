from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    notion_token: str | None = None
    notion_database_id: str | None = None

    class Config:
        env_prefix = ""
        env_file = ".env"
        fields = {
            "openai_api_key": {"env": "OPENAI_API_KEY"},
            "openai_model": {"env": "OPENAI_MODEL_NAME"},
            "notion_token": {"env": "NOTION_TOKEN"},
            "notion_database_id": {"env": "NOTION_DATABASE_ID"},
        }


@lru_cache()
def get_settings() -> Settings:
    return Settings()

