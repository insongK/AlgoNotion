// Content script로부터 전달되는 메시지 수신 → 소스 확인 후 solved.ac 보강 → 웹훅 전송
import { fetchSolvedAcProblem, postToBackendWebhook } from '../scripts/api_client.js';
import { normalizeLanguage } from '../scripts/language_normalizer.js';
import { buildWebhookPayload } from '../scripts/payload_builder.js';

const DEFAULT_WEBHOOK_BASE = 'http://localhost:8000';

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[AlgoNotion] Message received in background:', {
    type: message?.type,
    senderUrl: sender?.tab?.url,
    payloadKeys: Object.keys(message?.payload || {}),
    submissionId: message?.payload?.submissionId,
    problemId: message?.payload?.problemId,
    codeLength: typeof message?.payload?.code === 'string' ? message.payload.code.length : null,
    codePreview: typeof message?.payload?.code === 'string' ? message.payload.code.slice(0, 120) : null,
  });

  switch (message?.type) {
    case 'BAEKJOON_AC_SUBMISSION': {
      const payload = message.payload || {};

      if (!payload.code) {
        console.warn('[AlgoNotion] BAEKJOON_AC_SUBMISSION payload has no code, skip.', {
          submissionId: payload.submissionId,
          problemId: payload.problemId,
          payload,
        });
        return false;
      }

      (async () => {
        try {
          console.log('[AlgoNotion] ─── AC 제출 처리 시작 ───');
          console.log('[AlgoNotion] from:', sender?.tab?.url);
          console.log('[AlgoNotion] submissionId:', payload.submissionId, 'problemId:', payload.problemId);

          // 1) solved.ac에서 문제 제목·티어 조회
          let titleKo = '';
          let level = null;
          try {
            console.log('[AlgoNotion] [1/4] solved.ac API 호출 중...');
            const solved = await fetchSolvedAcProblem(payload.problemId);
            titleKo = solved.titleKo;
            level = solved.level;
            console.log('[AlgoNotion] [1/4] solved.ac OK → titleKo:', titleKo || '(없음)', 'level:', level);
          } catch (e) {
            console.warn('[AlgoNotion] [1/4] solved.ac 실패 (계속 진행):', e.message);
          }

          // 2) 언어 정규화
          console.log('[AlgoNotion] [2/4] 언어 정규화... raw:', payload.language);
          const language = normalizeLanguage(payload.language);
          console.log('[AlgoNotion] [2/4] 정규화된 언어:', language);

          // 3) WebhookPayload 조립
          console.log('[AlgoNotion] [3/4] WebhookPayload 조립 중...');
          const webhookPayload = buildWebhookPayload({
            platform: 'baekjoon',
            problemId: payload.problemId,
            title: titleKo,
            level,
            language,
            code: payload.code,
            time: payload.time,
            memory: payload.memory,
          });
          console.log('[AlgoNotion] [3/4] payload 준비 완료 (meta_info.title:', webhookPayload.meta_info.title, ')');

          // 4) 백엔드 웹훅 전송
          const baseUrl = await getWebhookBaseUrl();
          const webhookUrl = baseUrl.replace(/\/?$/, '');
          console.log('[AlgoNotion] [4/4] 백엔드 전송 →', webhookUrl + '/webhook');
          await postToBackendWebhook(webhookUrl, webhookPayload);
          console.log('[AlgoNotion] [4/4] 백엔드 전송 완료.');
          console.log('[AlgoNotion] ─── AC 제출 처리 완료 ───');
        } catch (err) {
          console.error('[AlgoNotion] ─── AC 제출 처리 실패 ───');
          console.error('[AlgoNotion]', err.message);
          console.error(err);
        }
      })();

      return false;
    }
    default:
      break;
  }
  return false;
});

/**
 * 옵션에서 저장한 백엔드 URL을 반환한다. 없으면 기본값.
 * @returns {Promise<string>}
 */
async function getWebhookBaseUrl() {
  try {
    const st = await chrome.storage.sync.get('backendUrl');
    return (st.backendUrl && st.backendUrl.trim()) ? st.backendUrl.trim() : DEFAULT_WEBHOOK_BASE;
  } catch {
    return DEFAULT_WEBHOOK_BASE;
  }
}
