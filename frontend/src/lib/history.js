// Local "My Reports" history — no auth/reporter accounts exist yet, so this
// browser's own submitted checks are tracked client-side in localStorage.
const KEY = "antibody_my_reports";
const MAX_ENTRIES = 100;

export function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "[]");
  } catch {
    return [];
  }
}

export function addToHistory(entry) {
  const list = loadHistory();
  list.unshift({ ...entry, outcome: null, added_at: new Date().toISOString() });
  localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX_ENTRIES)));
}

export function updateHistoryOutcome(reportId, outcome) {
  const list = loadHistory();
  const idx = list.findIndex((r) => r.report_id === reportId);
  if (idx === -1) return;
  list[idx] = { ...list[idx], outcome };
  localStorage.setItem(KEY, JSON.stringify(list));
}
