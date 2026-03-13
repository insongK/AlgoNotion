from typing import Any, Dict, List, Type, TypeVar

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel

from app.core.config import get_settings


T = TypeVar("T", bound=BaseModel)


def get_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment")
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def create_structured_analysis(
    messages: List[Dict[str, str]],
    response_format: type[T],
) -> T:
    """
    OpenAI의 beta.chat.completions.parse를 사용해
    LLM 응답을 Pydantic 모델로 바로 파싱한다.
    """
    settings = get_settings()
    client = get_openai_client()

    try:
        completion = await client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=messages,
            response_format=response_format,
        )
    except OpenAIError as e:
        # 인증/요금제/모델명 오류, 입력 포맷 문제 등 OpenAI 측 에러
        raise RuntimeError(
            "OpenAI chat.completions.parse 호출에 실패했습니다. "
            "API 키, 네트워크 상태, 모델 이름(openai_model)을 확인하세요."
        ) from e
    except Exception as e:
        # 네트워크 장애, 직렬화 문제 등 비예상 오류
        raise RuntimeError(
            "OpenAI API 호출 중 예기치 못한 오류가 발생했습니다."
        ) from e

    if not completion.choices:
        raise RuntimeError("OpenAI 응답에 choices가 비어 있습니다.")

    parsed = getattr(completion.choices[0].message, "parsed", None)
    if parsed is None:
        raise RuntimeError(
            "OpenAI 응답에서 parsed 데이터를 찾을 수 없습니다. "
            "response_format 설정과 모델 지원 여부를 확인하세요."
        )

    return parsed


