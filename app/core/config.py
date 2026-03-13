from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL_NAME")
    notion_token: str | None = Field(default=None, validation_alias="NOTION_TOKEN")
    notion_database_id: str | None = Field(default=None, validation_alias="NOTION_DATABASE_ID")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

