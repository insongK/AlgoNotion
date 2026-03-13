from app.schemas.webhook import WebhookPayload
from app.schemas.analysis import AnalysisResult
from app.clients.openai_client import create_structured_analysis


def build_prompt(payload: WebhookPayload) -> str:
    """
    WebhookPayload를 기반으로 LLM에 전달할 프롬프트를 구성.
    - 현재는 단순 텍스트 기반, 이후에 시스템/유저 메시지 구조 등으로 확장 가능.
    """
    meta = payload.meta_info
    sub = payload.submission_info
    return f"""
당신은 코딩테스트 풀이를 분석하는 시니어 엔지니어입니다.

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


async def analyze_submission(payload: WebhookPayload) -> AnalysisResult:
    """
    Step 2: OpenAI API를 호출해 구조화된 분석 결과를 생성.
    - 현재는 create_structured_analysis의 raw 응답을 그대로 받아
      임시로 더미 AnalysisResult로 매핑.
    - 이후 responses.create의 JSON Schema 기능 등을 이용해
      바로 AnalysisResult 형태로 파싱하는 방향으로 확장 가능.
    """
    prompt = build_prompt(payload)

    # TODO: response에서 실제 필드를 파싱하도록 구현
    _ = await create_structured_analysis(prompt)

    return AnalysisResult(
        approach="두 포인터를 사용해 O(N) 시간에 해결한 접근입니다.",
        time_complexity="O(N)",
        improvement="입출력 최적화와 예외 케이스(빈 배열 등)에 대한 방어 코드가 부족합니다.",
        next_problem="baekjoon 3273 두 수의 합",
        better_code="# TODO: LLM이 생성한 더 나은 예시 코드를 여기에 채웁니다.",
    )

