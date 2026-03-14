from notion_client import AsyncClient

from app.core.config import get_settings


def get_notion_client(token: str | None = None) -> AsyncClient:
    """
    요청별 토큰이 있으면 우선 사용하고, 없으면 환경변수 NOTION_TOKEN을 사용한다.
    """
    settings = get_settings()
    notion_token = token or settings.notion_token
    if not notion_token:
        raise ValueError("NOTION_TOKEN is not set in environment and no per-request token was provided")

    return AsyncClient(auth=notion_token)
