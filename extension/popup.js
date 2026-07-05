const WEB_APP_URL = "http://localhost:5173";

const textEl = document.getElementById("text");
const resultEl = document.getElementById("result");
const errEl = document.getElementById("err");
const checkBtn = document.getElementById("checkBtn");
const scanPageBtn = document.getElementById("scanPageBtn");

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

document.getElementById("openApp").addEventListener("click", (e) => {
  e.preventDefault();
  chrome.tabs.create({ url: WEB_APP_URL });
});
