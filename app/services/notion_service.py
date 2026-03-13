from logging import getLogger
from typing import Any, Dict, List

from notion_client.errors import APIResponseError

from app.clients.notion_client import get_notion_client
from app.core.config import get_settings
from app.schemas.analysis import AnalysisResult
from app.schemas.webhook import WebhookPayload


logger = getLogger(__name__)


def _build_properties(payload: WebhookPayload, analysis: AnalysisResult) -> Dict[str, Any]:
    meta = payload.meta_info
    sub = payload.submission_info

    title = f"[{meta.problem_id}] {meta.title}"
    performance_text = f"{sub.time}ms / {sub.memory}KB"

    return {
        "이름": {
            "title": [
                {
                    "type": "text",
                    "text": {"content": title},
                }
            ]
        },
        "플랫폼": {
            "select": {"name": payload.platform},
        },
        "언어": {
            "select": {"name": meta.language},
        },
        "성능": {
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

    return [
        # 🤖 AI 코드 리뷰
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "🤖 AI 코드 리뷰"},
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
                        "text": {"content": f"접근: {analysis.approach}"},
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
                        "text": {"content": f"시간 복잡도: {analysis.time_complexity}"},
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
                        "text": {"content": f"개선점: {analysis.improvement}"},
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
                        "text": {"content": f"다음 추천 문제: {analysis.next_problem}"},
                    }
                ]
            },
        },
        # 💻 제출한 코드 및 모범 답안
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "💻 제출한 코드 및 모범 답안"},
                    }
                ]
            },
        },
        {
            "object": "block",
            "type": "code",
            "code": {
                "language": meta.language,
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": sub.code},
                    }
                ],
            },
        },
        {
            "object": "block",
            "type": "code",
            "code": {
                "language": meta.language,
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": analysis.better_code},
                    }
                ],
            },
        },
    ]


async def save_to_notion(payload: WebhookPayload, analysis: AnalysisResult) -> None:
    """
    WebhookPayload(원본 데이터)와 AnalysisResult(AI 분석 결과)를 기반으로
    Notion Database에 페이지를 생성한다.
    """
    settings = get_settings()
    if not settings.notion_database_id:
        logger.warning("NOTION_DATABASE_ID is not set; Notion 저장을 건너뜁니다.")
        return

    client = get_notion_client()

    properties = _build_properties(payload, analysis)
    children = _build_children(payload, analysis)

    try:
        await client.pages.create(
            parent={"database_id": settings.notion_database_id},
            properties=properties,
            children=children,
        )
    except APIResponseError as e:
        logger.exception(
            "Notion API 응답 오류로 페이지 생성에 실패했습니다. status=%s, code=%s, message=%s",
            e.status,
            getattr(e, "code", None),
            e.message,
        )
    except Exception as e:
        logger.exception("Notion 페이지 생성 중 예기치 못한 오류가 발생했습니다.")

