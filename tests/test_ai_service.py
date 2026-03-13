import pytest

from app.schemas.webhook import MetaInfo, SubmissionInfo, WebhookPayload
from app.schemas.analysis import AnalysisResult
from app.services.ai_service import analyze_submission, build_prompt


def _make_sample_payload() -> WebhookPayload:
    return WebhookPayload(
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


def test_build_prompt_returns_messages_and_contains_code() -> None:
    """
    build_prompt가 OpenAI Chat API 규격에 맞는 messages 배열을 반환하고,
    유저 메시지에 제출 코드가 포함되어 있는지 확인한다.
    """
    payload = _make_sample_payload()

    messages = build_prompt(payload)

    assert isinstance(messages, list)
    assert len(messages) == 2

    system_msg = messages[0]
    user_msg = messages[1]

    assert system_msg["role"] == "system"
    assert "시니어 엔지니어" in system_msg["content"]

    assert user_msg["role"] == "user"
    assert payload.submission_info.code in user_msg["content"]


@pytest.mark.asyncio
async def test_analyze_submission_returns_analysis_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    analyze_submission이 내부적으로 create_structured_analysis를 호출해
    AnalysisResult Pydantic 객체를 반환하는지 검증한다.
    실제 OpenAI 호출은 monkeypatch로 대체한다.
    """
    from app import services  # type: ignore  # for namespace clarity
    from app.services import ai_service

    async def _fake_create_structured_analysis(*args, **kwargs) -> AnalysisResult:  # type: ignore[override]
        return AnalysisResult(
            approach="테스트용 접근 요약",
            time_complexity="O(1)",
            improvement="테스트용 개선 제안",
            next_problem="baekjoon 1000 A+B",
            better_code="print('test better code')",
        )

    monkeypatch.setattr(
        ai_service,
        "create_structured_analysis",
        _fake_create_structured_analysis,
    )

    payload = _make_sample_payload()

    result = await analyze_submission(payload)

    assert isinstance(result, AnalysisResult)
    assert result.approach.startswith("테스트용")
    assert result.time_complexity == "O(1)"
    assert "테스트용 개선" in result.improvement
    assert "baekjoon" in result.next_problem
    assert "better code" in result.better_code

