// Client-generated anonymous id — persisted per-browser so the backend's
// existing reporter_id plumbing (hashed before storage, never real PII) can
// recognize repeat visits without any login.
const KEY = "antibody_client_id";

export function getClientId() {
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    localStorage.setItem(KEY, id);
  }
  return id;
}
