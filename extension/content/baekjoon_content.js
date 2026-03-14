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

const SOURCE_FETCH_MAX_RETRIES = 5;
const SOURCE_FETCH_RETRY_DELAYS_MS = [1000, 1500, 2500, 4000, 6000];

const processedSubmissionIds = new Set();
const uploadButtonStateBySubmissionId = new Map();
let pollingIntervalId = null;

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

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

function isBaekjoonSubmitPage() {
  return (
    window.location.hostname === "www.acmicpc.net" &&
    window.location.pathname.startsWith("/submit/")
  );
}

function extractTextFromElement(el) {
  if (!el) return "";
  if ("value" in el && typeof el.value === "string") {
    return el.value;
  }
  return (el.textContent || "").trim();
}

function extractCodeFromCodeMirror(root) {
  if (!root) return "";
  const lines = root.querySelectorAll(".CodeMirror-line, .cm-line");
  if (!lines.length) return "";
  return Array.from(lines)
    .map((line) => line.textContent || "")
    .join("\n")
    .trim();
}

function extractCodeFromAce(root) {
  if (!root) return "";
  const lines = root.querySelectorAll(".ace_line");
  if (!lines.length) return "";
  return Array.from(lines)
    .map((line) => line.textContent || "")
    .join("\n")
    .trim();
}

function extractSubmitPageCodeFromDocument(root = document) {
  const directSelectors = [
    "textarea#source",
    "textarea[name='source']",
    "#source",
    "pre.prettyprint",
    "pre code",
    ".source-code",
  ];

  for (const selector of directSelectors) {
    const el = root.querySelector(selector);
    const text = extractTextFromElement(el);
    if (text.trim()) {
      return text;
    }
  }

  const codeMirrorRoot = root.querySelector(".CodeMirror");
  const codeMirrorText = extractCodeFromCodeMirror(codeMirrorRoot);
  if (codeMirrorText) {
    return codeMirrorText;
  }

  const aceRoot = root.querySelector(".ace_editor");
  const aceText = extractCodeFromAce(aceRoot);
  if (aceText) {
    return aceText;
  }

  return "";
}

function extractSubmitPageCode() {
  return extractSubmitPageCodeFromDocument(document);
}

function extractSubmitPageMeta() {
  const match = window.location.pathname.match(/^\/submit\/(\d+)\/(\d+)/);
  if (!match) return null;

  const [, problemId, submissionId] = match;
  const languageSelect =
    document.querySelector("select#language") ||
    document.querySelector("select[name='language']");
  const selectedLanguage =
    languageSelect?.selectedOptions?.[0]?.textContent ||
    languageSelect?.value ||
    "";

  return {
    submissionId,
    problemId,
    language: selectedLanguage.trim(),
    time: null,
    memory: null,
  };
}

async function fetchSourceCodeFromSubmitPage(problemId, submissionId) {
  const url = `https://www.acmicpc.net/submit/${problemId}/${submissionId}`;
  console.log("[AlgoNotion] Fetching submit page fallback:", { problemId, submissionId, url });

  const res = await fetch(url, {
    credentials: "include",
    cache: "no-store",
  });
  const html = await res.text();

  console.log("[AlgoNotion] Submit page fallback response:", {
    problemId,
    submissionId,
    status: res.status,
    ok: res.ok,
    redirected: res.redirected,
    finalUrl: res.url,
    contentType: res.headers.get("content-type"),
    htmlLength: html.length,
    htmlPreview: html.slice(0, 120),
  });

  if (!res.ok) {
    throw new Error(`Submit page fetch failed: ${res.status}`);
  }

  const parsed = new DOMParser().parseFromString(html, "text/html");
  const code = extractSubmitPageCodeFromDocument(parsed);

  console.log("[AlgoNotion] Submit page fallback extraction:", {
    problemId,
    submissionId,
    codeLength: code.length,
    codePreview: code.slice(0, 120),
  });

  if (!code.trim()) {
    throw new Error("Submit page fallback returned an empty code body");
  }

  return code;
}

function sendSubmissionMessage(meta, code, source) {
  const payload = { ...meta, code };
  console.log("[AlgoNotion] Sending message to background:", {
    source,
    submissionId: meta.submissionId,
    codeLength: code.length,
    codePreview: code.slice(0, 120),
  });

  chrome.runtime.sendMessage({
    type: "BAEKJOON_AC_SUBMISSION",
    payload,
  });
}

function sendSubmissionMessageAsync(meta, code, source) {
  return new Promise((resolve, reject) => {
    const payload = { ...meta, code };
    console.log("[AlgoNotion] Sending message to background:", {
      source,
      submissionId: meta.submissionId,
      codeLength: code.length,
      codePreview: code.slice(0, 120),
    });

    chrome.runtime.sendMessage(
      {
        type: "BAEKJOON_AC_SUBMISSION",
        payload,
      },
      (response) => {
        const runtimeError = chrome.runtime.lastError;
        if (runtimeError) {
          reject(new Error(runtimeError.message));
          return;
        }

        if (!response?.ok) {
          reject(new Error(response?.error || "Unknown background error"));
          return;
        }

        resolve(response);
      },
    );
  });
}

function getUploadButtonState(submissionId) {
  return uploadButtonStateBySubmissionId.get(submissionId) || "idle";
}

function setUploadButtonState(submissionId, state) {
  uploadButtonStateBySubmissionId.set(submissionId, state);
}

function ensureUploadButton(row, meta, colMap) {
  const cells = row.querySelectorAll("td");
  const resultCell = cells[colMap.result];
  if (!resultCell) return;
  if (resultCell.querySelector(".algonotion-upload-btn")) return;

  const button = document.createElement("button");
  button.type = "button";
  button.className = "algonotion-upload-btn";
  button.textContent = "Notion 업로드";
  button.style.marginLeft = "8px";
  button.style.padding = "2px 8px";
  button.style.fontSize = "12px";
  button.style.cursor = "pointer";
  button.style.border = "1px solid #2b6cb0";
  button.style.borderRadius = "4px";
  button.style.background = "#fff";
  button.style.color = "#2b6cb0";

  const syncButtonUI = () => {
    const state = getUploadButtonState(meta.submissionId);
    if (state === "uploading") {
      button.disabled = true;
      button.textContent = "업로드 중...";
      return;
    }
    if (state === "done") {
      button.disabled = true;
      button.textContent = "업로드 완료";
      button.style.borderColor = "#2f855a";
      button.style.color = "#2f855a";
      return;
    }
    if (state === "failed") {
      button.disabled = false;
      button.textContent = "다시 업로드";
      button.style.borderColor = "#c53030";
      button.style.color = "#c53030";
      return;
    }

    button.disabled = false;
    button.textContent = "Notion 업로드";
    button.style.borderColor = "#2b6cb0";
    button.style.color = "#2b6cb0";
  };

  button.addEventListener("click", async (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (getUploadButtonState(meta.submissionId) === "uploading") return;

    try {
      setUploadButtonState(meta.submissionId, "uploading");
      syncButtonUI();

      let code;
      try {
        console.log("[AlgoNotion] Trying submit page fallback first.", {
          submissionId: meta.submissionId,
          problemId: meta.problemId,
        });
        code = await fetchSourceCodeFromSubmitPage(meta.problemId, meta.submissionId);
      } catch (submitErr) {
        console.warn("[AlgoNotion] Submit page fallback failed, trying source download path.", {
          submissionId: meta.submissionId,
          problemId: meta.problemId,
          message: submitErr?.message || String(submitErr),
        });
        code = await fetchSourceCode(meta.submissionId);
      }

      await sendSubmissionMessageAsync(meta, code, "status-page-button");
      processedSubmissionIds.add(meta.submissionId);
      setUploadButtonState(meta.submissionId, "done");
      syncButtonUI();
    } catch (err) {
      console.warn(
        "[AlgoNotion] Failed to fetch source for",
        meta.submissionId,
        err?.message || err,
      );
      console.error("[AlgoNotion] Source fetch error detail:", err);
      setUploadButtonState(meta.submissionId, "failed");
      syncButtonUI();
    }
  });

  resultCell.appendChild(button);
  syncButtonUI();
}

function processSubmitPage() {
  const meta = extractSubmitPageMeta();
  if (!meta) {
    console.warn("[AlgoNotion] Submit page meta could not be parsed.");
    return;
  }

  const code = extractSubmitPageCode();
  console.log("[AlgoNotion] Submit page helper ready:", {
    submissionId: meta.submissionId,
    problemId: meta.problemId,
    language: meta.language,
    codeLength: code.length,
  });
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
  let lastError = null;

  for (let attempt = 1; attempt <= SOURCE_FETCH_MAX_RETRIES; attempt++) {
    console.log("[AlgoNotion] Fetching source code:", { submissionId, url, attempt });

    try {
      const res = await fetch(url, {
        credentials: "include",
        cache: "no-store",
      });
      const text = await res.text();
      const trimmed = text.trim();
      const contentType = res.headers.get("content-type");
      const isHtmlResponse =
        contentType?.includes("text/html") ||
        /^<!doctype html/i.test(trimmed) ||
        /^<html/i.test(trimmed);

      console.log("[AlgoNotion] Source response:", {
        submissionId,
        attempt,
        status: res.status,
        ok: res.ok,
        redirected: res.redirected,
        finalUrl: res.url,
        contentType,
      });

      console.log("[AlgoNotion] Source body:", {
        submissionId,
        attempt,
        length: text.length,
        preview: text.slice(0, 120),
      });

      if (!res.ok) {
        throw new Error(`Source download failed: ${res.status}`);
      }

      if (!trimmed) {
        throw new Error("Source download returned an empty body");
      }

      if (isHtmlResponse) {
        throw new Error("Source download returned HTML instead of source code");
      }

      return text;
    } catch (err) {
      lastError = err;
      console.warn("[AlgoNotion] Source fetch attempt failed:", {
        submissionId,
        attempt,
        message: err?.message || String(err),
      });

      if (attempt < SOURCE_FETCH_MAX_RETRIES) {
        await sleep(SOURCE_FETCH_RETRY_DELAYS_MS[attempt - 1] ?? 3000);
      }
    }
  }

  throw lastError || new Error("Source fetch failed for an unknown reason");
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
    console.log("[AlgoNotion] Accepted row found:", meta);
    ensureUploadButton(row, meta, colMap);
  });
}

function startPolling() {
  if (pollingIntervalId !== null) return;
  pollingIntervalId = window.setInterval(pollStatusTable, 2000);
}

if (isBaekjoonStatusPage()) {
  console.log("[AlgoNotion] Content script active on status page.");
  startPolling();
} else if (isBaekjoonSubmitPage()) {
  console.log("[AlgoNotion] Content script active on submit page.");
  processSubmitPage();
}
