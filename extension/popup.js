const DEFAULT_WEB_PORT = 5173;
const DEFAULT_API_PORT = 8000;

const textEl = document.getElementById("text");
const resultEl = document.getElementById("result");
const errEl = document.getElementById("err");
const checkBtn = document.getElementById("checkBtn");
const scanPageBtn = document.getElementById("scanPageBtn");
const settingsToggle = document.getElementById("settingsToggle");
const settingsPanel = document.getElementById("settingsPanel");
const apiPortEl = document.getElementById("apiPort");
const webPortEl = document.getElementById("webPort");
const settingsSaveBtn = document.getElementById("settingsSave");

const BAND_COLORS = {
  confirmed: "#b91c1c",
  likely: "#b45309",
  suspicious: "#b45309",
  unrecognized: "#0369a1",
  safe: "#15803d",
};

function showResult(v) {
  errEl.classList.remove("show");
  resultEl.classList.add("show");
  const color = BAND_COLORS[v.band] || "#1e293b";
  resultEl.innerHTML = `
    <div class="band" style="color:${color}">${v.band_emoji || ""} ${v.band_label || "Checked"}</div>
    <div class="explain">${v.explanation || "No further detail available."}</div>
  `;
}

function showError(msg) {
  resultEl.classList.remove("show");
  errEl.classList.add("show");
  errEl.textContent = msg;
}

function runCheck(text) {
  text = (text || "").trim();
  if (!text) {
    showError("Nothing to check — paste some text first.");
    return;
  }
  checkBtn.disabled = true;
  checkBtn.textContent = "Checking…";
  chrome.runtime.sendMessage({ type: "antibody-scan", text }, (res) => {
    checkBtn.disabled = false;
    checkBtn.textContent = "Check it";
    if (!res) {
      showError("Couldn't reach the extension background service.");
      return;
    }
    if (res.ok) showResult(res.verdict);
    else showError(res.error || "Couldn't reach the Antibody server — is it running?");
  });
}

checkBtn.addEventListener("click", () => runCheck(textEl.value));

scanPageBtn.addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    showError("No active tab to scan.");
    return;
  }
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.body.innerText.slice(0, 4000),
    });
    textEl.value = result || "";
    runCheck(result);
  } catch (e) {
    showError("Can't read this page (browser internal pages are off-limits).");
  }
});

document.getElementById("openApp").addEventListener("click", async (e) => {
  e.preventDefault();
  const { webPort } = await chrome.storage.local.get("webPort");
  chrome.tabs.create({ url: `http://localhost:${webPort || DEFAULT_WEB_PORT}` });
});

// Settings: backend/web-app ports, so switching `uvicorn --port` or
// `vite --port` doesn't require editing extension source + reloading it.
settingsToggle.addEventListener("click", () => {
  settingsPanel.classList.toggle("show");
});

chrome.storage.local.get(["apiPort", "webPort"], ({ apiPort, webPort }) => {
  apiPortEl.value = apiPort || DEFAULT_API_PORT;
  webPortEl.value = webPort || DEFAULT_WEB_PORT;
});

settingsSaveBtn.addEventListener("click", async () => {
  const apiPort = parseInt(apiPortEl.value, 10) || DEFAULT_API_PORT;
  const webPort = parseInt(webPortEl.value, 10) || DEFAULT_WEB_PORT;
  await chrome.storage.local.set({ apiPort, webPort });
  settingsSaveBtn.textContent = "Saved ✓";
  setTimeout(() => (settingsSaveBtn.textContent = "Save"), 1200);
});
