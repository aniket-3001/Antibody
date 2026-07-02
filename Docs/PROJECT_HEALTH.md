# MemoryOS — Project Health Review

Date: 2026-07-02. Author: engineering (self-review, pre-Milestone 3).
Scope: everything committed through `f8678ec` (Milestone 2.2 complete).

This is a checkpoint, written to be uncomfortable where it needs to be.
Its job is to catch expensive problems while they're still cheap to fix —
not to score the work done so far. Where something is genuinely solid,
it says so plainly; where it isn't, it says that plainly too.

---

## 1. Overall architecture maturity

**Uneven, and the unevenness is itself the headline finding.**

`memory_core` is mature for what it is: a twice-validated (Milestone 1
spike, Milestone 2.2 live reproduction), provider-abstracted, ontology-first
integration with Cognee. The design doc, the skeleton, and the
architecture review were done in the right order and each one caught real
issues before they became expensive (the `forget(hard=...)` misconception,
the dataset cold-start bug, the missing evidence-lookup path — all found
*before* they shipped broken, not after).

But that maturity is concentrated entirely in one module that no judge
will ever see directly. `Backend/` and `Frontend/` are empty directories,
unchanged since the initial commit. Zero lines of user-facing product
exist. The project has done Milestone-1-and-2-style de-risking work more
thoroughly than a hackathon strictly requires — three rounds of design
review, a full error-model taxonomy, a Performance Budget section — while
three of five planned milestones (Backend, Frontend, Demo hardening) sit
at 0%, with a presumably fixed deadline this document has no visibility
into (see §5). That trade needs to be a conscious choice from here, not
inertia.

---

## 2. Remaining technical risks

- **No automated test suite.** The design's own 3-tier testing strategy
  (§7 of `MEMORY_CORE_DESIGN.md`: pure unit tests, `FakeProvider`
  integration tests, live contract tests) is implemented 1-for-3. Only the
  slow, costly, live tier exists (`tests/reproduce_milestone_1.py`).
  Nothing catches a regression automatically; every change is currently
  validated by "run the expensive script and eyeball the report."
- **The error taxonomy was collapsed in practice — fixed as of this
  revision.** `ingestion/pipeline.py` used to wrap every failure from
  `provider.ingest_source()` in a blanket `except Exception ->
  ProviderError`, making `ExtractionError`/`OntologyError` and most of
  `ConfigurationError`'s intended coverage dead code. Exception typing now
  lives in `ModeAProvider` itself (the only module that knows which raw
  Cognee call is executing): `cognee.add()` failures → `ProviderError`,
  ontology-file load failures → `OntologyError`, `cognee.cognify()`
  failures → `ExtractionError`. `pipeline.py` and `recall()` preserve
  already-typed exceptions instead of re-wrapping them, with a narrow
  catch-all as defense in depth for anything a provider fails to type.
  `config.py` also now validates Mode A's required env vars
  (`LLM_PROVIDER`/`LLM_API_KEY`/`EMBEDDING_PROVIDER`) at `get_provider()`
  time, closing the `ConfigurationError` gap — note this does not and
  cannot catch Milestone 1's actual billing failure (a valid key, no
  credit), which is correctly a runtime `ProviderError`, not a config-time
  problem.
- **A more severe, previously-unknown version of the "multi-project
  isolation" risk was found and fixed while verifying the exception-taxonomy
  change**: `ModeAProvider.fetch_graph()` called `get_graph_engine()`
  without establishing Cognee's per-dataset context
  (`set_database_global_context_variables`), which that call needs and
  `cognee.add()`/`cognify()`/`search()` set internally but a raw
  `get_graph_engine()` call does not. Practical effect, verified: in a
  **fresh process**, `get_graph()`/`find_evidence()`/`recall()`'s evidence
  step silently returned an **empty graph** for a project that actually had
  55 nodes / 170 edges — not a multi-project conflict, a **single-project
  read failing after any process restart**, which is worse than originally
  documented and directly undermines the product's core "persists across
  sessions" premise. Root-caused and fixed (scoped, verified in a fresh
  process: 55 nodes / 170 edges and 2 `CONTRADICTS` chains returned
  correctly); the full reproduction script was re-run end-to-end afterward
  and still passes 10/10. What remains **actual, deferred** debt — per
  explicit instruction, not implemented here — is the *concurrency* half of
  this risk: no locking, so two `ingest()` calls racing for the same or
  different projects can still interleave incorrectly (the before/after
  node-count diffing in `ingest_source()` is not safe under concurrent
  writes). That is the "multi-project isolation" item recorded as debt in
  §6, now scoped more precisely than before.
- **No packaging for `memory_core`.** It runs against `prototype/.venv`'s
  incidental installs — no `pyproject.toml`/`requirements.txt` of its own,
  no pinned versions. This is fine for one person on one machine; it will
  actively block Milestone 3 the moment a FastAPI process needs its own,
  reproducible environment.
- **`get_graph()` is a full, unpaginated dump** — O(graph size), no
  filtering. Validated fine at ~170 edges. Unvalidated beyond that, and the
  Performance Budget (`MEMORY_CORE_DESIGN.md` §8) already named this as the
  single highest scaling risk in the design — worth remembering it's not
  hypothetical anymore once a UI is polling it.
- **The 58/180 (Milestone 1) vs. 55/170 (Milestone 2.2 reproduction) node/edge
  count difference was attributed to incremental vs. batched `cognify()`
  calls, but that explanation was never rigorously isolated** — it's the
  most likely cause, not a confirmed one. If it's actually run-to-run LLM
  non-determinism instead, that's a live-demo reliability question that
  hasn't been ruled out.
- **`forget(hard=True)`'s default doesn't mean what the original design
  assumed.** Cognee 1.2.2 doesn't support a real hard/soft distinction;
  the flag is kept for API stability but is currently cosmetic. Low risk
  operationally (behavior is correct either way), but a real trap for
  anyone reading the signature and assuming it controls something it
  doesn't.

---

## 3. Remaining product risks

- **`recall()`'s evidence-relationship selection is a hardcoded binary**
  (`"contradiction"` strategy → `CONTRADICTS`, everything else →
  `SUPPORTS`). A real query like *"why do we use YOLO11"* — exactly the
  kind of relationship question `ONTOLOGY.md`'s `USES`/`EVALUATES` edges
  exist to answer — will currently attach the wrong evidence type, or none.
  Only the contradiction path has ever actually been exercised.
- **The "gap analysis" query type** (`ARCHITECTURE.md` §6 names it one of
  three demo-critical query shapes, e.g. *"which datasets were never
  evaluated?"*) **has never been implemented, only planned.** There is no
  `CYPHER`-based structural query path anywhere in the codebase yet.
- **`improve()`'s demo narrative has never actually been observed.**
  `ARCHITECTURE.md` calls cross-document re-linking "the single most
  under-appreciated" lifecycle operation and the clearest visual argument
  for persistent memory. The reproduction script technically triggered it
  (4 sequential `ingest()` calls into one project), but nobody has looked
  at whether the emergent re-linking is visually or narratively compelling,
  because there is no visualization to look at yet.
- **"What is a project?" is undecided at the product level.** The PRD's
  user journey starts with "Create Project," and `memory_core` requires a
  `project_id` on every call — but nothing upstream defines how a project
  is chosen, created, or presented to a user. This is a product decision
  the backend cannot avoid making, and it isn't made yet.

---

## 4. Remaining demo risks

- **The entire demo currently exists as a Python script that prints a
  markdown report to a terminal.** There is no clickable, presentable
  artifact of any kind.
- **No frozen/prepared demo corpus beyond the same 4-fixture synthetic
  corpus used for validation.** `ARCHITECTURE.md` §10 explicitly named
  "prepared project state, scripted queries" as the mitigation for demo
  fragility (Milestone 5) — none of that exists yet.
- **Graph visualization has never been rendered.** The Milestone 1 spike
  wrapped `cognee.visualize_graph()` in a try/except and explicitly treated
  it as non-essential; `memory_core` doesn't attempt it at all. Given
  `HACKATHON_CONTEXT.md`'s own judging criteria name "graph visualization
  should play a central role" under User Experience, this is not a nice-to-
  have — it is currently the single least-built, most heavily-weighted
  piece of the entire project.
- **Every demo query is a live LLM call**, with no caching or
  pre-computation strategy decided. Live demo latency and live failure risk
  (rate limits, transient API errors) are both currently unmanaged.
- **Billing is a manually-monitored personal API key** with no
  balance-check or alerting — this exact failure mode (insufficient
  credits) already happened once this project (Milestone 1). Nothing
  prevents a repeat on the day it matters most.

---

## 5. Remaining hackathon risks

- **All work past the initial commit is unpushed to GitHub.** `git status`
  shows the local `master` branch 5 commits ahead of `origin/master` — the
  entire Milestone 1 checkpoint, the design doc, the skeleton, the
  architecture review, and Milestone 2.2 exist only on this machine. This
  is the single highest-severity risk in this document: one disk failure
  away from losing everything past the first commit, and the invited
  collaborators (`hrsh-kr`, `shreyashi22486`, `parthrastogicoder`) have had
  nothing to pull, review, or build on since the repo was created, because
  the module their work would depend on isn't visible to them.
- **No CI, no branch protection, no visible review activity.** Not
  necessarily wrong for a solo-driven hackathon sprint, but worth naming
  since three collaborators were explicitly invited and the repo currently
  gives them nothing to do.
- **No deadline is tracked anywhere in the project's own documentation.**
  `HACKATHON_CONTEXT.md` describes judging criteria and philosophy in
  detail but names no date. Worth an explicit gut-check outside this
  document: how much time is actually left, and does "two milestones deeply
  de-risked, zero milestones of user-facing work started" fit it?
- **The judging criteria (`HACKATHON_CONTEXT.md`) weight User Experience and
  Presentation Quality as 2 of 6 dimensions** — both entirely dependent on
  work that hasn't started. Technical Excellence and Best Use of Cognee
  (where this project is currently strongest) are only 2 of the other 4.

---

## 6. Technical debt

Itemized, no padding. Items 1–2 are resolved as of this revision; kept
here (struck through in spirit, not deleted) so the record is honest about
what changed and when, not rewritten as if it were always fine.

1. ~~`ingestion/pipeline.py`'s blanket `except Exception -> ProviderError`
   made `ExtractionError`/`ConfigurationError` dead code.~~ **Fixed**:
   exception typing moved to `ModeAProvider`, the only module that knows
   which Cognee call is executing; `pipeline.py`/`recall()` now preserve
   typed exceptions instead of re-wrapping them.
2. ~~`config.py` carried an unresolved "Milestone 2.2 TODO" for provider
   env-var validation.~~ **Fixed**: `get_provider()` now validates Mode A's
   required env vars and raises `ConfigurationError` for missing/placeholder
   values.
3. No `pyproject.toml`/`requirements.txt` for `memory_core` — see §2.
   **Not addressed this pass** — explicitly out of scope for this fix.
4. No automated tests — see §2. **Not addressed this pass** — `FakeProvider`
   and the Tier 1/2 suite are explicitly deferred, recorded as debt per
   instruction, not implemented.
5. `SourceRecord.title`/`.source_type` and `MemoryStats.source_counts` are
   documented best-effort placeholders, not real data (Cognee doesn't
   expose a recoverable title or source-type field; see
   `MEMORY_CORE_DESIGN.md` §12). Will need a real fix — likely a small
   metadata store of `memory_core`'s own — before Milestone 4's UI can show
   anything meaningful in a source list or inspector panel.
6. `recall()`'s evidence-relationship selection is a two-way hardcoded
   branch, not the general router `ARCHITECTURE.md` §6 describes.
7. `Backend/`, `Frontend/`, `scripts/` are empty placeholder directories
   carried since the initial commit. Cosmetic, but empty scaffolding
   signals more progress than exists — worth pruning or populating, not
   leaving ambiguous.
8. **New, more precisely scoped**: `ModeAProvider.ingest_source()`'s
   before/after node-count diffing and Cognee's own dataset queue are not
   safe under concurrent `ingest()` calls (same project or different
   projects). This is the real remaining substance of "multi-project
   isolation," now that the single-project-fresh-process read bug (§2) is
   fixed — no locking exists, and none is implemented here, per explicit
   instruction to defer it.

---

## 7. What's stable — safe to build on without expecting churn

- `memory_core/models.py`, `memory_core/errors.py` — pure data/types,
  exercised across two full milestones.
- `memory_core/ontology/vocabulary.py` + `research_ontology.owl` — mirrors
  `ONTOLOGY.md`, the project's single most stable document (approved,
  unchanged since Milestone 1).
- `ingest()` / `improve()` / `forget()` signatures — exercised end-to-end
  against real Cognee + Anthropic, behavior matches the validated design.
- `graph/query.py`'s normalization helpers (`normalize_relationship`,
  `node_label`, `node_type`) — ported from code battle-tested across two
  live Cognee runs with consistent results.
- The `MemoryProvider` Protocol boundary itself — the one piece of
  architecture that has already paid for itself twice (it's the reason the
  backend will never need to know Cognee exists).

## 8. What's expected to change

- `recall()`'s evidence-relationship mapping — needs to become a real
  router before any query beyond "contradiction" is demo-worthy.
- `list_sources()`/`get_stats()`'s title/source-type handling — will
  change the moment there's a real metadata story.
- Error handling in `ingestion/pipeline.py` — needs the exception-type
  distinction actually restored before the backend builds HTTP-status
  mapping on top of it (§9 below explains why this matters for the freeze
  decision).
- `config.py` — needs real env validation, and possibly a different
  lifecycle once a long-running backend process owns provider resolution
  instead of a script resolving it fresh per call.
- Everything project-scoping-related — the single-storage-root assumption
  is a known placeholder (§2), not a permanent design.

---

## 9. API freeze recommendations

**Freeze now — the backend can build against these with confidence:**

- `ingest()`, `improve()`, `forget()` signatures and their
  `IngestResult`/`ForgetResult` return shapes.
- `MemoryNode` / `MemoryEdge` / `MemoryGraph`.
- The `MemoryCoreError` hierarchy's names and catch semantics — **now
  actually wired**, not just designed (§6 items 1–2 fixed). Backend code
  can write `except OntologyError`/`except ExtractionError` today and get
  real, distinct behavior, not a generic `ProviderError` for everything.
- `ModeAProvider.fetch_graph()`'s dataset-context bug is fixed — `get_graph()`/
  `find_evidence()`/`recall()` now correctly read a project's graph after a
  process restart, not just within the process that ingested it. This was
  the one item in this freeze list worth double-checking before relying on
  it; it no longer is.

**Do not freeze yet — expect movement, avoid deep coupling:**

- `recall()`'s exact evidence-selection behavior.
- `MemoryStats.source_counts` / `SourceRecord.source_type` / `.title`.
- `project_id` semantics — the single-storage-root assumption may need to
  change shape, not just implementation, once the backend defines what a
  "project" actually is (§3).

---

## 10. Estimated completion percentage

Two honest numbers, because one alone would be spin:

**By planned engineering effort** (rough weighting across
`ARCHITECTURE.md` §11's 5 milestones — spike 10%, `memory_core` 30%,
backend 20%, frontend 25%, demo hardening 15%): Milestones 1–2 are
complete, Milestones 3–5 are at 0%. **~35–40% of total planned effort.**

**By judge-visible product surface**: zero. No UI, no live demo, no graph
visualization, no deployed anything. Two of six judging dimensions (User
Experience, Presentation Quality) currently score at their floor because
nothing exists for a judge to see or use.

Both numbers are true at once, and the gap between them is the main thing
this document is trying to surface.

---

## If I were joining as Staff Engineer: three changes before the backend

Bounded, concrete, none of them a redesign — each is finishing or
correcting something already decided, not proposing new architecture.

**1. Build the `FakeProvider` and the Tier 1/2 test suite the design
already promised (§7 of `MEMORY_CORE_DESIGN.md`), before writing backend
code against `memory_core`.** Right now the only safety net is a live,
costly script. The backend is about to start iterating quickly on top of
this module; without fast, free, deterministic tests, every backend change
risks silently breaking `memory_core` in a way nobody notices until the
next expensive live run — or the demo. This isn't new scope; it's closing
a gap the project's own design doc already specified and never built.

**2. ~~Fix the collapsed error taxonomy~~ — done.** Exception typing now
lives in `ModeAProvider` (the only module that knows which Cognee call is
executing); `pipeline.py`/`recall()` preserve typed exceptions instead of
re-wrapping them; `config.py` validates Mode A's required env vars.
Auditing "the same pattern elsewhere" surfaced something more important
than the audit itself: `fetch_graph()` had a real bug (missing dataset
context) that made graph reads silently empty after a process restart —
found, root-caused, fixed, and re-verified against a full live reproduction
run while closing this item. See §2/§6 for the full account.

**3. Give `memory_core` a real package boundary and force an explicit
decision on project/storage isolation before the backend multiplies
concurrent usage.** Two parts, one recommendation: add a
`pyproject.toml`/`requirements.txt` so it's a real, reproducible
dependency instead of a hitchhiker on `prototype/.venv`; and decide —
out loud, in writing — what "a project" means for the hackathon (even if
the honest answer is "one demo project, multi-tenancy explicitly out of
scope") before the backend's first concurrent request silently corrupts a
graph nobody was watching for a race condition.

None of these require touching the parts of the codebase already marked
stable in §7. All three are cheaper today than they will be once a backend
and frontend are both built on top of the current gaps.
