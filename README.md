# 🚀 Algorithm Insight Automator (PoC)

## 📖 Project Overview
이 프로젝트는 코딩테스트 플랫폼(백준 등)에서 정답을 맞힌 코드를 자동으로 추출하고 분석하여 기록하는 파이프라인 서비스입니다. 단순히 주어진 문제를 풀고 넘어가는 것을 넘어, 문제의 근본적인 원인을 파고들고 더 깊은 기술적 고민을 통해 꾸준한 기술적 성장을 이루기 위한 목적을 가집니다.

## 🛠 Tech Stack
- **Backend/Orchestration:** Python 3.10+, FastAPI, Uvicorn
- **AI/LLM:** OpenAI API (gpt-4o-mini)
- **Integration:** Notion API (`notion-client`)
- **Frontend (Planned):** Chrome Extension Manifest V3

## 📦 Requirements & Installation

- **Python**: 3.10 이상
- **의존성 설치**:

```bash
pip install -r requirements.txt
```

## ⚙️ Environment Variables

`.env` 파일 또는 시스템 환경변수로 아래 값을 설정해야 합니다.

- `OPENAI_API_KEY`: OpenAI API 키 (필수)
- `OPENAI_MODEL_NAME`: 사용할 LLM 모델명 (기본값: `gpt-4o-mini`)
- `NOTION_TOKEN`: Notion 통합 토큰 (Step 3 구현 시 사용)
- `NOTION_DATABASE_ID`: 분석 결과를 적재할 Notion Database ID (Step 3 구현 시 사용)

## 📁 Directory Structure

```text
.
├── app/
│   ├── main.py                     # FastAPI 엔트리포인트
│   ├── api/
│   │   └── routes/
│   │       └── webhook.py           # Webhook 수신 라우터
│   ├── core/
│   │   ├── config.py                # 환경변수(.env) 기반 설정
│   │   └── logging.py               # 로깅 설정(선택)
│   ├── schemas/
│   │   ├── webhook.py               # meta_info / submission_info 입력 스키마
│   │   └── analysis.py              # LLM Output(approach/time_complexity/...) 스키마
│   ├── services/
│   │   ├── ai_service.py            # OpenAI 호출 및 결과 구조화/파싱
│   │   └── notion_service.py        # Notion 적재/페이지 구성
│   ├── clients/
│   │   ├── openai_client.py         # OpenAI API 클라이언트 래퍼
│   │   └── notion_client.py         # Notion API 클라이언트 래퍼
│   └── utils/
│       └── errors.py                # 공통 예외/에러 유틸(선택)
├── tests/                           # (선택) 테스트
├── .env.example                     # 환경변수 예시(키 값은 채우지 않음)
├── requirements.txt
└── README.md
```

### 주요 모듈 역할

- `app/main.py`: FastAPI 앱 생성 및 라우터(`api/routes/webhook.py`) 등록
- `app/api/routes/webhook.py`: 웹훅 엔드포인트(`/webhook`) 정의, Step 1+2 오케스트레이션
- `app/schemas/webhook.py`: 입력 스키마 (`platform`, `meta_info`, `submission_info`)
- `app/schemas/analysis.py`: LLM 분석 결과 스키마 (approach/time_complexity/improvement/next_problem/better_code)
- `app/core/config.py`: `.env` 기반 설정 로딩 (`OPENAI_API_KEY`, `OPENAI_MODEL_NAME`, `NOTION_TOKEN`, `NOTION_DATABASE_ID` 등)
- `app/clients/openai_client.py`: OpenAI Async 클라이언트 래퍼
- `app/clients/notion_client.py`: Notion AsyncClient 래퍼
- `app/services/ai_service.py`: 프롬프트 빌드 및 LLM 호출 → `AnalysisResult` 생성 로직
- `app/services/notion_service.py`: WebhookPayload + AnalysisResult를 기반으로 Notion 페이지 생성

## 🧪 Testing

- **테스트 실행**

```bash
pytest
```

- **주요 테스트 파일**
  - `tests/test_webhook_api.py`: `/webhook` 엔드포인트 요청/응답 및 Validation 검증 (OpenAI 호출 mock)
  - `tests/test_ai_service.py`: `build_prompt` 메시지 구조 및 `analyze_submission`의 `AnalysisResult` 반환 검증
  - `tests/test_notion_client_service.py`: Notion 클라이언트 초기화 및 `save_to_notion`이 `pages.create`를 올바로 호출하는지 검증

## 🔄 PoC Pipeline Architecture
현재 PoC(Proof of Concept)는 다음 3단계로 구성되며, FastAPI 서버가 중심 역할을 합니다.

### Step 1: Webhook 수신 (FastAPI)
클라이언트(Postman 또는 Extension)로부터 문제 메타 정보와 제출된 코드 데이터를 JSON 형태로 수신합니다.
- **Input Data (Pydantic Models):**
  - `platform`, `meta_info` (title, problem_id, link, level, language 등), `submission_info` (code, memory, time)

### Step 2: AI 심층 분석 (OpenAI API)
수신한 데이터를 바탕으로 LLM을 호출하여, 코드의 효율성을 시스템 관점에서 깊이 있게 분석합니다. 
- **AI Output (Structured JSON):**
  - `approach`: 접근 방식 (100자 이내)
  - `time_complexity`: 시간복잡도 분석
  - `improvement`: 부족한 부분 및 구조적 개선점
  - `next_problem`: 다음 추천 문제 (플랫폼, 문제 번호/제목 포함)
  - `better_code`: 더 좋은 모범 답안 코드

현재 PoC 단계에서는 `app/services/ai_service.py`에서 OpenAI 응답을 더미 데이터로 매핑하고 있으며, 이후 `responses.create`의 JSON 구조화를 활용해 위 필드를 직접 파싱하도록 확장할 예정입니다.

### Step 3: Notion 자동 기록 (Notion API)
원본 데이터와 AI의 분석 결과를 조합하여 Notion Database에 체계적으로 적재합니다.
- **Notion Structure:**
  - `Properties`: 문제 제목, 언어, 플랫폼, 실행 성능(시간/메모리)
  - `Page Blocks`: AI 분석 결과(마크다운 텍스트) 및 제출한 원본 코드(코드 블록)


