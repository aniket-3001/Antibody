// Thin API client — talks to the backend surfaces (M4 contract).
const API_BASE = import.meta.env.VITE_API_URL || "";
// Help chatbot is a separate process/port (see help_api/) — proxied under
// /help by vite.config.js locally, routed to its own service in prod.
const HELP_API_BASE = import.meta.env.VITE_HELP_API_URL || "";

const j = async (r) => {
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
};

export const checkMessage = (text, channel, reporterId) =>
  fetch(`${API_BASE}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, channel, reporter_id: reporterId }),
  }).then(j);

// Extract text from a file without evaluating it — powers the upload preview,
// so the user can see/edit the OCR'd or transcribed text before checking it.
export const extractText = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return fetch(`${API_BASE}/report/extract`, { method: "POST", body: fd }).then(j);
};

// Multimodal intake: a recorded scam-call clip or an SMS screenshot.
// The server transcribes/OCRs it, then returns the verdict + the transcript.
// transcriptOverride lets the caller submit user-edited preview text instead
// of re-running OCR/transcription server-side.
export const uploadFile = (file, channel, reporterId, transcriptOverride = null) => {
  const fd = new FormData();
  fd.append("file", file);
  if (channel) fd.append("channel", channel);
  if (reporterId) fd.append("reporter_id", reporterId);
  if (transcriptOverride !== null) fd.append("transcript_override", transcriptOverride);
  return fetch(`${API_BASE}/report/upload`, { method: "POST", body: fd }).then(j);
};

export const getReport = (reportId) =>
  fetch(`${API_BASE}/report/${reportId}`).then(j);

export const submitOutcome = (reportId, outcome) =>
  fetch(`${API_BASE}/report/${reportId}/outcome`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ outcome }),
  }).then(j);

export const forgetReport = (reportId) =>
  fetch(`${API_BASE}/report/${reportId}/forget`, { method: "POST" }).then(j);

export const getFeed = () => fetch(`${API_BASE}/feed`).then(j);
export const getFamilies = () => fetch(`${API_BASE}/families`).then(j);
export const getGraph = () => fetch(`${API_BASE}/graph`).then(j);

export const getMyReports = (reporterId) =>
  fetch(`${API_BASE}/reports/mine?reporter_id=${encodeURIComponent(reporterId)}`).then(j);

export const getLeaderboard = (reporterId) =>
  fetch(`${API_BASE}/leaderboard?reporter_id=${encodeURIComponent(reporterId)}`).then(j);

export const forgetReporter = (reporterId) =>
  fetch(`${API_BASE}/reporter/forget`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reporter_id: reporterId }),
  }).then(j);

export const askHelp = (question, history = []) =>
  fetch(`${HELP_API_BASE}/help/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
  }).then(j);
