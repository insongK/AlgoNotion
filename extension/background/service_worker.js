// content script로부터 전달되는 메시지를 수신하는 Service Worker 뼈대.
// 추후 여기에 Baekjoon 소스 다운로드, solved.ac 호출, 백엔드 웹훅 전송 로직을 추가한다.

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // 메시지 타입에 따라 분기할 수 있도록 switch 구문을 사용한다.
  switch (message?.type) {
    case 'BAEKJOON_AC_SUBMISSION': {
      const payload = message.payload || {};

      // TODO: 여기에서 Baekjoon 소스 코드 다운로드 → solved.ac 메타데이터 조회 →
      //       언어 정규화 → 백엔드 웹훅 호출 로직을 순차적으로 연결할 예정.
      // 현재는 전달된 payload를 예쁘게 로그로만 출력한다.
      // eslint-disable-next-line no-console
      console.log('[AlgoNotion][BAEKJOON_AC_SUBMISSION]', {
        from: sender?.tab?.url,
        submissionId: payload.submissionId,
        problemId: payload.problemId,
        language: payload.language,
        time: payload.time,
        memory: payload.memory,
      });

      break;
    }
    default:
      // 다른 타입의 메시지는 현재는 처리하지 않고 무시한다.
      break;
  }

  // async sendResponse를 사용하지 않으므로 false를 반환해 리스너 수명을 종료한다.
  return false;
});

