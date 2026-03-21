from logging import getLogger
from typing import Dict, List

from app.clients.openai_client import create_structured_analysis
from app.errors import AppError, BadGatewayError
from app.schemas.analysis import AnalysisResult
from app.schemas.webhook import WebhookPayload


logger = getLogger(__name__)


def build_prompt(payload: WebhookPayload) -> List[Dict[str, str]]:
    meta = payload.meta_info
    sub = payload.submission_info

    system_content = (
        "You are a senior coding interview reviewer (시니어 엔지니어). "
        "Based on the problem metadata and submitted code, "
        "return only JSON with these fields filled.\n"
        "- approach: concise summary of the solution approach\n"
        "- time_complexity: big-O time complexity\n"
        "- improvement: concrete code or logic improvement\n"
        "- next_problem: one recommended next problem\n"
        "- better_code: improved code for the same problem\n"
    )

    user_content = f"""
[Problem]
- platform: {payload.platform}
- title: {meta.title}
- problem_id: {meta.problem_id}
- link: {meta.link}
- level: {meta.level}
- language: {meta.language}

[Submitted Code]
```{meta.language}
{sub.code}
```

[Execution]
- time: {sub.time}
- memory: {sub.memory}
"""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


async def analyze_submission(payload: WebhookPayload) -> AnalysisResult:
    messages = build_prompt(payload)

    try:
        return await create_structured_analysis(
            messages=messages,
            response_format=AnalysisResult,
        )
    except AppError:
        logger.exception("OpenAI-based analysis failed with mapped application error.")
        raise
    except Exception as e:
        logger.exception("OpenAI-based analysis failed with unexpected error.")
        raise BadGatewayError("Failed to analyze submission with OpenAI") from e
