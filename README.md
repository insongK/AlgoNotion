# 🚀 Algorithm Insight Automator (PoC)

## 📖 Project Overview
이 프로젝트는 코딩테스트 플랫폼(백준 등)에서 정답을 맞힌 코드를 자동으로 추출하고 분석하여 기록하는 파이프라인 서비스입니다. 단순히 주어진 문제를 풀고 넘어가는 것을 넘어, 문제의 근본적인 원인을 파고들고 더 깊은 기술적 고민을 통해 꾸준한 기술적 성장을 이루기 위한 목적을 가집니다.

## 🛠 Tech Stack
- **Backend/Orchestration:** Python 3.10+, FastAPI, Uvicorn
- **AI/LLM:** OpenAI API (gpt-4o-mini)
- **Integration:** Notion API (`notion-client`)
- **Frontend (Planned):** Chrome Extension Manifest V3

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

### Step 3: Notion 자동 기록 (Notion API)
원본 데이터와 AI의 분석 결과를 조합하여 Notion Database에 체계적으로 적재합니다.
- **Notion Structure:**
  - `Properties`: 문제 제목, 언어, 플랫폼, 실행 성능(시간/메모리)
  - `Page Blocks`: AI 분석 결과(마크다운 텍스트) 및 제출한 원본 코드(코드 블록)


