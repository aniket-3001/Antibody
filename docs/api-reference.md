# API reference

Base URL: the service root (e.g. `http://localhost:8000` in dev, or the Cloud Run
URL in production). Interactive OpenAPI docs are served at `/docs` when the app is
running.

Every response carries an `X-Request-ID` header; every error shares one JSON shape
(see [Error envelope](#error-envelope)).

## Endpoints at a glance

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/report` | Submit a text report, get a verdict |
| `POST` | `/scan` | Read-only verdict — nothing recorded (browser extension) |
| `POST` | `/report/upload` | Submit a screenshot / audio / PDF, get a verdict |
| `GET` | `/report/{id}` | Re-fetch a prior verdict (shareable link) |
| `POST` | `/report/{id}/outcome` | Record what happened (strengthens the family) |
| `POST` | `/report/{id}/forget` | Prune a false positive out of the graph |
| `POST` | `/reporter/forget` | Hard-delete a browser's own data (real erasure) |
| `GET` | `/reports/mine` | A browser's own submitted reports |
| `GET` | `/leaderboard` | Community leaderboard by verified reports |
| `GET` | `/feed` | Trending families, recent reports, emerging campaigns |
| `GET` | `/families` | All known families + signatures + guidance |
| `GET` | `/graph` | Shared-tactic graph (nodes + edges) |
| `GET` | `/health` | Liveness + whether an LLM is configured |

---

## `POST /report`

Submit a message for assessment.

**Request**

```json
{ "text": "URGENT: your package needs a $2.99 redelivery fee, pay at http://usps-fee.biz",
  "channel": "sms",
  "reporter_id": "optional-anonymous-client-id" }
```

`channel` and `reporter_id` are optional. `reporter_id` is a client-generated
anonymous id; it is **hashed** server-side before storage and never stored raw.

**Response `200`** — the verdict object:

```jsonc
{
  "band": "confirmed",              // confirmed | likely | suspicious | unrecognized
  "band_label": "Confirmed scam",
  "band_emoji": "🔴",
  "confidence": 0.94,
  "family": "usps_redelivery_fee_scam",
  "family_display": "Usps Redelivery Fee Scam",
  "report_count": 12,
  "first_seen": "2026-06-30T10:12:00+00:00",
  "reasons": ["matches a known-bad url domain: usps-fee.biz", "independently reported 12× by the community"],
  "signals": { "indicator": 0.98, "semantic": 0.71, "structural": 0.6, "corroboration": 0.82, "family": 0.5 },
  "indicators": [{ "kind": "url_domain", "value": "usps-fee.biz" }],
  "tactics": ["fake_delivery_fee", "urgency_pressure"],
  "lures": ["package_delivery"],
  "highlights": [{ "start": 0, "end": 6, "kind": "tactic", "label": "urgency_pressure" }],
  "explanation": "This matches the usps redelivery fee scam pattern. ...",
  "explanation_source": "cognee_graph",   // or "fallback"
  "citations": [{ "snippet": "...", "ref": "chunk 3", "doc": "..." }],
  "guidance": { "do_now": [...], "report_to": [...], "recovery": [...] },
  "shared_tactics": [{ "tactic": "urgency_pressure", "also_used_by": ["tech_support_refund_scam"] }],
  "report_id": "rep_ab12cd34ef56"
}
```

**Errors** — `400 empty_report` if `text` is blank; `422 validation_error` if `text`
is missing.

```bash
curl -s http://localhost:8000/report \
  -H 'Content-Type: application/json' \
  -d '{"text":"pay a small redelivery fee at usps-fee.biz","channel":"sms"}'
```

## `POST /scan`

Read-only verdict — the **same engine as `/report`**, but it never records a
report or touches trust/leaderboard. Backs the browser extension, where scanning
a page shouldn't silently add it to the shared graph.

**Request**: `{ "text": "…", "channel": "sms" }` (channel optional).
**Response `200`**: the verdict object, **without** a `report_id` (nothing was recorded).
**Errors**: `400 empty_report`.

```bash
curl -s http://localhost:8000/scan -H 'Content-Type: application/json' \
  -d '{"text":"pay a redelivery fee at usps-fee.biz"}'
```

## `GET /report/{id}`

Re-fetch a prior verdict by id — backs the "Warn Others" **shareable link**
(`?v=<id>` on the web app). It re-runs `assess()` on the stored text rather than
caching the original verdict, so a shared link always reflects current
family/corroboration data.

**Response `200`**: the verdict object (with `report_id`, `transcript`, `input_kind`).
**Errors**: `404 report_not_found` (unknown or pruned).

## `POST /report/upload`

Multimodal intake. `multipart/form-data` with `file` (required) and optional
`channel` / `reporter_id`. Images are OCR'd, audio is transcribed, PDFs are read —
all best-effort and locally, and the raw file is always handed to Cognee's native
loaders. Returns the same verdict object plus `transcript` (what was extracted) and
`input_kind` (`image` | `audio` | `document`). If nothing could be extracted, returns
an `unrecognized` verdict explaining that the raw file was still added to the graph.

```bash
curl -s http://localhost:8000/report/upload \
  -F file=@scam_screenshot.png -F channel=sms
```

## `POST /report/{id}/outcome`

Record what actually happened. This is the **improve** loop: a confirmed outcome
raises reporter trust and reinforces the family; confirming a previously
*unrecognized* report **promotes it to a new family** so the next person is warned.

**Request**: `{ "outcome": "confirmed_scam" }` — one of `confirmed_scam`,
`i_got_scammed`, `actually_legit`.

**Response `200`**: `{ "ok": true, "family": "usps_redelivery_fee_scam", "outcome": "confirmed_scam" }`

**Errors**: `404 report_not_found`.

## `POST /report/{id}/forget`

Prune a false positive. Soft-deletes the report from the ops store (stops it poisoning
semantic matches), rebuilds the semantic index, and scopes a Cognee `forget()` to that
exact document in the background.

**Response `200`**: `{ "ok": true, "pruned": "rep_ab12cd34ef56" }`

## `POST /reporter/forget`

**Real erasure** (§10) for a browser's own anonymous id — hard-deletes its
reporter row and every report it filed from the ops DB, and scopes a Cognee
`forget()` against the graph for each report that reached it. Distinct from
`/report/{id}/forget`, which soft-prunes a single false-positive report.

**Request**: `{ "reporter_id": "<anonymous client id>" }`
**Response `200`**: `{ "ok": true, "deleted_reports": 3 }`

Because reporter identity lives only in the ops DB (never the graph), this is a
normal `DELETE`, not graph surgery — see
[Security & privacy](security-and-privacy.md#2-privacy-by-construction-de-identified-graph).

## `GET /reports/mine?reporter_id=...`

A browser's own reports, keyed by its anonymous client id (hashed the same way as at
submit time). Returns `{ "reports": [{ id, date, text, channel, family, status, points }] }`
where `status` is `confirmed` | `legit` | `pending`.

## `GET /leaderboard?limit=20&reporter_id=...`

Community leaderboard ranked by *verified* reports (not raw volume — see the
anti-poisoning model in [Security & privacy](security-and-privacy.md)). Reporters are
anonymous; the caller's own row is marked `is_you`. Returns
`{ "leaderboard": [{ rank, label, is_you, points, verified, tier }] }`.

## `GET /feed`

The live threat feed:

```jsonc
{
  "total_reports": 128,
  "families": [{ "name": "...", "display": "...", "count": 12, "first_seen": "...",
                 "hours_since_last": 3.2, "tactics": [...] }],
  "recent":  [{ "id": "...", "preview": "...", "channel": "sms", "family": "...",
                "reported_at": "...", "outcome": null }],
  "shared_tactics": [{ "tactic": "urgency_pressure", "families": ["...", "..."] }],
  "emerging": [{ "name": "...", "display": "...", "count": 4, "emerged_hours_ago": 18.0 }]
}
```

## `GET /families`

All known families with signatures + guidance, sorted by report count:
`{ "families": [{ name, display, summary, tactics, lures, channels, first_seen,
last_seen, report_count, guidance }] }`.

## `GET /graph`

The shared-tactic knowledge graph for visualization/traversal. Nodes are `family`,
`tactic`, or `lure`; a tactic used by ≥2 families is coloured as shared. Shape:
`{ "nodes": [{ id, label, type, color, props }], "edges": [{ id, from, to, label, props }] }`.

## `GET /health`

```json
{ "status": "ok", "env": "dev", "llm": false, "version": "0.1.0" }
```

Used by Cloud Run / Render as the liveness probe. `llm` reflects whether an LLM key
is configured.

---

## Error envelope

Every error — typed, validation, or unexpected — returns the same shape:

```json
{ "error": "empty_report",
  "message": "Empty report — nothing to assess.",
  "request_id": "a1b2c3d4",
  "path": "/report" }
```

| `error` | Status | Meaning |
|---|---|---|
| `empty_report` | 400 | Report text was blank |
| `bad_request` | 400 | Malformed request |
| `report_not_found` | 404 | Unknown report id |
| `validation_error` | 422 | Request body failed schema validation |
| `http_error` | 4xx | Unknown route / other HTTP error |
| `internal_error` | 500 | Unexpected server fault (message hidden outside dev) |

`request_id` matches the `X-Request-ID` response header and the server logs, so a
user-reported failure is one grep away from its stack trace. See
[`api/core/`](../api/core/) for the implementation.
