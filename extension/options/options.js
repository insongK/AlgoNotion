// AlgoNotion 옵션 페이지용 스크립트.
// - 백엔드 Webhook URL을 chrome.storage.sync에 저장/로드한다.

const BACKEND_URL_KEY = 'algonotion_backend_url';

const backendUrlInput = document.getElementById('backend-url');
const saveButton = document.getElementById('save-button');
const statusLabel = document.getElementById('status');

function showStatus(message) {
  if (!statusLabel) return;
  statusLabel.textContent = message;
  window.setTimeout(() => {
    statusLabel.textContent = '';
  }, 2000);
}

function restoreOptions() {
  chrome.storage.sync.get([BACKEND_URL_KEY], (result) => {
    if (backendUrlInput && typeof result[BACKEND_URL_KEY] === 'string') {
      backendUrlInput.value = result[BACKEND_URL_KEY];
    }
  });
}

function saveOptions() {
  if (!backendUrlInput) return;

  const url = backendUrlInput.value.trim();

  chrome.storage.sync.set(
    {
      [BACKEND_URL_KEY]: url,
    },
    () => {
      showStatus('설정이 저장되었습니다.');
    },
  );
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', restoreOptions);
} else {
  restoreOptions();
}

if (saveButton) {
  saveButton.addEventListener('click', saveOptions);
}

