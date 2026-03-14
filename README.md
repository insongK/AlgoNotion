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
python -m pytest
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

현재는 OpenAI Python SDK의 `client.beta.chat.completions.parse`를 사용해 위 5개 필드를 **Pydantic 모델(`AnalysisResult`)로 직접 파싱**하여 반환합니다.

### Step 3: Notion 자동 기록 (Notion API)
원본 데이터와 AI의 분석 결과를 조합하여 Notion Database에 체계적으로 적재합니다.
- **Notion Structure:**
  - `Properties`: 문제 제목, 언어, 플랫폼, 실행 성능(시간/메모리)
  - `Page Blocks`: AI 분석 결과(마크다운 텍스트) 및 제출한 원본 코드(코드 블록)

## 구현 중 확인된 문제점

- 일반적인 Manifest V3 설정만으로는 백준 소스 fetch가 안정적으로 동작하지 않았습니다. 이 프로젝트에서는 `declarativeNetRequest` 헤더 수정 규칙을 추가하기 전까지 `https://www.acmicpc.net/source/download/{submissionId}` 요청이 `200 OK`인데도 body가 비어 있었습니다.
- 초기 확장 흐름은 `chrome.runtime.sendMessage`만 끝나면 업로드 완료로 처리하고 있었기 때문에, 실제 backend 또는 Notion 저장이 실패해도 UI상 성공처럼 보일 수 있었습니다.
- 웹훅 라우트에서 Notion 저장 실패를 삼키고 있었기 때문에, 브라우저에서는 정상 처리처럼 보여도 실제 Notion 페이지는 생성되지 않는 문제가 있었습니다.
- 제출 코드와 AI가 생성한 개선 코드가 길어질 경우, Notion rich text 길이 제한을 초과해 단일 code block 생성이 실패할 수 있었습니다.
- 백준 응답은 요청 컨텍스트에 따라 동작이 달랐습니다. 브라우저에서 직접 이동할 때는 정상이어도, BaekjoonHub 방식의 헤더 수정 없이 확장 `fetch()`로 호출하면 응답 본문이 비는 경우가 있었습니다.

## 추가 개선사항

- 확장 UI에서 `코드 추출 실패`, `백엔드 전송 실패`, `Notion 저장 실패`를 구분해서 보여주는 상태 피드백을 추가할 필요가 있습니다.
- 확장 메시지 흐름과 backend 실패 전파에 대한 자동화 테스트를 추가할 필요가 있습니다.
- 웹훅 전송 실패에 대한 재시도 및 backoff 정책을 추가하고, 해당 정보를 로그로 확인할 수 있게 해야 합니다.
- 긴 제출 코드와 긴 AI 생성 코드에 대해 Notion block 분할이 정상 동작하는지 검증하는 테스트가 필요합니다.
- 현재 content script에 들어간 인라인 버튼 스타일을 별도 stylesheet로 분리해 유지보수성을 높일 필요가 있습니다.
- 현재 메모리 기준으로만 처리하는 중복 업로드 방지를, extension storage 기반의 submission ID 기록으로 보강할 필요가 있습니다.
- 실제 운영을 고려하면 구조화된 백엔드 로그, 요청 ID, 확장 팝업 또는 페이지 토스트 기반의 오류 노출 같은 관측성 보강이 필요합니다.


