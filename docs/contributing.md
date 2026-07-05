# Contributing

Antibody values a small, sharp codebase: clear module docstrings that tie decisions to
intent, load-bearing comments only, and a fast test suite that runs with no API keys.

## Local setup

Requires **Python 3.11+** and **Node 18+**.

```bash
# Backend
cp .env.example .env                 # all keys optional
pip install -r requirements-dev.txt  # app + test/lint/type tooling
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev    # http://localhost:5173, proxies API paths to :8000
```

The backend seeds its own graph on first boot — there's no empty state to set up.

## The quality gate

Everything below runs in CI on every PR. Run it locally before pushing:

```bash
ruff check .        # lint (E, W, F, I, B, C4, UP, SIM)
mypy                # types (files = api, seed)
pytest              # 60 tests, no API keys needed
pytest --cov        # with coverage (currently ~75%)
```

Install the pre-commit hooks to catch all of this at commit time:

```bash
pip install pre-commit
pre-commit install
```

The hooks run ruff (+ autofix), mypy, and standard hygiene checks. We lint but do
**not** enforce a repo-wide autoformatter — the source is deliberately hand-aligned
(e.g. the confidence engine) for readability, so `ruff format` is not part of the gate.

## Code style

- **Docstrings state intent, not mechanics.** Every module opens with *why it exists*
  and which design decision it embodies. Match that voice.
- **Comments are load-bearing.** Only comment the non-obvious — a constraint, a
  gotcha, a "why not the obvious thing." The IPv4-only `getaddrinfo` shim and the
  litellm local-cost-map note in `config.py` are the model.
- **Type everything.** `from __future__ import annotations` at the top, real hints on
  public functions. mypy is a gate.
- **One place touches Cognee.** Anything Cognee-related goes through
  `api/memory/memory_service.py`, and must degrade gracefully (`MemoryUnavailable`).
- **Keep the fast path pure.** `api/memory/confidence.py` has no I/O — keep it that way
  so the safety property stays unit-testable.

## Adding a new scam family

Most contributions are new scam families and their signatures. Add them in the seed
([`seed/seed_data.py`](../seed/seed_data.py)) and, if the family has hard IOCs, they'll
become CONFIRMED fast-path keys automatically. A family needs:

1. **Tactics & lures** — reuse existing labels where possible; shared `Tactic`/`Lure`
   nodes are what make the graph traversable (see [memory layer](memory-layer.md)).
   New keyword sets go in [`api/memory/indicators.py`](../api/memory/indicators.py).
2. **A legit control** (recommended) — a real, benign message that resembles the family,
   marked `is_control=True`. Controls train the asymmetric gate to recognize look-alikes
   as legit instead of accusing them.
3. **Guidance** — `do_now` / `report_to` / `recovery` steps for that family.
4. **A test** — assert the family forms and a reworded variant matches it; if you touch
   `confidence.py`, the semantic-only-never-confirmed test must still pass.

## Pull requests

- Branch off `master`; keep commits in logical groups with clear messages.
- Green CI is required: ruff + mypy + pytest + frontend build.
- If you change verdict behaviour, say so explicitly — the band mapping and the
  asymmetric gate are the product's contract with its users.

## Where to read next

- [Architecture](architecture.md) — the big picture and request lifecycle.
- [Confidence engine](confidence-engine.md) — the scoring and the safety gate.
- [Memory layer](memory-layer.md) — the Cognee integration and the four verbs.
