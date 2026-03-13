from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.notion_client import get_notion_client
from app.core.config import Settings
from app.schemas.analysis import AnalysisResult
from app.schemas.webhook import MetaInfo, SubmissionInfo, WebhookPayload
from app.services.notion_service import save_to_notion


def _make_sample_payload_and_analysis() -> tuple[WebhookPayload, AnalysisResult]:
    payload = WebhookPayload(
        platform="baekjoon",
        meta_info=MetaInfo(
            title="두 수의 합",
            problem_id="3273",
            link="https://www.acmicpc.net/problem/3273",
            level="silver",
            language="python",
        ),
        submission_info=SubmissionInfo(
            code="nums = [1, 2, 3]\nprint(sum(nums))",
            memory=12345,
            time=120,
        ),
    )
    analysis = AnalysisResult(
        approach="투 포인터를 사용해 선형 시간에 해결했습니다.",
        time_complexity="O(N)",
        improvement="입력 검증과 엣지 케이스 처리 로직을 보완할 수 있습니다.",
        next_problem="baekjoon 1253 좋다",
        better_code="print('better code from AI')",
    )
    return payload, analysis


def test_get_notion_client_raises_when_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    NOTION_TOKEN이 설정되지 않은 경우 get_notion_client가 ValueError를 발생시키는지 확인.
    """
    from app import core  # type: ignore
    from app.core import config

    def _fake_settings() -> Settings:
        return Settings(
            openai_api_key="dummy",
            openai_model="gpt-4o-mini",
            notion_token=None,
            notion_database_id=None,
        )

    monkeypatch.setattr(config, "get_settings", _fake_settings)

    with pytest.raises(ValueError):
        get_notion_client()


@pytest.mark.asyncio
async def test_save_to_notion_calls_pages_create(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    NOTION_DATABASE_ID와 NOTION_TOKEN이 설정된 경우,
    save_to_notion이 Notion AsyncClient의 pages.create를 한 번 호출하는지 확인.
    실제 네트워크 호출은 mock 처리한다.
    """
    from app.services import notion_service

    payload, analysis = _make_sample_payload_and_analysis()

    # 설정 mock
    def _fake_settings() -> Settings:
        return Settings(
            openai_api_key="dummy",
            openai_model="gpt-4o-mini",
            notion_token="dummy-token",
            notion_database_id="dummy-db-id",
        )

    monkeypatch.setattr(notion_service, "get_settings", _fake_settings)

    # 클라이언트 및 pages.create mock
    fake_client = MagicMock()
    fake_client.pages.create = AsyncMock()

    monkeypatch.setattr(notion_service, "get_notion_client", lambda: fake_client)

    await save_to_notion(payload, analysis)

    fake_client.pages.create.assert_awaited_once()
    kwargs: Dict[str, Any] = fake_client.pages.create.call_args.kwargs
    assert kwargs["parent"]["database_id"] == "dummy-db-id"
    assert "properties" in kwargs
    assert "children" in kwargs

