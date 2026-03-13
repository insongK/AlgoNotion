from typing import Any, Dict

from openai import AsyncOpenAI

from app.core.config import get_settings


def get_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment")
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def create_structured_analysis(prompt: str) -> Dict[str, Any]:
    """
    LLM 호출을 담당하는 최소 래퍼.
    - 실제 프로덕션에서는 프롬프트 템플릿/에러 처리/리트라이 등을 확장.
    """
    settings = get_settings()
    client = get_openai_client()

    # TODO: responses.create의 정확한 파라미터는 requirements 및 실제 버전에 맞춰 조정
    response = await client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    return response  # 상위 서비스 레이어에서 필요한 형태로 파싱

