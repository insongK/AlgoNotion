## 🎯 Chrome Extension (Manifest V3) 설계 개요

이 확장은 **백준(Baekjoon) 제출 화면을 감시**하여, 사용자가 문제를 맞았을 때:

- **제출 ID(submissionId)를 추출**하고
- **정답 코드 원문과 메타데이터(문제 번호, 언어, 실행 시간/메모리)를 수집**한 뒤
- **solved.ac API를 통해 정확한 한글 제목과 티어(난이도)를 보강**하고
- 이 모든 정보를 **백엔드 FastAPI 웹훅 엔드포인트(`/webhook`)로 전송**하여
- 최종적으로 **OpenAI 분석 + Notion 자동 기록 파이프라인**으로 흘려보내는 역할을 수행한다.

BaekjoonHub의 핵심 아이디어 4가지를 모두 반영한다:

1. `setInterval` 기반 **채점 현황 테이블 폴링 및 "맞았습니다!!" 상태 감지**
2. `submissionId`를 이용해 `https://www.acmicpc.net/source/download/${submissionId}` 로 **소스코드 원본 추출**
3. **문제 번호 -> solved.ac API 호출**을 통해 정확한 한글 문제 제목 + 티어(난이도) 추출
4. **언어 문자열 정규화**(예: `Python 3`, `Java 11` → `python`, `java`)로 Notion/백엔드 호환성 확보

---

## 📁 extension 디렉터리 구조 (초안)

```text
extension/
├── manifest.json                 # Manifest V3 정의
├── content/
│   ├── baekjoon_content.js       # 백준 문제/채점 화면에서 DOM 파싱 및 폴링 로직
│   └── utils_dom.js              # DOM 파싱/셀 선택 유틸 (선택)
├── background/
│   └── service_worker.js         # Background Service Worker: 메시지 라우팅, solved.ac / 백엔드 호출
├── scripts/
│   ├── api_client.js             # 백엔드 FastAPI 및 solved.ac 호출 래퍼
│   ├── language_normalizer.js    # 언어 문자열 정규화 로직
│   └── payload_builder.js        # WebhookPayload 구조로 데이터 조립
├── options/
│   ├── options.html              # 옵션 페이지(백엔드 URL, API Key 등 설정)
│   └── options.js                # 옵션 저장/불러오기 로직 (chrome.storage.sync)
├── assets/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── EXTENSION_README.md           # 확장 전용 사용법/구현 메모
```

> 실제 구현 시 파일 수는 조정 가능하나, SRP(단일 책임 원칙)를 유지하기 위해 **역할별로 명확히 모듈을 분리**한다.

---

## 1️⃣ manifest.json 설계 (Manifest V3)

**역할**: 확장의 메타 정보, 권한, 엔트리 포인트를 정의한다.

- **기본 정보**
  - `manifest_version: 3`
  - `name`, `description`, `version`
  - `icons`: `assets/icon16.png`, `icon48.png`, `icon128.png`

- **permissions**
  - `"activeTab"`: 현재 탭 DOM 접근
  - `"scripting"`: MV3에서 content script 주입/제어 시 필요 시 고려
  - `"storage"`: 옵션 페이지에서 저장한 설정 읽기/쓰기
  - `"tabs"`: 필요 시 URL 확인/탭 정보 조회
  - `"alarms"` (선택): 폴링 간격 제어를 service worker 레벨로 확장할 때 고려

- **host_permissions**
  - `"https://www.acmicpc.net/*"`: 백준 사이트 DOM/네트워크 접근
  - `"https://solved.ac/*"`: solved.ac API 호출
  - (백엔드) `"https://<our-backend-domain>/*"`: FastAPI 웹훅 엔드포인트 호출

- **background**
  - `service_worker: "background/service_worker.js"`

- **content_scripts**
  - `matches: ["https://www.acmicpc.net/status*"]` (채점 현황 페이지)
  - `js: ["content/baekjoon_content.js"]`
  - `run_at: "document_idle"` (DOM 로딩 이후)

- **options_page**
  - `"options/options.html"`

---

## 2️⃣ content/baekjoon_content.js – 백준 DOM 파싱 & 폴링

**역할**: 백준 Status(채점 현황) 페이지에서 **사용자 제출 목록을 지속적으로 모니터링**하고, "맞았습니다!!" 상태의 제출을 발견하면 **submissionId + 메타 정보를 background로 전파**한다.

### 2-1. 초기화 로직

- 페이지 로드 시:
  - 현재 URL이 `https://www.acmicpc.net/status` 또는 이와 유사한 경로인지 확인
  - 사용자 ID/필터가 올바르게 설정돼 있는지 확인(선택)
  - 이미 폴링이 동작 중인지 체크(중복 `setInterval` 방지)

### 2-2. setInterval 기반 폴링

- `setInterval` 주기: 2~5초 수준(백준허브 벤치마킹, 서버 부하/사용자 경험 고려)
- 매 주기마다:
  1. **채점 현황 테이블 DOM 탐색**
     - 각 row(제출 기록)에 대해:
       - 제출 번호(`submissionId`)
       - 결과(텍스트/아이콘) → `"맞았습니다!!"` / `"ac"` 감지
       - 문제 번호(`problemId`)
       - 언어, 실행 시간(ms), 메모리(KB) 추출
  2. **이미 처리한 제출인지 여부 체크**
     - `localStorage` 또는 `window.__algoNotionProcessedIds` 등으로 중복 처리 방지
  3. **새로운 AC 제출 발견 시**
     - `submissionId`, `problemId`, `language`, `time`, `memory` 등을 객체로 구성
     - `chrome.runtime.sendMessage` 또는 `chrome.runtime.sendMessage`를 통해 background로 전송

### 2-3. 에러 및 예외 상황 처리

- DOM 구조 변경으로 인해 셀을 찾지 못하면:
  - console.warn로 **오류 패턴 기록**
  - 일정 횟수 이상 실패 시 폴링 중단 or 사용자에게 알림(선택)
- 동일 `submissionId`에 대해 재처리 방지:
  - in-memory set + localStorage 백업 조합 고려

---

## 3️⃣ background/service_worker.js – 메시지 허브 & 외부 API 호출

**역할**: content script에서 전달한 **제출 정보(submissionId, problemId, 언어, 성능)**를 받아:

1. **source download URL**(`https://www.acmicpc.net/source/download/${submissionId}`)로부터 **원본 코드 fetch**
2. **solved.ac API**를 통해 문제 메타데이터(한글 제목, 티어 등) 보강
3. 언어 문자열을 정규화한 뒤
4. 백엔드 FastAPI 서버의 `/webhook` 엔드포인트로 **최종 WebhookPayload JSON을 전송**

### 3-1. 메시지 수신 핸들러

- `chrome.runtime.onMessage.addListener((message, sender, sendResponse) => { ... })`
- message 타입 예:
  - `{ type: "BAEKJOON_AC_SUBMISSION", payload: { submissionId, problemId, language, time, memory } }`

### 3-2. 소스 코드 다운로드 (BaekjoonHub 벤치마킹)

- `fetch("https://www.acmicpc.net/source/download/" + submissionId, { credentials: "include" })`
  - **쿠키 포함** 여부 확인 (사용자 세션 필요)
  - response를 `text()`로 읽어 **원본 코드 문자열** 확보
  - 실패 시 재시도 정책(간단한 1~2회 재시도) 고려

### 3-3. solved.ac API 호출

- 문제 번호(`problemId`) 기반으로:
  - 예: `https://solved.ac/api/v3/problem/show?problemId=${problemId}`
  - 응답에서:
    - 한글 문제 제목
    - 티어(난이도), 태그 등 (필요한 것만 사용)
  - HTTP 에러/쿼터 초과 등 예외 처리:
    - 실패 시에도 파이프라인이 완전히 깨지지 않도록, 백엔드로는 최소 정보(문제 번호 정도)는 전송

### 3-4. 언어 문자열 정규화

- `scripts/language_normalizer.js`의 헬퍼 사용:
  - `"Python 3"` → `"python"`
  - `"Java 11"` → `"java"`
  - `"C++17"` → `"cpp"`
  - 백엔드/Notion에서 사용하는 언어 키와 1:1 매핑되도록 설계

### 3-5. WebhookPayload 조립 및 전송

- `scripts/payload_builder.js` 사용, WebhookPayload 스펙에 맞는 JSON 생성:
  - `platform`: `"baekjoon"`
  - `meta_info`:
    - `title`: solved.ac에서 가져온 한글 제목 (fallback: 백준 페이지에서 파싱한 제목 또는 빈 문자열)
    - `problem_id`: `problemId` (문자열)
    - `link`: `https://www.acmicpc.net/problem/${problemId}`
    - `level`: solved.ac 티어 정보(예: `"Silver III"`, 내부적으로 변환 가능)
    - `language`: 정규화된 언어(예: `"python"`, `"java"`)
  - `submission_info`:
    - `code`: 다운로드한 원본 코드
    - `memory`: 채점 현황에서 읽은 메모리(KB)
    - `time`: 채점 현황에서 읽은 실행시간(ms)

- 백엔드 호출:
  - URL: 옵션에서 설정한 **백엔드 웹훅 엔드포인트** (예: `https://<our-backend>/webhook`)
  - 메서드: `POST`
  - 헤더: `Content-Type: application/json`
  - 바디: 위에서 조립한 WebhookPayload JSON
  - 실패 시:
    - console.error 로 로깅
    - 특정 에러 코드에 따라 재시도/백오프 정책 고려 (초기 버전에서는 단순 로그로 충분)

---

## 4️⃣ scripts/ 모듈 설계

### 4-1. scripts/api_client.js

**역할**: HTTP 호출 공통 래퍼.

- `fetchBaekjoonSource(submissionId): Promise<string>`
  - 위에서 설명한 다운로드 URL로 코드 텍스트 반환
- `fetchSolvedAcProblem(problemId): Promise<{ title: string; tier: string; ... }>`
  - solved.ac 응답 중 필요한 필드만 추려서 반환
- `postToBackendWebhook(payload): Promise<void>`
  - 백엔드 `/webhook`에 POST
- 공통 에러 처리:
  - HTTP status 검증
  - JSON 파싱 실패 처리

### 4-2. scripts/language_normalizer.js

**역할**: 백준/solved.ac/브라우저에서 얻은 언어 문자열을 **백엔드/Notion에서 사용하는 규격**으로 통일.

- `normalizeLanguage(rawLanguage: string): string`
  - 전부 소문자 변환
  - `python 3` → `python`, `java 11` → `java`, `c++17` → `cpp` 등 매핑 테이블 기반
  - 알 수 없는 언어는 원본을 소문자로만 내려서, 백엔드 쪽에서 추가 처리할 수 있게 한다.

### 4-3. scripts/payload_builder.js

**역할**: content/background에서 수집한 데이터를 `.cursorrules`에 정의된 WebhookPayload 구조로 변환.

- 입력:
  - `platform`, `problemId`, `title`, `tier`, `language`, `code`, `time`, `memory`
- 출력:
  - `WebhookPayload` 형태의 JSON 객체
- 책임 분리:
  - 백엔드 스키마(WebhookPayload)가 변경될 경우 이 파일만 업데이트하면 되도록 설계.

---

## 5️⃣ options/ 옵션 페이지 설계

**역할**: 사용자 맞춤 설정을 제공하여, **백엔드 URL/토글 옵션** 등을 제어한다.

- `options.html`
  - 간단한 폼:
    - 백엔드 URL 입력 (`<input type="text">`)
    - solved.ac API 사용 여부 토글(선택)
    - 자동 업로드 활성/비활성 스위치(선택)
  - 저장/초기화 버튼

- `options.js`
  - `chrome.storage.sync`를 사용해 설정 저장/로드
  - 백그라운드/컨텐츠 스크립트가 설정을 읽을 수 있도록 메시지 또는 직접 storage 접근 허용

---

## 6️⃣ 에러 처리 & 로깅 전략

- **DOM 파싱 오류**:
  - content script에서 `console.warn`으로 남기되, 일정 횟수 이상 반복되면 폴링 중단 및 시각적 알림(향후 고려)

- **네트워크 오류 (source download / solved.ac / 백엔드)**:
  - background에서 `console.error` 로그 남김
  - 실패 시에도 브라우저 UI(백준 페이지) 사용성에 영향을 주지 않도록 **조용히 실패**하는 것을 원칙으로 함

- **권한/세션 문제 (백준 로그인 안 돼 있을 때 등)**:
  - source download 403/401 에러가 발생하면, "로그인 필요"임을 로그에 남기고 재시도하지 않음.

---

## 7️⃣ 백엔드와의 인터페이스 정리

백엔드 FastAPI의 `/webhook` 엔드포인트는 `.cursorrules` 및 `README.md`에서 정의한 아래 스키마를 받는다:

- `platform`: `"baekjoon"`
- `meta_info`:
  - `title`: solved.ac에서 가져온 한글 제목(또는 fallback)
  - `problem_id`: 백준 문제 번호 (문자열)
  - `link`: `https://www.acmicpc.net/problem/${problemId}`
  - `level`: solved.ac 티어 (예: `"Silver III"`)
  - `language`: 정규화된 언어 키 (예: `"python"`)
- `submission_info`:
  - `code`: 백준에서 다운받은 원본 소스 코드
  - `memory`: 실행 메모리(KB)
  - `time`: 실행 시간(ms)

이 구조를 기준으로 **extension → backend → OpenAI → Notion**까지가 하나의 일관된 파이프라인을 이룬다.

---

## 8️⃣ 향후 확장 포인트

- **다른 플랫폼 지원**: 프로그래머스, LeetCode 등으로 확장 시, `content/{platform}_content.js`를 추가하고, `platform` 값만 변경하면 백엔드는 그대로 재사용 가능.
- **에러/이벤트 대시보드**: extension에서 발생하는 네트워크/DOM 오류를 별도의 백엔드 엔드포인트로 전송해 관측 가능하게 만들 수도 있다.
- **UI Notification**: 정답 제출 후 Notion 저장이 완료되면, 크롬 알림 또는 작은 토스트를 띄워 사용 경험을 개선.

---

## 9️⃣ 구현 순서 제안 (Step-by-Step)

1. `extension/manifest.json` 기본 뼈대 작성 (MV3, 권한, background, content_scripts, options_page)
2. `content/baekjoon_content.js`에서:
   - 채점 현황 테이블 구조 분석
   - `setInterval` 기반 폴링으로 "맞았습니다!!" 행 감지
   - submissionId/problemId/language/time/memory 추출 및 중복 방지 로직 구현
   - background로 메시지 전송까지 확인
3. `scripts/api_client.js`에서:
   - 백준 소스 다운로드 fetch 래퍼 구현
   - solved.ac problem fetch 래퍼 구현
   - 백엔드 `/webhook` POST 래퍼 구현
4. `scripts/language_normalizer.js` / `scripts/payload_builder.js` 구현:
   - 언어 정규화 테이블 작성
   - WebhookPayload JSON 생성 함수 구현
5. `background/service_worker.js`에서:
   - 메시지 리스너 구현
   - source download + solved.ac + payload builder + backend POST를 하나의 플로우로 연결
6. `options/` 페이지 구현:
   - 백엔드 URL 및 옵션을 chrome.storage.sync에 저장/로드
   - background/api_client.js에서 해당 설정을 사용하도록 연동
7. 크롬 개발자 모드에서 로컬 로드 후:
   - 백준 사이트에서 실제로 AC 제출 시 end-to-end 동작 확인
   - 콘솔/네트워크 로그로 에러 및 edge case 분석

