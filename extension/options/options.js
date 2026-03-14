const BACKEND_URL_KEY = 'algonotion_backend_url';
const NOTION_TOKEN_KEY = 'algonotion_notion_token';
const NOTION_DATABASE_ID_KEY = 'algonotion_notion_database_id';

const backendUrlInput = document.getElementById('backend-url');
const notionTokenInput = document.getElementById('notion-token');
const notionDatabaseIdInput = document.getElementById('notion-database-id');
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
  chrome.storage.sync.get(
    [BACKEND_URL_KEY, NOTION_TOKEN_KEY, NOTION_DATABASE_ID_KEY],
    (result) => {
      if (backendUrlInput && typeof result[BACKEND_URL_KEY] === 'string') {
        backendUrlInput.value = result[BACKEND_URL_KEY];
      }
      if (notionTokenInput && typeof result[NOTION_TOKEN_KEY] === 'string') {
        notionTokenInput.value = result[NOTION_TOKEN_KEY];
      }
      if (notionDatabaseIdInput && typeof result[NOTION_DATABASE_ID_KEY] === 'string') {
        notionDatabaseIdInput.value = result[NOTION_DATABASE_ID_KEY];
      }
    },
  );
}

function saveOptions() {
  if (!backendUrlInput) return;

  const url = backendUrlInput.value.trim();
  const notionToken = notionTokenInput ? notionTokenInput.value.trim() : '';
  const notionDatabaseId = notionDatabaseIdInput ? notionDatabaseIdInput.value.trim() : '';

  chrome.storage.sync.set(
    {
      [BACKEND_URL_KEY]: url,
      [NOTION_TOKEN_KEY]: notionToken,
      [NOTION_DATABASE_ID_KEY]: notionDatabaseId,
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
