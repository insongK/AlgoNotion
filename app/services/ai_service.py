from logging import getLogger
from typing import Dict, List

from app.schemas.webhook import WebhookPayload
from app.schemas.analysis import AnalysisResult
from app.clients.openai_client import create_structured_analysis


logger = getLogger(__name__)


def build_prompt(payload: WebhookPayload) -> List[Dict[str, str]]:
    """
    WebhookPayload를 기반으로 OpenAI Chat API 규격에 맞는 messages 배열을 생성한다.
    - System: 시니어 엔지니어 역할 및 출력 요구사항 명시
    - User: 문제/코드/실행 정보 전달
    """
    meta = payload.meta_info
    sub = payload.submission_info

    system_content = (
        "당신은 코딩테스트 풀이를 분석하는 시니어 엔지니어입니다. "
        "입력으로 주어지는 문제 정보와 사용자의 제출 코드를 기반으로, "
        "다음 필드를 모두 채운 JSON 구조로만 답변해야 합니다:\n"
        "- approach: 100자 이내의 접근 방식 요약\n"
        "- time_complexity: 빅오 표기법 기반 시간 복잡도\n"
        "- improvement: 코드 품질/성능/구조 관점에서의 개선점\n"
        "- next_problem: 다음으로 풀면 좋은 문제 추천 (플랫폼과 문제 ID 또는 제목 포함)\n"
        "- better_code: 더 나은 모범 코드 (동일 문제 기준)\n"
    )

    user_content = f"""
[문제 정보]
- 플랫폼: {payload.platform}
- 제목: {meta.title}
- 문제 ID: {meta.problem_id}
- 링크: {meta.link}
- 레벨: {meta.level}
- 언어: {meta.language}

[제출 코드]
```{meta.language}
{sub.code}
```

[실행 정보]
- 시간: {sub.time}
- 메모리: {sub.memory}
"""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


async def analyze_submission(payload: WebhookPayload) -> AnalysisResult:
    """
    Step 2: OpenAI API를 비동기로 호출해 구조화된 분석 결과(AnalysisResult)를 생성한다.
    """
    messages = build_prompt(payload)

    try:
        result = await create_structured_analysis(
            messages=messages,
            response_format=AnalysisResult,
        )
    except Exception as e:
        # 호출 실패의 근본 원인을 로그에 남기고 상위 레이어에서 HTTP 응답으로 변환할 수 있도록 래핑
        logger.exception("OpenAI 기반 풀이 분석에 실패했습니다.")
        raise RuntimeError("OpenAI를 사용한 풀이 분석 중 오류가 발생했습니다.") from e

    return result

