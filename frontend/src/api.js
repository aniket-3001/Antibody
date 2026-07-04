// Thin API client — talks to the backend surfaces (M4 contract).
const j = async (r) => {
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
};

export const checkMessage = (text, channel) =>
  fetch("/report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, channel }),
  }).then(j);

// Multimodal intake: a recorded scam-call clip or an SMS screenshot.
// The server transcribes/OCRs it, then returns the verdict + the transcript.
export const uploadFile = (file, channel) => {
  const fd = new FormData();
  fd.append("file", file);
  if (channel) fd.append("channel", channel);
  return fetch("/report/upload", { method: "POST", body: fd }).then(j);
};

export const submitOutcome = (reportId, outcome) =>
  fetch(`/report/${reportId}/outcome`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ outcome }),
  }).then(j);

export const forgetReport = (reportId) =>
  fetch(`/report/${reportId}/forget`, { method: "POST" }).then(j);

export const getFeed = () => fetch("/feed").then(j);
export const getFamilies = () => fetch("/families").then(j);
export const getGraph = () => fetch("/graph").then(j);
