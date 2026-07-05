// Thin API client — talks to the backend surfaces (M4 contract).
const API_BASE = import.meta.env.VITE_API_URL || "";

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

// Multimodal intake: a recorded scam-call clip or an SMS screenshot.
// The server transcribes/OCRs it, then returns the verdict + the transcript.
export const uploadFile = (file, channel, reporterId) => {
  const fd = new FormData();
  fd.append("file", file);
  if (channel) fd.append("channel", channel);
  if (reporterId) fd.append("reporter_id", reporterId);
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
