from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.schemas.analysis import AnalysisResult


def _build_valid_payload() -> dict:
    return {
        "platform": "baekjoon",
        "meta_info": {
            "title": "두 수의 합",
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
    """
    /webhook에 정상 JSON을 보내면 200 OK와 AnalysisResult 스펙 구조가 응답되는지 검증.
    OpenAI 호출은 mock 처리한다.
    """
    dummy_result = AnalysisResult(
        approach="두 포인터를 사용한 선형 탐색입니다.",
        time_complexity="O(N)",
        improvement="입출력 최적화와 예외 상황 처리 코드를 추가할 수 있습니다.",
        next_problem="baekjoon 1253 좋다",
        better_code="print('better code')",
    )
    mock_create_structured_analysis.return_value = dummy_result

    payload = _build_valid_payload()

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    body = response.json()

    # Pydantic으로 한번 더 검증
    parsed = AnalysisResult(**body)
    assert parsed.approach == dummy_result.approach
    assert parsed.time_complexity == dummy_result.time_complexity
    assert parsed.improvement == dummy_result.improvement
    assert parsed.next_problem == dummy_result.next_problem
    assert parsed.better_code == dummy_result.better_code


def test_webhook_invalid_payload_returns_422(client: TestClient) -> None:
    """
    필수 필드가 누락된 JSON을 보냈을 때 422 Unprocessable Entity가 나는지 검증.
    (예: platform 누락)
    """
    invalid_payload = {
        "meta_info": {
            "title": "두 수의 합",
            "problem_id": "3273",
            "language": "python",
        },
        "submission_info": {
            "code": "print('hi')",
        },
    }

    response = client.post("/webhook", json=invalid_payload)

    assert response.status_code == 422

