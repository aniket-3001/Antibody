# Antibody

[![CI](https://github.com/aniket-3001/Antibody/actions/workflows/ci.yml/badge.svg)](https://github.com/aniket-3001/Antibody/actions/workflows/ci.yml)

A collective immune system against scams. People forward a text, screenshot, or
voice-call recording; Antibody matches it against a shared memory graph of known
scam campaigns and gives back a verdict, an explanation, and what to do next.
Every report that comes in — confirmed or false-positive — makes the graph a
little smarter for the next person.

**Live demo:** _coming soon — see [Deployment](#deployment)._

Built around [Cognee](https://github.com/topoteretes/cognee) as the memory
layer: reports are `add()`-ed and `cognify()`-ed into a shared knowledge graph,
`search(GRAPH_COMPLETION)` finds cited matches, `improve`/`memify` strengthen a
family after a confirmed outcome, and `forget` prunes false positives back out.

## How it works

1. **Intake** (`api/intake/`) — text, SMS screenshots, or scam-call audio come
   in via `POST /report` / `POST /report/upload`. Loaders OCR/transcribe raw
   files; a deterministic pass pulls out indicators (URLs, phone numbers,
   wallet addresses) and candidate tactics.
2. **Memory** (`api/memory/`) — the only layer that talks to Cognee. Reports
   are cognified against a shared ontology (`ontology.py`) where `Tactic` and
   `Lure` nodes are shared across scam families, so the graph can answer
   "this campaign uses the same fake-fee tactic as that one."
3. **Verdict** (`api/verdict/`) — a transparent, rule-based confidence engine
   (`engine.py`) fuses indicator match, semantic similarity, structural tactic
   overlap, and community corroboration into one of four bands:

   | Band | Trigger |
   |---|---|
   | 🔴 Confirmed | exact match on a known-bad indicator (URL/phone/wallet) |
   | 🟠 Likely | strong semantic/structural match + ≥3 corroborating reports |
   | 🟡 Suspicious | weak/semantic-only match |
   | 🟢 Unrecognized | no meaningful match — safety tips only |

   The gate is asymmetric by design: a legitimate message can never be
   hard-accused, only an exact indicator match can.
4. **Feed** (`api/feed/`) — `GET /feed`, `GET /families`, `GET /graph` surface
   trending families and the shared-tactic graph for the live threat feed.

## Project layout

```
api/
  main.py           # FastAPI app, lifespan boot, CORS, static frontend mount
  config.py         # env-driven settings
  intake/           # POST /report, /report/upload — loaders + indicator extraction
  memory/           # the only package that imports cognee: ontology + MemoryService,
                     # ops store (SQLite), semantic index, confidence signals
  verdict/          # 4-band confidence engine + guidance mapping
frontend/           # React + Vite — CheckView (submit/verdict) + FeedView (live feed)
seed/               # synthetic scam families, reports, and legit controls
```

## Running it

Requires Python 3.11+ and Node 18+.

```bash
# Backend
cp .env.example .env
pip install -r api/requirements.txt
# optional, for scanned-screenshot OCR (needs the Tesseract binary on PATH):
pip install pytesseract pillow
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev    # http://localhost:5173, proxies /report /feed /families /graph /health to :8000
```

The backend seeds its own graph on first boot (synthetic reports across six
scam families plus legit controls) — there's no empty-state demo. No LLM key
is required: deterministic indicator matching and local `fastembed` semantic
matching produce correct verdicts on their own. Set `LLM_*` in `.env` to
additionally light up Cognee's cited graph explanations and the
`improve`/`memify` feedback loop.

### Environment

| Variable | Required | Default | Notes |
|---|---|---|---|
| `API_HOST` / `API_PORT` | No | `127.0.0.1` / `8000` | |
| `WEB_ORIGIN` | No | `http://localhost:5173` | added to the CORS allowlist |
| `DATA_DIR` | No | `./.antibody_data` | ops DB + Cognee's embedded kuzu/lancedb stores + model cache |
| `LLM_PROVIDER` / `LLM_MODEL` / `LLM_ENDPOINT` / `LLM_API_KEY` | No | — | OpenAI-compatible; read directly by Cognee |
| `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` / `EMBEDDING_DIMENSIONS` | No | `fastembed` / `all-MiniLM-L6-v2` / `384` | local, no API key needed |
| `EMBEDDING_ENDPOINT` / `EMBEDDING_API_KEY` | No | — | only needed for a remote embedding provider (see below) |

Both `LLM_*` and `EMBEDDING_*` follow Cognee's own "custom OpenAI-compatible
endpoint" convention (litellm-style model strings), so any such provider works:

```bash
# OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# DeepSeek
LLM_PROVIDER=custom
LLM_MODEL=deepseek/deepseek-chat
LLM_ENDPOINT=https://api.deepseek.com/v1

# NVIDIA NIM (chat + embeddings)
LLM_PROVIDER=custom
LLM_MODEL=nvidia_nim/meta/llama-4-maverick-17b-128e-instruct
LLM_ENDPOINT=https://integrate.api.nvidia.com/v1
LLM_API_KEY=nvapi-...

EMBEDDING_PROVIDER=litellm
EMBEDDING_MODEL=nvidia_nim/nvidia/nv-embedqa-e5-v5
EMBEDDING_DIMENSIONS=1024
EMBEDDING_API_KEY=nvapi-...
```

### API

| Endpoint | Purpose |
|---|---|
| `POST /report` | Submit a text report |
| `POST /report/upload` | Submit a screenshot or audio recording |
| `POST /report/{id}/outcome` | Record what happened (strengthens the family) |
| `POST /report/{id}/forget` | Prune a false positive out of the graph |
| `GET /feed` | Trending families, live counts |
| `GET /families` | All known scam families + guidance |
| `GET /graph` | Shared-tactic graph for traversal/visualization |
| `GET /health` | Liveness + whether an LLM is configured |

## Testing

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

The suite covers indicator/tactic extraction, the confidence-fusion asymmetric
gate (semantic-only evidence can never reach the `confirmed` band — the core
safety property of the app), semantic matching, the ops store, and an
end-to-end API smoke test. It runs with no LLM key configured, the same way
CI runs it.

## Deployment

Antibody ships as a single Docker container: `uvicorn api.main:app` serves
both the API and the built frontend (`frontend/dist`) from one process, so
there's no second service or CORS setup to run in production.

**Locally:**

```bash
docker build -t antibody .
docker run -p 8000:8000 --env-file .env antibody
# open http://localhost:8000
```

**Render (recommended, free tier):**

1. Push this repo to GitHub and create a new **Web Service** on
   [Render](https://render.com), pointing it at the repo — Render detects the
   `Dockerfile` automatically.
2. Set any `LLM_*` / `EMBEDDING_*` values you want (NVIDIA NIM, OpenAI,
   DeepSeek, ...) in Render's dashboard **Environment** tab, never in a
   committed file. Without a key, Antibody still runs correctly on its
   deterministic + semantic fallback path.
3. Deploy. The seed graph auto-loads on first boot (`load_seed_if_empty()`),
   so the demo is never empty, even after a cold start.

The free tier spins the instance down after 15 minutes idle (the first
request after that takes ~30-60s to wake it back up) and has no persistent
disk — both fine here since a fresh boot always reloads the seed data. For an
always-on instance with persistent storage, Render's Starter plan
(~$7/month) removes both constraints.

## AI-assisted build

This project was built with substantial AI assistance (Claude/Claude Code) —
architecture drafting, code generation across the backend and frontend, and
iterative debugging were all done in collaboration with an AI pair programmer,
per the hackathon's disclosure requirement. The design decisions (ontology
shape, the four-rule confidence gate, the reuse of Cognee's low-level
`add`/`cognify`/`search`/`improve`/`forget` verbs) were directed by the human
author.
