/**
 * 수집한 데이터를 .cursorrules / 백엔드 WebhookPayload 스펙에 맞는 JSON 객체로 조립한다.
 * platform, meta_info, submission_info 구조.
 */

/** solved.ac level(1~30) → 티어 이름 */
const LEVEL_TIER_NAMES = [
  'Unrated', 'Bronze V', 'Bronze IV', 'Bronze III', 'Bronze II', 'Bronze I',
  'Silver V', 'Silver IV', 'Silver III', 'Silver II', 'Silver I',
  'Gold V', 'Gold IV', 'Gold III', 'Gold II', 'Gold I',
  'Platinum V', 'Platinum IV', 'Platinum III', 'Platinum II', 'Platinum I',
  'Diamond V', 'Diamond IV', 'Diamond III', 'Diamond II', 'Diamond I',
  'Ruby V', 'Ruby IV', 'Ruby III', 'Ruby II', 'Ruby I',
];

function levelToTierName(level) {
  if (level == null || level < 0 || level > 30) return null;
  return LEVEL_TIER_NAMES[level] || null;
}

/**
 * WebhookPayload 스펙에 맞는 객체를 생성한다.
 * @param {object} params
 * @param {string} params.platform - 예: "baekjoon"
 * @param {string} params.problemId - 백준 문제 번호
 * @param {string} params.title - 한글 제목 (solved.ac 또는 fallback)
 * @param {string|number|null} [params.level] - 티어 문자열 또는 solved.ac level 숫자(1~30)
 * @param {string} params.language - 정규화된 언어 (예: "python")
 * @param {string} params.code - 소스 코드 원문
 * @param {number} [params.time] - 실행 시간 (ms)
 * @param {number} [params.memory] - 메모리 (KB)
 * @returns {{ platform: string; meta_info: object; submission_info: object }}
 */
export function buildWebhookPayload({
  platform = 'baekjoon',
  problemId,
  title = '',
  level = null,
  language,
  code,
  time = null,
  memory = null,
}) {
  const link = `https://www.acmicpc.net/problem/${problemId}`;

  const tierName = typeof level === 'number' ? levelToTierName(level) : level;
  const meta_info = {
    title: title || `문제 ${problemId}`,
    problem_id: String(problemId),
    link,
    level: tierName != null ? String(tierName) : null,
    language,
  };

  const submission_info = {
    code,
    memory: memory != null ? Number(memory) : null,
    time: time != null ? Number(time) : null,
  };

  return {
    platform,
    meta_info,
    submission_info,
  };
}
