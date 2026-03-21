from typing import Dict, List, TypeVar

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel

from app.core.config import get_settings
from app.errors import BadGatewayError, ServiceUnavailableError, TooManyRequestsError


T = TypeVar("T", bound=BaseModel)


def get_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise ServiceUnavailableError("OPENAI_API_KEY is not set in environment")
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def create_structured_analysis(
    messages: List[Dict[str, str]],
    response_format: type[T],
) -> T:
    settings = get_settings()
    client = get_openai_client()

    try:
        completion = await client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=messages,
            response_format=response_format,
        )
    except OpenAIError as e:
        if getattr(e, "status_code", None) == 429:
            raise TooManyRequestsError("OpenAI rate limit exceeded") from e
        raise BadGatewayError("OpenAI chat.completions.parse request failed") from e
    except Exception as e:
        raise BadGatewayError("Unexpected error while calling OpenAI API") from e

    if not completion.choices:
        raise BadGatewayError("OpenAI response choices were empty")

    parsed = getattr(completion.choices[0].message, "parsed", None)
    if parsed is None:
        raise BadGatewayError("OpenAI response did not include parsed content")

    return parsed
