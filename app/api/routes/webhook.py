from fastapi import APIRouter, HTTPException

from app.schemas.webhook import WebhookPayload
from app.schemas.analysis import AnalysisResult
from app.services.ai_service import analyze_submission
from app.services.notion_service import save_to_notion


router = APIRouter()


@router.post("/webhook", response_model=AnalysisResult)
async def receive_webhook(payload: WebhookPayload) -> AnalysisResult:
    """
    Step 1 + Step 2 + Step 3(노션 저장)를 한 번에 처리하는 엔드포인트.
    - Step 1: 코딩테스트 플랫폼에서 전달된 메타 정보 + 제출 코드 수신
    - Step 2: OpenAI API를 호출해 구조화된 분석 결과 생성
    - Step 3: Notion Database에 원본 + 분석 결과 저장
    """
    try:
        analysis = await analyze_submission(payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}") from e

    # Notion 저장은 응답 모델을 바꾸지 않고 비동기 처리만 수행
    try:
        await save_to_notion(payload, analysis)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notion save failed: {e}") from e

    return analysis

