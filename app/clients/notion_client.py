from notion_client import AsyncClient

from app.core.config import get_settings


def get_notion_client() -> AsyncClient:
    """
    NOTION_TOKEN을 사용해 AsyncClient를 초기화하는 래퍼.
    """
    settings = get_settings()
    if not settings.notion_token:
        raise ValueError("NOTION_TOKEN is not set in environment")

    return AsyncClient(auth=settings.notion_token)

