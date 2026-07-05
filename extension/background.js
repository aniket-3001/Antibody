// The real backend the marketing mockup only pretended to call. Requests are
// made here (not in a content script) so Chrome's extension host_permissions
// grant applies — content-script fetches are still bound by the page's own
// CORS, but background/popup fetches from a permitted origin are not.
const API_BASE = "http://127.0.0.1:8000";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "antibody-check-selection",
    title: 'Check "%s" with Antibody',
    contexts: ["selection"],
  });
});

async function scanText(text) {
  const res = await fetch(`${API_BASE}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

chrome.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId !== "antibody-check-selection" || !info.selectionText) return;
  try {
    const v = await scanText(info.selectionText);
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icon128.png",
      title: `${v.band_emoji || "🔍"} ${v.band_label || "Checked"}`,
      message: v.explanation || "No further detail available — try the full app for a breakdown.",
      priority: v.band === "confirmed" ? 2 : 0,
    });
  } catch (e) {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icon128.png",
      title: "Antibody — couldn't check that",
      message: String(e.message || e),
    });
  }
});

// Popup relays through here so both entry points (right-click, popup) share
// one fetch/error path instead of duplicating API_BASE handling twice.
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type !== "antibody-scan") return;
  scanText(msg.text)
    .then((verdict) => sendResponse({ ok: true, verdict }))
    .catch((e) => sendResponse({ ok: false, error: String(e.message || e) }));
  return true; // keep the message channel open for the async response
});
