# Antibody — what it is and how it works

Antibody is a collective-immune-system scam checker. When someone pastes a
suspicious message, uploads a screenshot, or plays a scam-call recording, the
app assesses it against a shared graph of previously-reported scam patterns
and returns a verdict: confirmed, likely, suspicious, unrecognized, or safe.

## Core features

- **Check a message**: paste text, upload an image (OCR'd), a PDF, or an
  audio clip (transcribed). Antibody returns a band, a confidence score, and
  an explanation with citations back to similar past reports.
- **Feed**: a live view of what's being reported right now, plus "emerging
  threats" — families of scam that are picking up velocity.
- **Knowledge graph**: a visual view of tactics, lures, and scam families and
  how they connect.
- **Leaderboard**: ranks anonymous reporters by verified reports. Confirming
  a scam or getting scammed raises your trust score; marking something
  "actually legit" lowers it slightly.
- **My Reports**: a reporter's own submission history, keyed off a
  browser-generated anonymous id (never a real identity). Click any report to
  open its full verdict, record an outcome, and see whether it has been folded
  into the shared knowledge graph yet.
- **Help Center**: an interactive chatbot (this one) that answers questions
  about Antibody from a local Markdown knowledge base (`help_docs/`), including
  how to recover after a scam.
- **Browser extension**: a popup + right-click "Check with Antibody" that
  calls the same read-only /scan endpoint — scanning a page never adds it to
  the shared graph, only /report does that.

## Performance & caching

When a report is submitted, its full verdict is cached as JSON inside the
SQLite operational store (which runs in WAL mode so background graph writes
never block readers). Re-opening a report — from a shareable link or the My
Reports view — serves that cached verdict instantly, with zero additional LLM
calls (denial-of-wallet protection). The React frontend also lazy-mounts its
tabs and keeps them alive, so switching between checking a message and
chatting with the Help Center never loses your place or in-progress input.

## Anonymous identity

Every browser gets a random client id (a UUID) stored locally. The backend
only ever stores a one-way hash of it (`"r_" + sha256(id)[:16]`), never the
raw id. You can copy your id or reset it from the sidebar's "Your anonymous
id" panel — resetting hard-deletes your old id's reports and trust score from
the server and gives you a fresh one.

## Troubleshooting

- **"Unexpected token '<' is not valid JSON"**: this means the frontend tried
  to parse an HTML page as JSON — almost always a dev-proxy misconfiguration
  in `frontend/vite.config.js` (a new backend route added without a matching
  proxy entry). Check the proxy list covers every route the frontend calls.
- **Leaderboard/My Reports show nothing**: these are scoped to your anonymous
  id. If you just reset your id, your history starts over — this is expected,
  not a bug.
- **Verdict has no cited explanation**: the deterministic + semantic matching
  engine always produces a verdict band even without an LLM key configured;
  the "cited explanation" step specifically needs Cognee's GRAPH_COMPLETION,
  which needs an LLM key. No key means a template explanation instead of a
  cited one — the verdict itself is unaffected.
- **A report should be removed (false positive)**: `/report/{id}/forget`
  soft-prunes a single report (keeps it in the audit trail but stops it
  poisoning future matches). For a reporter's own full erasure, use "Forget
  me" in the sidebar — that's a hard delete of every report tied to that id.
