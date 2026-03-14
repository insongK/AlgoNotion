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

## 배포 계획

### 목표 운영 구조

- Chrome Extension은 백준 제출 정보를 수집하고, 공용 백엔드 서버로 전송합니다.
- 공용 백엔드 서버는 OpenAI API 호출 비용을 부담하고, AI 분석 결과를 생성합니다.
- Notion 저장은 사용자별 설정을 기준으로 분기되어야 합니다. 즉, OpenAI는 공용, Notion은 개인별 연결 구조가 적합합니다.

### 권장 아키텍처

1. 사용자는 확장 프로그램을 설치합니다.
2. 확장 프로그램은 공용 백엔드 URL로 제출 데이터를 전송합니다.
3. 공용 백엔드는 OpenAI로 분석을 수행합니다.
4. 공용 백엔드는 요청에 포함된 사용자별 Notion 설정을 사용해 각자의 Notion DB에 저장합니다.

### EC2 배포 초안

- 인프라:
  - AWS EC2 1대
  - 고정 공인 IP 또는 Elastic IP 사용 권장
  - 운영체제는 Ubuntu 계열 권장
- 런타임:
  - Python 3.10 이상
  - `uvicorn` 또는 `gunicorn + uvicorn worker`
- 리버스 프록시:
  - Nginx 사용 권장
  - `80/443` 포트를 열고 내부적으로 FastAPI 포트로 프록시
- 프로세스 관리:
  - `systemd` 서비스로 등록 권장
- 보안:
  - 보안 그룹에서 `22`, `80`, `443`만 개방 권장
  - 개발 단계에서는 임시로 `8000` 직접 개방 가능

### EC2 배포 순서 예시

1. EC2 생성 및 보안 그룹 설정
2. Python / pip / git 설치
3. 프로젝트 코드 배포
4. `.env` 설정
5. 가상환경 생성 및 `requirements.txt` 설치
6. `uvicorn app.main:app --host 0.0.0.0 --port 8000`으로 1차 구동 확인
7. `systemd` 서비스 등록
8. 필요 시 Nginx 연결
9. 확장 프로그램의 backend URL을 EC2 주소로 변경

### 운영 모드 선택

- 단일 사용자 PoC:
  - 서버 `.env`에 `NOTION_TOKEN`, `NOTION_DATABASE_ID`를 직접 넣어도 됩니다.
  - 가장 단순하지만 여러 사용자를 받을 수는 없습니다.
- 다중 사용자 운영:
  - 서버 공용 `.env`에는 OpenAI 설정만 둡니다.
  - Notion 관련 값은 사용자별로 받아 저장해야 합니다.
  - 이 구조가 실제 배포에 더 적합합니다.

## 사용자별 Notion 설정 방식

### 왜 분리가 필요한가

- OpenAI API 비용은 서비스 운영자가 부담할 수 있습니다.
- 하지만 Notion은 각 사용자가 자신의 워크스페이스와 데이터베이스에 저장하길 원할 가능성이 높습니다.
- 따라서 `NOTION_TOKEN`, `NOTION_DATABASE_ID`를 서버 전역 환경변수 하나로 두는 방식은 다중 사용자 운영에 맞지 않습니다.

### 현재 구조의 한계

- 현재 백엔드는 `.env`의 `NOTION_TOKEN`, `NOTION_DATABASE_ID`를 전역으로 읽습니다.
- 이 방식은 한 사람의 Notion만 연결할 수 있습니다.
- 여러 사용자가 동시에 쓰면 모두 같은 Notion으로 저장되는 문제가 생깁니다.

### 권장 사용자별 설정 구조

사용자별로 아래 정보가 필요합니다.

- `notion_token`
- `notion_database_id`

확장 프로그램 또는 별도 설정 페이지에서 사용자 입력을 받고, 백엔드에 함께 전달하는 방식이 적합합니다.

예시 흐름:

1. 사용자가 확장 옵션 페이지에 자신의 Notion Integration Token 입력
2. 사용자가 자신의 Notion Database ID 입력
3. 확장 프로그램이 이 값을 `chrome.storage` 등에 저장
4. 제출 업로드 시 웹훅 payload 또는 별도 인증 토큰과 함께 백엔드에 전송
5. 백엔드는 해당 사용자 설정으로 Notion API 호출

### 사용자에게 안내해야 할 Notion 설정 절차

1. Notion에서 새 Integration 생성
2. Integration Token 발급
3. 저장 대상 Database 생성
4. 해당 Database에 Integration을 연결
5. Database ID 확인
6. 확장 옵션 페이지에 Token과 Database ID 입력

### 확장 옵션 페이지에 입력하는 실제 방법

아래 순서대로 진행하면 됩니다.

1. Notion API 키 발급
   - 브라우저에서 Notion Integrations 관리 페이지로 이동합니다.
   - `New integration`을 눌러 새 Integration을 생성합니다.
   - 이름은 `AlgoNotion`처럼 알아보기 쉽게 지정합니다.
   - 생성이 완료되면 `Internal Integration Token`을 확인할 수 있습니다.
   - 이 값을 확장 옵션의 `Notion Integration Token` 칸에 입력합니다.

2. 저장할 Notion 데이터베이스 준비
   - 본인 워크스페이스에 문제 기록용 Database를 하나 생성합니다.
   - 최소한 제목, 언어, 플랫폼, 성능 정도를 담을 수 있게 준비하는 것을 권장합니다.

3. Integration을 Database에 연결
   - 해당 Database 페이지 우측 상단의 공유 메뉴를 엽니다.
   - 생성한 Integration을 초대하거나 연결합니다.
   - 이 과정이 빠지면 토큰이 있어도 해당 Database에 쓸 수 없습니다.

4. Database ID 확인
   - Database 페이지 URL에서 Database ID를 확인합니다.
   - 보통 URL 안의 긴 문자열이 Database ID입니다.
   - 하이픈이 포함된 형태든 제거된 형태든 Notion에서 일반적으로 인식 가능합니다.
   - 이 값을 확장 옵션의 `Notion Database ID` 칸에 입력합니다.

5. 확장 옵션 페이지 입력
   - Chrome 확장 프로그램의 `AlgoNotion 설정` 페이지를 엽니다.
   - `백엔드 URL`에 배포한 서버 주소를 입력합니다. 예: `http://43.201.46.22:8000`
   - `Notion Integration Token`에 1단계에서 발급한 토큰을 입력합니다.
   - `Notion Database ID`에 4단계에서 확인한 값을 입력합니다.
   - `저장` 버튼을 누릅니다.

6. 실제 업로드 확인
   - 백준 제출 목록 페이지에서 `Notion 업로드` 버튼을 누릅니다.
   - 정상 동작하면 본인 Database에 페이지가 생성됩니다.
   - 실패하면 확장 로그 또는 백엔드 로그에서 Notion 권한/Database 연결 여부를 먼저 확인합니다.

### 백엔드에서 필요한 추가 작업

- 사용자별 Notion 설정 저장소 필요
  - 간단한 단계에서는 SQLite 가능
  - 운영 단계에서는 PostgreSQL 권장
- 사용자 식별 수단 필요
  - 최소한 extension 발급 키 또는 로그인 기반 식별 필요
- 웹훅 처리 시 전역 Notion 설정 대신 사용자별 Notion 설정 조회 필요
- Notion 토큰은 평문 저장 대신 암호화 저장 권장

### 현실적인 단계별 진행안

- 1단계:
  - 지금 구조 유지
  - 운영자 1명만 사용하는 PoC로 먼저 안정화
- 2단계:
  - extension 옵션 페이지에 `backend URL`, `Notion Token`, `Notion Database ID` 입력 UI 추가
  - 백엔드가 payload의 사용자별 Notion 설정을 사용하도록 변경
- 3단계:
  - 사용자 계정 시스템 추가
  - 사용자별 설정을 서버 DB에 저장
  - 확장에서는 API Key 또는 로그인 세션만 보내도록 단순화

## 배포 전 체크리스트

- EC2에서 백엔드 프로세스가 실제로 떠 있는지 확인
- 보안 그룹 인바운드 포트 확인
- 확장 backend URL이 실제 서버 주소를 가리키는지 확인
- OpenAI API Key가 서버에 설정되어 있는지 확인
- Notion 저장 방식이 `단일 사용자 전역 설정`인지 `사용자별 설정`인지 명확히 결정
- 실패 로그를 확인할 수 있는 백엔드 로그 수집 방식 준비


