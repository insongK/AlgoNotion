// DOM 선택자 상수들: 나중에 구조가 바뀌더라도 이 부분만 수정할 수 있도록 분리한다.
const STATUS_TABLE_SELECTOR = '#status-table'; // 채점 현황 테이블 전체
const TABLE_BODY_ROW_SELECTOR = 'tbody tr'; // 각 제출 기록 행
const SUBMISSION_ID_CELL_SELECTOR = 'td:nth-child(1)'; // 제출 번호가 들어있는 셀 (예시)
const PROBLEM_ID_CELL_SELECTOR = 'td:nth-child(3)'; // 문제 번호가 들어있는 셀 (예시)
const LANGUAGE_CELL_SELECTOR = 'td:nth-child(7)'; // 언어가 들어있는 셀 (예시)
const TIME_CELL_SELECTOR = 'td:nth-child(9)'; // 실행 시간이 들어있는 셀 (예시)
const MEMORY_CELL_SELECTOR = 'td:nth-child(8)'; // 메모리가 들어있는 셀 (예시)
const RESULT_CELL_SELECTOR = 'td:nth-child(4)'; // 결과(맞았습니다!! 등)가 들어있는 셀 (예시)

// "맞았습니다!!" 또는 AC 상태를 감지하기 위한 키워드/클래스
const AC_TEXT_KEYWORD = '맞았습니다!!';
const AC_CLASS_NAME = 'ac'; // 백준에서 사용하는 AC 결과용 클래스 (예시)

// 이미 처리한 submissionId를 기억해 두어 중복 전송을 막는다.
const processedSubmissionIds = new Set();

// interval 중복 실행을 막기 위한 플래그와 핸들
let pollingIntervalId = null;

/**
 * 현재 페이지가 백준 채점 현황(Status) 페이지인지 대략적으로 판별한다.
 */
function isBaekjoonStatusPage() {
  return window.location.hostname === 'www.acmicpc.net' &&
    window.location.pathname.startsWith('/status');
}

/**
 * 한 행(row)에서 결과가 "AC"인지 판별한다.
 */
function isRowAccepted(row) {
  const resultCell = row.querySelector(RESULT_CELL_SELECTOR);
  if (!resultCell) {
    return false;
  }

  const text = resultCell.textContent || '';
  const hasAcText = text.includes(AC_TEXT_KEYWORD);
  const hasAcClass = resultCell.classList.contains(AC_CLASS_NAME);

  return hasAcText || hasAcClass;
}

/**
 * 한 행(row)이 현재 로그인한 유저의 제출인지 판별한다.
 * - 실제 구현 시에는 로그인 영역 또는 테이블 내 사용자 ID 셀을 파싱해 비교해야 한다.
 * - 여기서는 TODO로 남겨두고, 기본적으로는 true를 반환해 전체 제출을 대상으로 동작하게 한다.
 */
function isRowFromCurrentUser(_row) {
  // TODO: 백준 DOM에서 현재 사용자 ID와 row의 사용자 ID를 비교하도록 구현
  return true;
}

/**
 * 한 행(row)에서 제출 메타데이터를 추출한다.
 */
function extractSubmissionMeta(row) {
  const submissionIdCell = row.querySelector(SUBMISSION_ID_CELL_SELECTOR);
  const problemIdCell = row.querySelector(PROBLEM_ID_CELL_SELECTOR);
  const languageCell = row.querySelector(LANGUAGE_CELL_SELECTOR);
  const timeCell = row.querySelector(TIME_CELL_SELECTOR);
  const memoryCell = row.querySelector(MEMORY_CELL_SELECTOR);

  if (!submissionIdCell || !problemIdCell || !languageCell || !timeCell || !memoryCell) {
    return null;
  }

  const submissionId = (submissionIdCell.textContent || '').trim();
  const problemId = (problemIdCell.textContent || '').trim();
  const language = (languageCell.textContent || '').trim();
  const time = parseInt((timeCell.textContent || '').trim(), 10);
  const memory = parseInt((memoryCell.textContent || '').trim(), 10);

  if (!submissionId || !problemId || !language || Number.isNaN(time) || Number.isNaN(memory)) {
    return null;
  }

  return {
    submissionId,
    problemId,
    language,
    time,
    memory,
  };
}

/**
 * 채점 현황 테이블을 순회하며 새로운 AC 제출을 발견하면 background로 전송한다.
 */
function pollStatusTable() {
  const table = document.querySelector(STATUS_TABLE_SELECTOR);
  if (!table) {
    // 테이블을 찾지 못한 경우, 조용히 패스하고 다음 interval에서 다시 시도한다.
    return;
  }

  const rows = table.querySelectorAll(TABLE_BODY_ROW_SELECTOR);
  rows.forEach((row) => {
    if (!isRowFromCurrentUser(row)) {
      return;
    }

    if (!isRowAccepted(row)) {
      return;
    }

    const meta = extractSubmissionMeta(row);
    if (!meta) {
      return;
    }

    if (processedSubmissionIds.has(meta.submissionId)) {
      // 이미 처리한 제출이면 다시 전송하지 않는다.
      return;
    }

    processedSubmissionIds.add(meta.submissionId);

    const message = {
      type: 'BAEKJOON_AC_SUBMISSION',
      payload: meta,
    };

    chrome.runtime.sendMessage(message);
  });
}

/**
 * 폴링을 시작한다. (2초 간격)
 */
function startPolling() {
  if (pollingIntervalId !== null) {
    return;
  }

  pollingIntervalId = window.setInterval(pollStatusTable, 2000);
}

// 페이지가 백준 채점 현황 페이지일 때만 폴링을 시작한다.
if (isBaekjoonStatusPage()) {
  startPolling();
}

