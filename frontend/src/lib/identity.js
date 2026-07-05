// Client-generated anonymous id — persisted per-browser so the backend's
// existing reporter_id plumbing (hashed before storage, never real PII) can
// recognize repeat visits without any login.
const KEY = "antibody_client_id";

function newId() {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getClientId() {
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = newId();
    localStorage.setItem(KEY, id);
  }
  return id;
}

// Rotates to a fresh anonymous id. Call after the backend has forgotten the
// old one (see forgetReporter in api.js) — otherwise this browser would just
// keep talking to the server under its old, still-remembered identity.
export function resetClientId() {
  const id = newId();
  localStorage.setItem(KEY, id);
  return id;
}
