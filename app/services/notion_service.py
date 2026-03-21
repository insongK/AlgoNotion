from logging import getLogger
from typing import Any, Dict, List

from notion_client.errors import APIResponseError

from app.clients.notion_client import get_notion_client
from app.core.config import get_settings
from app.errors import AppError, BadGatewayError, BadRequestError, ServiceUnavailableError, TooManyRequestsError
from app.schemas.analysis import AnalysisResult
from app.schemas.webhook import WebhookPayload


logger = getLogger(__name__)
NOTION_RICH_TEXT_LIMIT = 2000


def _resolve_notion_credentials(payload: WebhookPayload) -> tuple[str, str]:
    settings = get_settings()
    request_settings = payload.notion_settings

    if request_settings is not None:
        if not request_settings.token:
            raise BadRequestError("notion_settings.token is required")
        if not request_settings.database_id:
            raise BadRequestError("notion_settings.database_id is required")
        return request_settings.token, request_settings.database_id

    if not settings.notion_token:
        raise ServiceUnavailableError("NOTION_TOKEN is not set in environment")
    if not settings.notion_database_id:
        raise ServiceUnavailableError("NOTION_DATABASE_ID is not set in environment")

    return settings.notion_token, settings.notion_database_id


def _chunk_text(text: str, chunk_size: int = NOTION_RICH_TEXT_LIMIT) -> List[str]:
    if not text:
        return [""]
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


def _build_code_blocks(code: str, language: str) -> List[Dict[str, Any]]:
    return [
        {
            "object": "block",
            "type": "code",
            "code": {
                "language": language,
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": chunk},
                    }
                ],
            },
        }
        for chunk in _chunk_text(code)
    ]


def _build_properties(payload: WebhookPayload) -> Dict[str, Any]:
    meta = payload.meta_info
    sub = payload.submission_info

    title = f"[{meta.problem_id}] {meta.title}"
    performance_text = f"{sub.time}ms / {sub.memory}KB"

    return {
        "Name": {
            "title": [
                {
                    "type": "text",
                    "text": {"content": title},
                }
            ]
        },
        "Platform": {
            "select": {"name": payload.platform},
        },
        "Language": {
            "select": {"name": meta.language},
        },
        "Performance": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": performance_text},
                }
            ]
        },
    }


def _build_children(payload: WebhookPayload, analysis: AnalysisResult) -> List[Dict[str, Any]]:
    meta = payload.meta_info
    sub = payload.submission_info

    children = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "AI Code Review"},
                    }
                ]
            },
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"Approach: {analysis.approach}"},
                    }
                ]
            },
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"Time Complexity: {analysis.time_complexity}"},
                    }
                ]
            },
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"Improvement: {analysis.improvement}"},
                    }
                ]
            },
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"Next Problem: {analysis.next_problem}"},
                    }
                ]
            },
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Submitted Code and Better Version"},
                    }
                ]
            },
        },
    ]

    children.extend(_build_code_blocks(sub.code, meta.language))
    children.extend(_build_code_blocks(analysis.better_code, meta.language))
    return children


async def save_to_notion(payload: WebhookPayload, analysis: AnalysisResult) -> None:
    notion_token, notion_database_id = _resolve_notion_credentials(payload)

    client = get_notion_client(notion_token)
    properties = _build_properties(payload)
    children = _build_children(payload, analysis)

    try:
        await client.pages.create(
            parent={"database_id": notion_database_id},
            properties=properties,
            children=children,
        )
    except APIResponseError as e:
        logger.exception(
            "Notion page create failed. status=%s, code=%s, message=%s",
            e.status,
            getattr(e, "code", None),
            e.message,
        )
        if e.status == 429:
            raise TooManyRequestsError(f"Notion API rate limit exceeded: {e.message}") from e
        if 400 <= e.status < 500:
            raise AppError(e.status, f"Notion API error: {e.message}") from e
        raise BadGatewayError(f"Notion API error: {e.message}") from e
    except AppError:
        raise
    except Exception as e:
        logger.exception("Unexpected error while creating Notion page.")
        raise BadGatewayError("Unexpected error while saving to Notion") from e
