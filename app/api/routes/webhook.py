from fastapi import APIRouter, HTTPException

from app.schemas.webhook import WebhookPayload
from app.schemas.analysis import AnalysisResult
from app.services.ai_service import analyze_submission


router = APIRouter()


@router.post("/webhook", response_model=AnalysisResult)
async def receive_webhook(payload: WebhookPayload) -> AnalysisResult:
    """
    Step 1 + Step 2를 한 번에 처리하는 엔드포인트.
    - Step 1: 코딩테스트 플랫폼에서 전달된 메타 정보 + 제출 코드 수신
    - Step 2: OpenAI API를 호출해 구조화된 분석 결과 생성
    """
    try:
        return await analyze_submission(payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}") from e

