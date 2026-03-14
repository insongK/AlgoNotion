// DOM 선택자: 테이블만 고정하고, 컬럼 인덱스는 헤더 파싱으로 동적 결정
const STATUS_TABLE_SELECTOR = "#status-table";
const TABLE_BODY_ROW_SELECTOR = "tbody tr";

// 헤더 텍스트 → 컬럼 키 매핑 (공백/대소문자 무시하고 매칭)
const HEADER_KEYS = {
  "제출 번호": "submissionId",
  문제: "problemId",
  결과: "result",
  메모리: "memory",
  시간: "time",
  언어: "language",
};

const AC_TEXT_KEYWORD = "맞았습니다!!";
const AC_CLASS_NAME = "ac";

const processedSubmissionIds = new Set();
let pollingIntervalId = null;

/**
 * 테이블의 첫 번째 행(thead tr 또는 tbody의 첫 행)에서 헤더 텍스트를 읽어
 * '제출 번호', '문제', '결과', '메모리', '시간', '언어'의 컬럼 인덱스(1-based) 맵을 반환한다.
 * @param {HTMLTableElement} table
 * @returns {Record<string, number> | null} { submissionId: 1, problemId: 3, ... } 또는 null
 */
function parseTableHeader(table) {
  const theadRow = table.querySelector("thead tr");
  const headerRow = theadRow || table.querySelector("tbody tr");
  if (!headerRow) return null;

  const cells = headerRow.querySelectorAll("th, td");
  const indexMap = {};

  for (let i = 0; i < cells.length; i++) {
    const text = (cells[i].textContent || "").trim();
    for (const [headerLabel, key] of Object.entries(HEADER_KEYS)) {
      if (text === headerLabel) {
        indexMap[key] = i; // 0-based 인덱스로 저장 (querySelectorAll 결과와 일치)
        break;
      }
    }
  }

  const required = [
    "submissionId",
    "problemId",
    "result",
    "memory",
    "time",
    "language",
  ];
  const hasAll = required.every((k) => indexMap[k] !== undefined);
  return hasAll ? indexMap : null;
}

/**
 * 숫자만 추출한다. "128 MB" → 128, "12 ms" → 12
 * @param {string} raw
 * @returns {number}
 */
function extractNumber(raw) {
  const digits = (raw || "").replace(/[^0-9]/g, "");
  const num = parseInt(digits, 10);
  return Number.isNaN(num) ? 0 : num;
}

function isBaekjoonStatusPage() {
  return (
    window.location.hostname === "www.acmicpc.net" &&
    window.location.pathname.startsWith("/status")
  );
}

function isRowAccepted(row, colMap) {
  const idx = colMap.result;
  const cells = row.querySelectorAll("td");
  const resultCell = cells[idx];
  if (!resultCell) return false;

  const text = (resultCell.textContent || "").trim();
  const hasAcText = text.includes(AC_TEXT_KEYWORD);
  const hasAcClass = resultCell.classList.contains(AC_CLASS_NAME);
  return hasAcText || hasAcClass;
}

function isRowFromCurrentUser(_row) {
  return true;
}

/**
 * 한 행에서 메타데이터 추출. colMap은 0-based 인덱스 맵.
 */
function extractSubmissionMeta(row, colMap) {
  const cells = row.querySelectorAll("td");
  if (!cells.length) return null;

  const get = (key) => {
    const i = colMap[key];
    return i !== undefined ? (cells[i].textContent || "").trim() : "";
  };

  const submissionId = get("submissionId");
  const problemId = get("problemId");
  const language = get("language");
  const timeRaw = get("time");
  const memoryRaw = get("memory");

  if (!submissionId || !problemId || !language) return null;

  const time = extractNumber(timeRaw);
  const memory = extractNumber(memoryRaw);

  return {
    submissionId,
    problemId,
    language,
    time,
    memory,
  };
}

/**
 * submissionId로 소스 코드를 다운로드한다.
 * @param {string} submissionId
 * @returns {Promise<string>}
 */
async function fetchSourceCode(submissionId) {
  const url = `https://www.acmicpc.net/source/download/${submissionId}`;
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) throw new Error(`Source download failed: ${res.status}`);
  return res.text();
}

/**
 * 채점 현황 테이블을 순회하며 새로운 AC 제출을 발견하면
 * 소스 코드를 다운로드한 뒤 meta에 합쳐 background로 전송한다.
 */
function pollStatusTable() {
  const table = document.querySelector(STATUS_TABLE_SELECTOR);
  if (!table) return;

  const colMap = parseTableHeader(table);
  if (!colMap) {
    console.warn("[AlgoNotion] status table header could not be parsed.");
    return;
  }

  const rows = table.querySelectorAll(TABLE_BODY_ROW_SELECTOR);
  // 헤더가 tbody 첫 행일 수 있으므로, th가 있는 행은 스킵
  rows.forEach((row) => {
    if (row.querySelector("th")) return; // 헤더 행 스킵
    if (!isRowFromCurrentUser(row)) return;
    if (!isRowAccepted(row, colMap)) return;

    const meta = extractSubmissionMeta(row, colMap);
    if (!meta) return;
    if (processedSubmissionIds.has(meta.submissionId)) return;

    processedSubmissionIds.add(meta.submissionId);

    (async () => {
      try {
        const code = await fetchSourceCode(meta.submissionId);
        const payload = { ...meta, code };

        const message = {
          type: "BAEKJOON_AC_SUBMISSION",
          payload,
        };
        chrome.runtime.sendMessage(message);
      } catch (err) {
        console.warn(
          "[AlgoNotion] Failed to fetch source for",
          meta.submissionId,
          err,
        );
        processedSubmissionIds.delete(meta.submissionId);
      }
    })();
  });
}

function startPolling() {
  if (pollingIntervalId !== null) return;
  pollingIntervalId = window.setInterval(pollStatusTable, 2000);
}

if (isBaekjoonStatusPage()) {
  startPolling();
}
