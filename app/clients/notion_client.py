from notion_client import AsyncClient

from app.core.config import get_settings
from app.errors import ServiceUnavailableError


def get_notion_client(token: str | None = None) -> AsyncClient:
    settings = get_settings()
    notion_token = token or settings.notion_token
    if not notion_token:
        raise ServiceUnavailableError(
            "NOTION_TOKEN is not set in environment and no per-request token was provided"
        )

    return AsyncClient(auth=notion_token)
