from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.clients.notion_client import get_notion_client
from app.core.config import get_settings
from app.errors import ServiceUnavailableError
from app.schemas.analysis import AnalysisResult
from app.schemas.webhook import MetaInfo, SubmissionInfo, WebhookPayload
from app.services.notion_service import save_to_notion


def _make_sample_payload_and_analysis() -> tuple[WebhookPayload, AnalysisResult]:
    payload = WebhookPayload(
        platform="baekjoon",
        meta_info=MetaInfo(
            title="Two Sum",
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
        approach="Use two pointers.",
        time_complexity="O(N)",
        improvement="Validate inputs.",
        next_problem="baekjoon 1253 Good",
        better_code="print('better code from AI')",
    )
    return payload, analysis


def test_get_notion_client_raises_when_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "")
    get_settings.cache_clear()

    with pytest.raises(ServiceUnavailableError):
        get_notion_client()


@pytest.mark.asyncio
async def test_save_to_notion_calls_pages_create(monkeypatch: pytest.MonkeyPatch) -> None:
    payload, analysis = _make_sample_payload_and_analysis()

    monkeypatch.setenv("NOTION_TOKEN", "dummy-token")
    monkeypatch.setenv("NOTION_DATABASE_ID", "dummy-db-id")
    get_settings.cache_clear()

    fake_client = MagicMock()
    fake_client.pages.create = AsyncMock()

    monkeypatch.setattr(
        "app.services.notion_service.get_notion_client",
        lambda _token: fake_client,
    )

    await save_to_notion(payload, analysis)

    fake_client.pages.create.assert_awaited_once()
    kwargs: Dict[str, Any] = fake_client.pages.create.call_args.kwargs
    assert kwargs["parent"]["database_id"] == "dummy-db-id"
    assert "properties" in kwargs
    assert "children" in kwargs
