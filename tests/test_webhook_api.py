from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.errors import BadRequestError, ServiceUnavailableError, TooManyRequestsError
from app.schemas.analysis import AnalysisResult


def _build_valid_payload() -> dict:
    return {
        "platform": "baekjoon",
        "meta_info": {
            "title": "Two Sum",
            "problem_id": "3273",
            "link": "https://www.acmicpc.net/problem/3273",
            "level": "silver",
            "language": "python",
        },
        "submission_info": {
            "code": "import sys\nprint('hello world')",
            "memory": 12345,
            "time": 120,
        },
    }


@patch("app.services.ai_service.create_structured_analysis", new_callable=AsyncMock)
def test_webhook_success_returns_analysis_result(
    mock_create_structured_analysis: AsyncMock,
    client: TestClient,
) -> None:
    dummy_result = AnalysisResult(
        approach="Use two pointers on a sorted array.",
        time_complexity="O(N)",
        improvement="Handle edge cases explicitly.",
        next_problem="baekjoon 1253 Good",
        better_code="print('better code')",
    )
    mock_create_structured_analysis.return_value = dummy_result

    with patch("app.api.routes.webhook.save_to_notion", new=AsyncMock()):
        response = client.post("/webhook", json=_build_valid_payload())

    assert response.status_code == 200
    parsed = AnalysisResult(**response.json())
    assert parsed.approach == dummy_result.approach
    assert parsed.time_complexity == dummy_result.time_complexity
    assert parsed.improvement == dummy_result.improvement
    assert parsed.next_problem == dummy_result.next_problem
    assert parsed.better_code == dummy_result.better_code


def test_webhook_invalid_payload_returns_422(client: TestClient) -> None:
    invalid_payload = {
        "meta_info": {
            "title": "Two Sum",
            "problem_id": "3273",
            "language": "python",
        },
        "submission_info": {
            "code": "print('hi')",
        },
    }

    response = client.post("/webhook", json=invalid_payload)

    assert response.status_code == 422


@patch("app.api.routes.webhook.analyze_submission", new_callable=AsyncMock)
def test_webhook_openai_config_error_returns_503(
    mock_analyze_submission: AsyncMock,
    client: TestClient,
) -> None:
    mock_analyze_submission.side_effect = ServiceUnavailableError(
        "OPENAI_API_KEY is not set in environment"
    )

    response = client.post("/webhook", json=_build_valid_payload())

    assert response.status_code == 503
    assert response.json()["detail"] == "OPENAI_API_KEY is not set in environment"


@patch("app.api.routes.webhook.analyze_submission", new_callable=AsyncMock)
def test_webhook_notion_request_error_returns_400(
    mock_analyze_submission: AsyncMock,
    client: TestClient,
) -> None:
    mock_analyze_submission.return_value = AnalysisResult(
        approach="Use two pointers on a sorted array.",
        time_complexity="O(N)",
        improvement="Handle edge cases explicitly.",
        next_problem="baekjoon 1253 Good",
        better_code="print('better code')",
    )

    with patch(
        "app.api.routes.webhook.save_to_notion",
        new=AsyncMock(side_effect=BadRequestError("notion_settings.database_id is required")),
    ):
        payload = _build_valid_payload()
        payload["notion_settings"] = {"token": "secret", "database_id": ""}
        response = client.post("/webhook", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "notion_settings.database_id is required"


@patch("app.api.routes.webhook.analyze_submission", new_callable=AsyncMock)
def test_webhook_notion_rate_limit_returns_429(
    mock_analyze_submission: AsyncMock,
    client: TestClient,
) -> None:
    mock_analyze_submission.return_value = AnalysisResult(
        approach="Use two pointers on a sorted array.",
        time_complexity="O(N)",
        improvement="Handle edge cases explicitly.",
        next_problem="baekjoon 1253 Good",
        better_code="print('better code')",
    )

    with patch(
        "app.api.routes.webhook.save_to_notion",
        new=AsyncMock(side_effect=TooManyRequestsError("Notion API rate limit exceeded")),
    ):
        response = client.post("/webhook", json=_build_valid_payload())

    assert response.status_code == 429
    assert response.json()["detail"] == "Notion API rate limit exceeded"
