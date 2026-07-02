# `memory_core` — Design Document

Version: 1.2 (approved; extended by a pre-2.2 architecture review — §11)
Status: **Approved.** v1.1 revised v1.0 per reviewer request: `improve()`
promoted to a stable public function (§2.2, §10.2); Cognee Cloud
capability claims made explicitly version-scoped rather than permanent
(§4); Performance Budget section added (§8). v1.2 adds §11, recording two
new public functions and three type adjustments found by a pre-2.2
architecture review that traced the Milestone 1 spike's steps against the
API. Milestone 2.1 (module skeleton) is implemented; this document is the
spec Milestone 2.2 (ModeAProvider) implements against.
Precedes: Milestone 2.2 implementation.
Depends on: `Docs/ONTOLOGY.md` (schema, source of truth), `Docs/ARCHITECTURE.md`
(system context), `Docs/MILESTONE_1_REPORT.md` (validated evidence that the
patterns this design formalizes actually work against real Cognee 1.2.2).

---

## 0. A conflict this design resolves

Before designing `forget()`, a factual conflict needed resolving, per this
project's rule that conflicting documents must be surfaced, not silently
picked around:

- `ARCHITECTURE.md` §4 and §7 assert `cognee.delete(data_id, dataset_id,
  mode='soft'|'hard')` is a **verified** mechanism.
- `ONTOLOGY.md` §7 and `ARCHITECTURE.md` §12 both call scoped `forget()` an
  **open question**, stating "Cognee 1.2 does not expose a clean per-node
  `delete()`."
- `Docs/PROGRESS.md` (Milestone 1) repeats the "open" framing.

These cannot both be right. I checked the installed package (`cognee`
1.2.2) directly rather than trusting either document:

```
cognee.delete(data_id, dataset_id, mode='soft')
  → deprecated since 0.3.9, but present and functional.
cognee.datasets.delete_data(dataset_id, data_id, mode='soft', delete_dataset_if_empty=False)
  → the non-deprecated replacement. Confirmed present.
cognee.datasets.list_data(dataset_id) → enumerates data items in a dataset
  (used to resolve a source_id to a data_id at forget-time).
```

**Resolution: `ARCHITECTURE.md` was right that the mechanism exists; it was
wrong to call the *design question* closed.** The API exists and is
per-data-item (not dataset-only), which is better than `ONTOLOGY.md` feared.
But *how memory_core uses it* — how a `source_id` maps to a `data_id`, what
"hard" deletion's orphan-pruning actually does to shared extracted entities,
whether `delete_dataset_if_empty` matters for MemoryOS's per-project dataset
model — was never designed. §2.3 and §6 below do that design work. Treat
`ONTOLOGY.md` §7 and `ARCHITECTURE.md` §12's "open question" framing as
**closed by this document**; they should be updated to point here once this
design is approved.

---

## 1. Goals

### 1.1 What `memory_core` is responsible for

- **The only module in MemoryOS that imports `cognee`.** Every other layer
  (backend routes, frontend) talks to `memory_core`'s public API, never to
  Cognee directly. This is `ARCHITECTURE.md` Principle 5, enforced by
  package boundary, not convention.
- **Owning the research ontology as a shared contract** — the entity/edge
  vocabulary, its OWL projection, and the `custom_prompt` template that
  steers extraction toward it. Both ingestion and recall consume this same
  contract, so it has exactly one home.
- **Translating between MemoryOS's domain (`Paper`, `Hypothesis`,
  `CONTRADICTS`, "project", "source") and Cognee's domain (`dataset_name`,
  `node_set`, `SearchType`, `data_id`)** — callers of `memory_core` should
  never need to know a Cognee-specific term.
- **Being provider-agnostic at the call site.** Whether inference is running
  locally against Anthropic or against a future Cognee Cloud tenant must be
  invisible to `ingest()`/`recall()`/`forget()` callers — a config concern,
  not a call-site concern.
- **Guaranteeing that structural claims (node/edge counts, evidence
  subgraphs) are computed deterministically**, never asserted by an LLM.
  This is the trust property Milestone 1 validated and that the product's
  credibility depends on (`MILESTONE_1_REPORT.md` §4.2).
- **Being independently testable and runnable without a web server** —
  exactly as the Milestone 1 spike was. `memory_core` must import and run
  standalone; FastAPI is a caller, not a dependency.

### 1.2 What `memory_core` is explicitly NOT responsible for

- **HTTP.** No routes, no request/response serialization, no auth. That is
  the backend's job (`ARCHITECTURE.md` §5, `services/` vs `routes/`).
- **Presentation shape.** `memory_core` returns provider-agnostic Python
  models (§5). Converting a `MemoryGraph` into Cytoscape.js JSON is a
  backend/frontend concern — `memory_core` does not know a UI exists.
- **File upload handling, multipart parsing, URL fetching over the network.**
  Adapters (§3) accept already-retrieved bytes/text; *retrieving* a URL's
  content or receiving an uploaded file is the backend's job, which then
  hands bytes to `memory_core.ingest()`.
- **Multi-tenant auth / permissions.** `project_id` is a scoping key, not an
  authorization boundary — enforcing who may act on which `project_id` is
  the backend's job. (Cognee itself has a multi-tenant/user layer; this
  design deliberately does not surface it, to keep the hackathon MVP's
  auth surface at zero, matching the PRD's explicit non-goal.)
- **Confidence scoring, ranking, or re-ranking of results.** Cognee's own
  graph-completion and vector search already rank; `memory_core` does not
  add a second ranking layer in v1 (see §3 for why).
- **Being a general-purpose Cognee wrapper.** It exposes exactly the surface
  MemoryOS needs, not a 1:1 passthrough of Cognee's API. `search()`, for
  example, is deliberately not public (§2.6, §10.3).

---

## 2. Public API

All functions are `async def` (Cognee's own API is async throughout, and
the only planned caller — FastAPI — is async-native; see §10.5 for why no
sync wrapper exists). All functions accept `project_id: str` as a required
keyword-only scoping parameter, mapped internally to one Cognee
`dataset_name` per project (§4, §6).

Every function raises only from the exception hierarchy in §6. Nothing
raises a raw Cognee/`anthropic`/`aiohttp` exception across the module
boundary — that would leak Cognee-specific error types into the backend,
defeating the abstraction goal.

### 2.1 `ingest`

```python
async def ingest(
    source: SourceInput,
    *,
    project_id: str,
    active_hypotheses: list[str] | None = None,
) -> IngestResult: ...
```

- **Purpose.** Implements the `remember()` lifecycle operation. Normalizes
  `source` via the appropriate adapter, computes a content-hash identity for
  the source, and (unless a duplicate) runs the provider's `add()` +
  `cognify()` with the ontology resolver and a `custom_prompt` built from
  `active_hypotheses`. `improve()` (§2.2) is a distinct, stable public
  function that delegates to this same orchestration — see §10.2 for why
  both names exist rather than folding `improve()` away entirely.
- **Arguments.**
  - `source: SourceInput` — `{content: str | bytes, source_type: Literal["paper","experiment","research_note","text"], title: str | None, metadata: dict}`. `source_type` selects the adapter.
  - `project_id: str` — scopes to a Cognee dataset.
  - `active_hypotheses: list[str] | None` — verbatim hypothesis statements to inject into the extraction prompt so `SUPPORTS`/`CONTRADICTS` classification has something to classify against (mirrors the spike's validated `CUSTOM_PROMPT` pattern). If `None`, no hypothesis-stance classification is attempted for this ingest call (Tier-1/2 edges still extract normally). This isn't auto-discovered from existing graph state in v1 — see §10.7's note on why a real multi-hypothesis corpus isn't fully solved by this parameter.
- **Return type.** `IngestResult` (§5): `source_id`, `status` (`created` |
  `skipped_duplicate` | `degraded`), `nodes_created`, `edges_created`,
  `duration_ms`, `warnings: list[str]`.
- **Error handling.** Raises `ConfigurationError` if the active provider is
  misconfigured (missing key, unreachable). Raises `ProviderError` if the
  LLM/embedding call fails after the provider's own retry policy is
  exhausted (Cognee's `instructor`-level retries were observed directly in
  Milestone 1 — two attempts with backoff — so `ProviderError` is the
  *final* failure, not the first transient hiccup). Raises `ExtractionError`
  only if `cognify()` itself throws (a hard pipeline fault) — **never** for
  "succeeded but extracted few/no entities," which is instead reported as
  `IngestResult(status="degraded")` (see §6 for why this split matters).
- **Async/sync.** Async only.
- **Idempotency.** `ingest()` is idempotent **by content**, not by call
  count: `source_id` is derived deterministically from
  `hash(project_id, source.source_type, normalized(source.content))`. If
  that `source_id` already exists in the project, `ingest()` short-circuits
  — no duplicate `add()`/`cognify()` call — and returns
  `IngestResult(status="skipped_duplicate")` referencing the existing
  result. Calling `ingest()` twice with identical content is therefore safe
  and cheap. Calling it twice with *edited* content produces two distinct
  `SourceRecord`s (§10.7 flags this as a real open UX question, not
  silently resolved).
- **Expected latency.** Dominated by the LLM extraction call, not I/O.
  Observed in the Milestone 1 validated run (Mode A, Anthropic Claude,
  short documents): roughly 10–60 seconds per source, scaling with document
  length and the number of entities/edges it produces. Not sub-second; the
  backend should treat `ingest()` as a background/async-tracked operation
  for anything beyond a demo-scale corpus, not a request the caller blocks
  on synchronously in the HTTP response cycle (`cognee.add()` itself
  exposes a `run_in_background` flag for exactly this reason — a Milestone
  3 backend concern, noted here so it isn't missed).

### 2.2 `improve`

```python
async def improve(
    source: SourceInput,
    *,
    project_id: str,
    active_hypotheses: list[str] | None = None,
) -> IngestResult: ...
```

- **Purpose.** The stable, named entry point for the `improve()` lifecycle
  operation from `CLAUDE.md`'s required Cognee lifecycle
  (`remember`/`recall`/`improve`/`forget`) and the PRD's "Memory Evolution"
  feature. **Today, `improve()` delegates entirely to `ingest()`** — both
  call the same internal `ingestion/pipeline.py` orchestration function,
  because Cognee's own mechanism for "the graph grows and re-links when new
  research arrives" *is* `add()` + `cognify()` again (`ARCHITECTURE.md`
  §4). `improve()` exists as a distinct, stable name — not a mechanical
  alias kept for its own sake — for two concrete reasons: (1) product/demo
  narration needs to say "watch the memory improve" as a first-class,
  citable operation, not an implementation detail of `ingest()`; and (2) it
  reserves the API surface for real behavioral divergence later (e.g.
  re-evaluating existing `Hypothesis` stance against newly-ingested
  evidence, or re-linking checks beyond what plain re-`cognify()` does)
  without a breaking change — callers who call `improve()` today keep
  working unchanged the day it stops being a thin wrapper. Full rationale
  for why this reverses this document's original position: §10.2.
- **Arguments, return type.** Identical to `ingest()` (§2.1) — same
  `SourceInput`, same `IngestResult`.
- **Error handling.** Identical to `ingest()`. `improve()` does not
  introduce a new exception type or a special "this is the second ingest
  for this project" failure mode — Cognee's cross-document entity
  resolution (shared `Method`/`Hypothesis` nodes gaining new edges) happens
  automatically inside `cognify()`, not as extra logic this function adds.
- **Async/sync.** Async only.
- **Idempotency.** Identical to `ingest()` — same content-hash dedup.
- **Expected latency.** Identical to `ingest()` (§2.1). Not cheaper or more
  expensive than a first ingest — cross-document re-linking is part of
  Cognee's extraction/entity-resolution cost, already included in that
  estimate.

### 2.3 `recall`

```python
async def recall(
    query: str,
    *,
    project_id: str,
    strategy: RecallStrategy | None = None,
) -> RecallResult: ...
```

- **Purpose.** The single query entry point (`ARCHITECTURE.md` §6's recall
  router lives here). Classifies query intent (relationship/"why",
  contradiction, gap-analysis, factual) unless `strategy` overrides it,
  issues the corresponding Cognee `search()` call(s), and — critically —
  always returns the prose answer **and** the evidence it's grounded in
  together, never one without the other. This is the product's core trust
  mechanic (`ARCHITECTURE.md` §3.2, validated in Milestone 1).
- **Arguments.**
  - `query: str` — natural language question.
  - `project_id: str`.
  - `strategy: RecallStrategy | None` — optional explicit override (e.g.
    force the deterministic gap-analysis path) for callers that already
    know the query shape; `None` uses the intent router.
- **Return type.** `RecallResult` (§5): `query`, `answer: str`,
  `evidence: list[Evidence]`, `evidence_graph: MemoryGraph | None`,
  `degraded: bool`, `strategy_used: str`, `duration_ms`.
- **Error handling.** Raises `RecallError` only if the recall *pipeline*
  fails outright (no strategy could be executed, the provider errored on
  every attempt). **Does not raise** when the honest answer is "no evidence
  found" or "no relationship exists" — that is a normal, valid
  `RecallResult` with empty `evidence` and an answer that says so. This
  distinction is deliberate and is the most important rule in this
  document's error model (§6 elaborates). Raises `ProviderError` for
  LLM-call failures after retry, same semantics as `ingest()`.
- **Async/sync.** Async only.
- **Idempotency.** Read-only — calling `recall()` never mutates project
  state, so it is idempotent in the "no side effects" sense. It is **not**
  guaranteed to return byte-identical output across repeated calls with the
  same query, because the natural-language answer is LLM-generated and LLM
  output is not deterministic between calls. The `evidence`/`evidence_graph`
  fields (computed by deterministic traversal, per §1.1) *are* stable
  across calls against an unchanged graph — only the prose narration can
  vary.
- **Expected latency.** Observed in Milestone 1 (Mode A): roughly 5–15
  seconds for one or two search calls (answer + evidence context). Scales
  with graph size for the traversal component and is otherwise dominated by
  LLM completion latency.

### 2.4 `forget`

```python
async def forget(
    source_id: str,
    *,
    project_id: str,
    hard: bool = True,
) -> ForgetResult: ...
```

- **Purpose.** Implements `forget()`. Resolves `source_id` to a Cognee
  `data_id` within the project's dataset (via `cognee.datasets.list_data`,
  matching on the `node_set` tag assigned at ingest time), then calls
  `cognee.datasets.delete_data(dataset_id, data_id, mode=...)`.
- **Arguments.**
  - `source_id: str` — the `IngestResult.source_id` / `SourceRecord.id`
    returned at ingest time.
  - `project_id: str`.
  - `hard: bool = True` — `mode="hard"` by default, matching
    `ONTOLOGY.md` §7's target semantics (source-anchored node and its
    *exclusively*-referenced extracted entities are removed; entities still
    referenced by another surviving source are retained). `hard=False`
    requests `mode="soft"` (removes the source node only, leaves extracted
    entities as potential orphans) for callers that explicitly want that —
    expected to be rare.
- **Return type.** `ForgetResult` (§5): `source_id`, `deleted: bool`,
  `already_absent: bool`, `orphans_pruned: int`.
- **Error handling.** Raises `ProviderError` if the underlying delete call
  fails (e.g. transient DB error). **Does not raise** for an unknown or
  already-deleted `source_id`; deletion is intentionally idempotent,
  matching HTTP `DELETE` semantics (`ARCHITECTURE.md` §7's
  `DELETE /sources/{id}`) — returns
  `ForgetResult(deleted=False, already_absent=True)` instead. This means
  the backend can call `forget()` twice safely and doesn't need a
  pre-existence check.
- **Async/sync.** Async only.
- **Idempotency.** Fully idempotent by design (see above) — this is one of
  the few functions in the API where idempotency is a hard guarantee, not
  a best-effort content-hash heuristic.
- **Expected latency.** No LLM call involved — this is a database
  operation. Expected ~1–5 seconds (dominated by the `list_data` lookup and
  graph-consistency work on `mode="hard"`, not by inference).

### 2.5 Read-only accessors

These are not lifecycle operations but are required by the backend API
surface already specified in `ARCHITECTURE.md` §7 (`GET /graph`,
`GET /stats`, and the source list `DELETE /sources/{id}` implicitly needs
to enumerate).

```python
async def get_graph(*, project_id: str) -> MemoryGraph: ...
async def get_stats(*, project_id: str) -> MemoryStats: ...
async def list_sources(*, project_id: str) -> list[SourceRecord]: ...
```

- **Purpose.** Deterministic, LLM-free reads over the current graph state
  — `get_graph` for full visualization, `get_stats` for the header-strip
  counts, `list_sources` to enumerate what can be passed to `forget()`.
- **Error handling.** `get_graph` and the entity-count half of `get_stats`
  raise `CapabilityUnavailableError` if the active provider cannot produce
  a local graph (this is the honest, explicit version of whatever the
  active provider's current limitation is — see §4 — rather than silently
  returning an empty graph, which would be indistinguishable from "this
  project genuinely has no data" and would be a real bug source).
  `list_sources` and the source-count half of `get_stats` work in both
  modes, since they only need Cognee's dataset/data-item listing, not the
  local graph engine.
- **Async/sync.** Async only.
- **Idempotency.** Pure reads; trivially idempotent.
- **Expected latency.** Sub-second to a few seconds at demo scale (tens to
  low hundreds of nodes, as validated in Milestone 1's 58-node graph). Not
  validated at larger scale — see the Performance Budget (§8) for the
  explicit scaling caveat; this is the single highest scaling risk named in
  this design.

### 2.6 Deliberately not in the public API

- **`search()`** — not exposed. It is Cognee's primitive, not MemoryOS's;
  exposing it would let Cognee-specific concepts (`SearchType`) leak past
  the module boundary, which directly undermines Goal 1.1's provider-opacity
  requirement. `recall()` is the only sanctioned query entry point; it uses
  Cognee's search primitives internally.
- **`update()`** — deferred entirely, not designed. See §10.3.

(`improve()` is *not* on this list — as of v1.1 it is a first-class public
function; see §2.2 and §10.2 for why this document changed position on it.)

---

## 3. Internal Architecture

```
memory_core/
├── __init__.py         # public API surface: ingest, improve, recall,
│                        #   forget, get_graph, get_stats, list_sources
├── config.py            # provider/mode resolution from env; ConfigurationError
├── errors.py             # exception hierarchy (§6)
├── models.py              # all dataclasses (§5)
│
├── providers/
│   ├── base.py            # MemoryProvider Protocol (§4) + ProviderCapabilities
│   ├── mode_a.py            # local Cognee + direct LLM/embedding (implemented)
│   └── mode_b.py             # Cognee Cloud (scaffolded, not implemented — §4/§10.6)
│
├── ontology/
│   ├── vocabulary.py         # EntityType/RelationshipType enums, domain/range matrix
│   ├── research_ontology.owl # OWL projection (promoted from the spike, unchanged)
│   └── prompts.py              # custom_prompt template builder(active_hypotheses)
│
├── ingestion/
│   ├── pipeline.py              # ingest()/improve() orchestration: hash/dedup,
│   │                             #   adapter dispatch, provider.ingest_source()
│   │                             #   call (one function, two public wrappers)
│   └── adapters/
│       ├── base.py                # Adapter Protocol: raw SourceInput -> (text, metadata)
│       ├── text.py                 # plain text / research notes (implemented)
│       ├── markdown.py              # markdown (implemented; spike's fixture format)
│       ├── pdf.py                    # PyMuPDF (stub — not needed until real corpus)
│       └── url.py                     # stub
│
├── retrieval/
│   ├── router.py                  # intent -> RecallStrategy selection (ARCHITECTURE §6)
│   └── evidence.py                 # deterministic evidence-subgraph extraction,
│                                    #   generalized from the spike's
│                                    #   find_contradiction_evidence() to any
│                                    #   (relationship_type, target_node) pattern
│
└── graph/
    └── query.py                    # get_graph()/get_stats()/list_sources() +
                                     #   shared node/edge normalization helpers
                                     #   (promoted from the spike's normalize_node/
                                     #   normalize_edge/node_label/node_type)
```

### Module responsibilities

- **`config.py`** — the single place that reads environment variables and
  decides which `MemoryProvider` implementation to construct. Fails fast
  (`ConfigurationError`) at first use if required config is missing, rather
  than surfacing a confusing downstream `ProviderError` later (this is a
  direct lesson from Milestone 1's billing failure, which *did* surface as
  a confusing deep-stack error — see `PROGRESS.md`'s bug log).
- **`errors.py` / `models.py`** — no logic, just the shared vocabulary every
  other module imports. Kept dependency-free (no Cognee imports) so tests
  can import them without triggering Cognee's own import-time setup (which
  Milestone 1 observed does real work — log files, DB connections — just
  from `import cognee`).
- **`providers/`** — the execution-mode boundary (§4). This is the module
  that actually imports `cognee`; nothing outside `providers/` (plus
  `config.py`, which only *selects* a provider) touches the `cognee`
  package directly. This is what makes the Mode A/B swap "minimal code
  change" a structural guarantee, not a convention people have to remember.
- **`ontology/`** — data, not logic. `vocabulary.py` is the Python mirror of
  `ONTOLOGY.md`'s entity/relationship tables (kept in sync by
  discipline/review, same as the OWL file already is). Isolating it means a
  future ontology change (new entity type, new relationship) touches one
  module, not ingestion and retrieval code scattered across the package —
  directly enables the extension points in §9.
- **`ingestion/`** — orchestrates `ingest()` and `improve()`, both thin
  public wrappers around one internal pipeline function (§2.2). `adapters/`
  is nested here
  (not top-level, unlike the example structure in the brief) because
  adapters have exactly one consumer — the ingestion pipeline — and nesting
  makes that dependency direction explicit rather than implied. (Considered
  keeping `adapters/` top-level for discoverability; rejected because
  nothing outside ingestion should ever import an adapter directly.)
- **`retrieval/`** — orchestrates `recall()`. `router.py` and `evidence.py`
  are split because they answer different questions: the router decides
  *which Cognee search strategy to use* for a given question; `evidence.py`
  decides *which subgraph proves the answer*, by traversal, independent of
  which strategy produced the prose. `evidence.py` depends on
  `graph/query.py`'s normalization helpers rather than duplicating them.
- **`graph/`** — deterministic, LLM-free reads. Deliberately separate from
  `retrieval/` even though both do graph traversal: `graph/query.py`
  answers "what does the whole project's memory look like" (visualization,
  stats — no query in mind); `retrieval/evidence.py` answers "what subgraph
  explains *this specific* recall answer" (query-scoped). Different
  callers, different output shapes, shared low-level helpers.

### Explicitly rejected from the internal structure

The brief's example structure included `storage/` and `ranking/` as
top-level packages. Both are deliberately **not** present:

- **No `storage/`.** Cognee *is* the storage layer (hybrid graph + vector
  store) — `memory_core` has no storage implementation of its own to
  isolate. A `storage/` package would either be empty or would duplicate
  `providers/`'s job of talking to Cognee. Adding it would be structure for
  its own sake, which `CLAUDE.md`'s principles explicitly warn against.
- **No `ranking/`.** Cognee's `GRAPH_COMPLETION`/vector search already rank
  results internally; v1 has no second, MemoryOS-specific ranking pass to
  isolate. If one is ever needed (e.g. a "confidence" score blending recency
  + evidence count for `SUPPORTS`/`CONTRADICTS` edges — flagged as a real
  future idea in `ONTOLOGY.md` §8), it becomes a genuine new module at that
  point, not a placeholder maintained empty until then.

---

## 4. Provider Abstraction

### 4.1 The abstraction MemoryOS actually needs

The naive reading of "provider abstraction" is "make the LLM vendor
swappable." **That problem is already solved — by Cognee itself.** Cognee
1.2.2 reads `LLM_PROVIDER`/`EMBEDDING_PROVIDER` and related settings
entirely from environment configuration; no application code branches on
vendor. `memory_core` does not need to re-solve this; `config.py` simply
passes environment-driven settings through.

**The abstraction this project actually needs is the execution-mode
boundary** — because Mode A (local pipeline) and Mode B (Cognee Cloud) do
not just swap *who* runs inference; they change *which capabilities are
even available*. As of **Cognee 1.2.2** (the version this design was
verified against; see `ARCHITECTURE.md` §9.1):

- Mode B's remote `cognify()` path drops the ontology resolver and
  `graph_model` — two of the three extraction-quality levers `ONTOLOGY.md`
  §2.4 relies on.
- Mode B's graph is built and stored server-side — the local
  `get_graph_engine().get_graph_data()` call `graph/query.py` and
  `retrieval/evidence.py` depend on returns nothing.

**These are properties of the current SDK version, not permanent
architectural facts about Cognee Cloud as a product.** Cognee Cloud is
under active development; a future release could forward the ontology
resolver, or expose a way to pull the server-side graph back locally, and
this design should not be read as betting against that. What it does
assert is narrower and more durable: *whatever* Mode B turns out to
support at any given time, `memory_core` needs a way to ask "can I get a
deterministic evidence subgraph right now" and branch on the answer — that
question, and the `capabilities()` contract that answers it, is the actual
abstraction. The specific values below are today's answer, to be
re-checked whenever `ModeBProvider` is implemented, not a permanent
assumption baked into the interface.

### 4.2 The `MemoryProvider` interface

```python
class ProviderCapabilities:
    supports_deterministic_evidence: bool
    supports_ontology_resolver: bool
    supports_hard_delete: bool

class MemoryProvider(Protocol):
    def capabilities(self) -> ProviderCapabilities: ...

    async def ingest_source(
        self, text: str, *, dataset: str, node_set: list[str],
        ontology: OntologyBundle, custom_prompt: str,
    ) -> ProviderIngestReceipt: ...

    async def query(
        self, query_text: str, *, dataset: str, strategy: RecallStrategy,
    ) -> ProviderQueryResult: ...

    async def fetch_graph(self, *, dataset: str) -> RawGraph | None:
        """None if this provider cannot produce a local graph (Mode B today)."""

    async def list_data(self, *, dataset: str) -> list[ProviderDataItem]: ...

    async def delete_source(
        self, *, dataset: str, data_id: str, hard: bool,
    ) -> ProviderDeleteReceipt: ...
```

`memory_core`'s public functions (§2) call the single active provider
(resolved once by `config.py`) and never branch on mode themselves — mode-
specific behavior lives entirely inside `ModeAProvider`/`ModeBProvider`.
Where a capability is genuinely unavailable, the provider reports it via
`capabilities()`, and the calling function (`get_graph()`, etc.) turns that
into the explicit `CapabilityUnavailableError` from §2.4/§6 — never a
silent empty result.

### 4.3 Mode A — implemented in Milestone 2

`ModeAProvider` wraps exactly the pattern Milestone 1 validated:
`cognee.add(node_set=[...])`, `cognee.cognify(config={"ontology_config":
{"ontology_resolver": ...}}, custom_prompt=...)`,
`get_graph_engine().get_graph_data()`, `cognee.search(SearchType.
GRAPH_COMPLETION, ...)`, `cognee.datasets.delete_data(...)`. All Mode A
capabilities are `True`.

### 4.4 Mode B — scaffolded only, not implemented

`ModeBProvider` implements the `MemoryProvider` Protocol (so the type
contract is real and checkable) but most methods raise `NotImplementedError`
in Milestone 2. `capabilities()` reports
`supports_deterministic_evidence=False, supports_ontology_resolver=False` —
**the values verified against Cognee 1.2.2 at the time of writing, treated
as a snapshot to re-verify at implementation time, not a permanent
specification.** Whoever implements `ModeBProvider` should re-check these
against whatever Cognee Cloud SDK version is current then; if the platform
has closed the gap by that point, `capabilities()` simply reports more
`True`s and `recall()`'s degraded-mode branch (§4.5) naturally stops
triggering — no other code changes required. This is a deliberate scope
decision: implementing a working Cognee Cloud backend is not required for
the hackathon submission, and building it now would be effort spent on a
capability nobody is asking for yet (`CLAUDE.md`'s scope-management
principle). What *is* required — and what this section delivers — is that
the seam exists, is typed, and is where a future implementation plugs in
without touching `ingest()`/`recall()`/`forget()` or anything above
`providers/`. Selecting a provider is one `config.py` decision (e.g.
`MEMORY_CORE_MODE=local|cloud`), not a code change at any call site.

### 4.5 What `recall()` does when evidence is unavailable

If the active provider's `capabilities().supports_deterministic_evidence`
is `False`, `recall()` does not fail. It still returns the LLM's prose
answer (Mode B can still call `cognee.search()` and get a completion), but
sets `RecallResult.evidence = []`, `evidence_graph = None`, and
`degraded = True`. Callers (the backend/UI) are expected to check
`degraded` and communicate "this answer isn't backed by an inspectable
subgraph" rather than presenting a Mode B answer with the same visual
confidence as a Mode A one. This is a real, currently-unsolved product
question, flagged honestly in §10.6 rather than hidden behind a
clean-looking API — and one that may simply dissolve if a future Cognee
Cloud release closes the capability gap described in §4.1, which is
exactly why `degraded` is a runtime-computed flag and not a hardcoded
assumption.

---

## 5. Data Models

Two categories: **domain models** (mirror the ontology's own groupings, not
a 1:1 dataclass per entity type — see §10.4 for why) and
**operation-result models** (returned by the public API functions in §2).

### 5.1 Graph primitives

```python
class EntityType(str, Enum):
    PAPER = "Paper"; AUTHOR = "Author"; METHOD = "Method"; DATASET = "Dataset"
    BENCHMARK = "Benchmark"; EXPERIMENT = "Experiment"; HYPOTHESIS = "Hypothesis"
    FINDING = "Finding"; RESEARCH_NOTE = "ResearchNote"; TOPIC = "Topic"

class RelationshipType(str, Enum):
    WRITTEN_BY = "WRITTEN_BY"; USES = "USES"; EVALUATES = "EVALUATES"
    SUPPORTS = "SUPPORTS"; CONTRADICTS = "CONTRADICTS"
    DERIVED_FROM = "DERIVED_FROM"; REFERENCES = "REFERENCES"; ABOUT = "ABOUT"

@dataclass
class MemoryNode:
    id: str
    type: EntityType | Literal["unknown"]   # "unknown" for off-vocabulary/scaffolding nodes
    label: str
    attributes: dict[str, Any]
    source_ids: list[str]   # which SourceRecord(s) this node was extracted from

@dataclass
class MemoryEdge:
    source_id: str
    target_id: str
    relationship: RelationshipType | str   # str for off-vocabulary edges (never dropped, just untyped)
    attributes: dict[str, Any]

@dataclass
class MemoryGraph:
    nodes: list[MemoryNode]
    edges: list[MemoryEdge]
```

`MemoryNode.type`/`MemoryEdge.relationship` deliberately allow an
"unknown"/`str` escape hatch rather than raising on off-vocabulary data —
Milestone 1's real graph contained Cognee scaffolding edges
(`BELONGS_TO_SET`, `CONTAINS`, `IS_A`) alongside the ontology's own edges,
and dropping or crashing on them would lose real information. Callers that
only care about the closed ontology filter by type; nothing is hidden from
the caller who wants everything.

### 5.2 Source & domain models

```python
@dataclass
class SourceInput:                      # ingest() argument, not extracted from the graph
    content: str | bytes
    source_type: Literal["paper", "experiment", "research_note", "text"]
    title: str | None
    metadata: dict[str, Any]            # adapter-specific: authors, date, url, ...

@dataclass
class SourceRecord:                     # unifies Paper/Experiment/ResearchNote —
    id: str                             #   ONTOLOGY.md §3.2 already groups these three
    project_id: str                     #   as "source-anchored, unit of forget()"; this
    source_type: Literal["paper", "experiment", "research_note", "text"]
    title: str
    ingested_at: datetime
    node_set: str                       # the Cognee node_set tag (== id, by construction)
    raw_metadata: dict[str, Any]

@dataclass
class Hypothesis:
    id: str
    statement: str
    status: Literal["active", "retired"]

@dataclass
class Finding:
    id: str
    statement: str
    quantitative_value: str | None
    source_id: str | None               # originating SourceRecord, if resolvable

@dataclass
class Evidence:                          # one edge of a SUPPORTS/CONTRADICTS chain
    evidence_node: MemoryNode            # the Paper/Finding/Experiment node
    hypothesis: Hypothesis
    relationship: Literal["SUPPORTS", "CONTRADICTS"]
    source: SourceRecord | None          # resolved anchored document, if available
```

### 5.3 Operation results

```python
@dataclass
class IngestResult:
    source_id: str
    project_id: str
    status: Literal["created", "skipped_duplicate", "degraded"]
    nodes_created: int
    edges_created: int
    duration_ms: int
    warnings: list[str]

@dataclass
class RecallResult:                      # the brief's "QueryResult" — named for the verb
    query: str                           #   it pairs with (recall()), not the noun
    answer: str
    evidence: list[Evidence]
    evidence_graph: MemoryGraph | None
    degraded: bool
    strategy_used: str
    duration_ms: int

@dataclass
class ForgetResult:
    source_id: str
    deleted: bool
    already_absent: bool
    orphans_pruned: int

@dataclass
class MemoryStats:
    project_id: str
    source_counts: dict[str, int]            # by source_type; always available (both modes)
    entity_counts: dict[EntityType, int] | None   # None in Mode B (§2.5, §4.5)
    active_hypotheses: int
    last_ingest_at: datetime | None
```

---

## 6. Error Model

### 6.1 Hierarchy

```
MemoryCoreError                      (base — callers can catch broadly)
├── ConfigurationError               (provider misconfigured; fail-fast, config.py)
├── OntologyError                    (ontology/OWL file failed to load or validate)
├── ProviderError                    (LLM/embedding/DB call failed after retries)
├── ExtractionError                  (cognify() raised — a hard pipeline fault)
├── RecallError                      (the recall pipeline itself failed)
└── CapabilityUnavailableError       (operation needs a capability the active
                                       provider doesn't have — e.g. get_graph()
                                       under Mode B)
```

### 6.2 The governing rule

**Raise for:** the requested operation could not be completed as specified
— configuration is broken, a provider call failed outright, a pipeline
step threw, or the active provider structurally cannot do what was asked.

**Return normally (never raise) for:** a legitimate, honest state of the
world that happens to be "empty" or "negative" — no contradiction found, no
sources in a fresh project, nothing to delete because it's already gone.
These are answers, not failures.

This rule is stated explicitly because it is easy to get backwards under
deadline pressure (e.g. "recall found nothing, so throw a 404-shaped
exception" is a natural but wrong instinct — see the `RecallError` note in
§2.2). Getting it right here means the backend's HTTP layer maps
`MemoryCoreError` subtypes to 5xx/4xx status codes cleanly, while a normal
"no evidence" answer is just a 200 with an empty `evidence` list.

### 6.3 Notes on specific exceptions

- **`ExtractionError` is narrowly scoped.** It fires only when `cognify()`
  raises. "Cognify succeeded but the graph is thin" is *not* an error — it
  is impossible to reliably distinguish "provider is broken" from
  "genuinely sparse source text" with a heuristic, so this design doesn't
  try. That case is reported as `IngestResult(status="degraded")` with a
  warning, and left for the caller (or a human) to judge.
- **`ConfigurationError` is separated from `ProviderError`** deliberately.
  Milestone 1's billing failure (`PROGRESS.md`'s bug log) surfaced as a
  confusing, deeply-nested retry-exhaustion traceback that took real
  investigation to diagnose. A dedicated, fail-fast `ConfigurationError`
  raised the first time `config.py` resolves an unusable provider (missing
  key, unreachable endpoint) turns that class of failure into an
  immediately actionable message instead of a mystery three layers into an
  ingest call.
- **`CapabilityUnavailableError` exists specifically so Mode B's
  limitations are visible, not silently downgraded.** An empty `MemoryGraph`
  and "I can't produce a graph in this mode" must never look the same to a
  caller.

---

## 7. Testing Strategy

Three tiers, only the first two run without spending API credits or
touching the network:

### Tier 1 — Pure unit tests (no I/O, no mocks needed)

Targets: `ontology/prompts.py`'s prompt builder output, `ontology/
vocabulary.py`'s domain/range constraint checks, `graph/query.py`'s
node/edge normalization functions (`normalize_node`/`normalize_edge`/
`node_label`/`node_type`/`norm_rel` — promoted verbatim from the Milestone 1
spike, which already exercised them against real Cognee output shapes),
`retrieval/router.py`'s intent-to-strategy classification. These are
plain functions of data in, data out — fast, deterministic, run on every
commit.

### Tier 2 — Integration tests against a `FakeProvider`

A `FakeProvider` implements the `MemoryProvider` Protocol (§4.2) entirely
in-memory: `ingest_source()` appends to an in-memory node/edge list using a
small deterministic rule-based "extractor" (not an LLM) driven off keyword
matching in the test fixtures; `fetch_graph()` returns that in-memory state;
`delete_source()` mutates it. This tests `memory_core`'s own orchestration
logic — dedup/idempotency in `ingest()`, the "raise vs return" rule in
`recall()`/`forget()`, `CapabilityUnavailableError` triggering correctly
when a `FakeProvider` reports reduced capabilities — without ever calling
Cognee or an LLM. Fast, deterministic, runs on every commit. This tier is
also where the Mode A/Mode B *contract* is tested: the same test suite runs
against a `FakeProvider` configured with Mode A capabilities and again with
Mode B capabilities, proving `recall()`'s degraded-mode branch (§4.5)
actually works, without needing a real Cognee Cloud tenant to do it.

### Tier 3 — Live contract tests against real Cognee + real Anthropic

The Milestone 1 spike's own validated run, formalized: ingest the same four
fixtures, run the same `CONTRADICTS` query, assert the same success
criteria `MILESTONE_1_REPORT.md` reports. This tier catches real drift —
Cognee version upgrades, prompt behavior changes, Anthropic model
deprecations — that Tiers 1–2 structurally cannot catch, because they never
touch the real provider. It costs money and takes minutes, so it is
**not** part of the default fast test loop; it runs manually or behind an
explicit marker (e.g. `pytest -m live`), and is the one place this project
accepts "not run on every commit" as correct, not lazy — the alternative
(spending API credits on every push) doesn't buy proportionate confidence.

### Deterministic graph snapshots

For Tier 2/3, the resulting `MemoryGraph` (or the `FakeProvider`'s
deterministic equivalent) can be serialized and diffed against a committed
golden file — the same idea as `outputs/graph.json` from the Milestone 1
checkpoint, formalized as an assertion instead of a manually-read artifact.
Golden-file tests are used only where output is actually deterministic
(Tier 2's `FakeProvider`, or Tier 3's *structural* claims like relationship
type presence) — never against Tier 3's LLM prose, which is expected to
vary run to run (§2.2).

---

## 8. Performance Budget

Targets, not guarantees — derived from the single validated Milestone 1 run
(`MILESTONE_1_REPORT.md`: 4 sources, 58 nodes, 180 edges, Mode A /
Anthropic), not from load testing. Tier 3 of the testing strategy (§7) is
where these get re-measured against real data over time, not assumed to
hold forever.

### 8.1 Scope: what "demo scale" means

This design targets **demo-scale projects**: single-digit to low-double-
digit sources per project, producing graphs in the tens-to-low-hundreds of
nodes/edges — directly matching Milestone 1's validated 58-node/180-edge
result. This is a deliberate, named scope boundary (`CLAUDE.md`'s
MVP-over-production-scale principle), not an oversight. Explicitly **out
of budget and unvalidated** by this design:

- Projects with hundreds of sources / thousands of nodes.
- Concurrent multi-user ingestion into the same `project_id` — Cognee's
  dataset-level concurrency/locking behavior under simultaneous writers is
  unverified; this design assumes **single-writer-per-project** for v1.
- Sustained high-throughput `ingest()`/`improve()` (many sources per
  minute).

If MemoryOS ever needs any of these, that is new design work — this
document does not implicitly promise them.

### 8.2 Per-operation targets

| Operation | Target (p50 / p95) | Basis | Scaling risk |
|---|---|---|---|
| `ingest()` / `improve()` | 15s / 60s per source | Observed Milestone 1: ~35s/doc average for short (≤1 page) fixtures, dominated by LLM extraction | Scales with document length and entity density; unvalidated beyond short documents. If blown, the fix is backend-level background execution (`cognee.add(run_in_background=True)`), not a `memory_core` redesign — `memory_core` exposes a blocking `async` call regardless of scale; whether the caller awaits inline or schedules it is the backend's decision, and `memory_core` should not need to know which. |
| `recall()` | 8s / 20s | Observed Milestone 1: ~11s per search call, 1–2 calls per query | Traversal cost for the evidence subgraph is expected to grow with graph size; no complexity analysis has been done. Re-measure at Tier 3 as the fixture corpus grows. |
| `forget()` | 2s / 8s | No LLM call — DB-bound (`list_data` lookup + `delete_data`) | Low risk; `mode="hard"` orphan-pruning cost is the only part that could grow with graph size, and only within that source's neighborhood, not the whole graph. |
| `get_graph()` / `get_stats()` / `list_sources()` | 1s / 3s | Observed Milestone 1: full 58-node/180-edge dump well under a second | **Highest scaling risk in this design.** `get_graph()` is a full, unpaginated dump of `get_graph_engine().get_graph_data()` — O(graph size) by construction, no filtering or pagination in v1. Fine at demo scale; a real bottleneck if a project ever reaches thousands of nodes. Named as an explicit gap, not solved here — a future revision would need cursor-based pagination or type/date filtering on `get_graph()`. |

### 8.3 How these budgets are meant to be used

These are **directional targets to design against**, not SLAs to enforce
in code in Milestone 2 — there is no proposed timeout/circuit-breaker
logic in this document, because adding one before Tier 3 produces real
measurements would be guessing twice. Their purpose is to catch a design
that's obviously wrong early (e.g. if `get_graph()` needed a five-second
timeout at demo scale, something in this design would be broken, not just
slow) and to give Milestone 3's backend work honest numbers to plan the
ingest-as-background-job decision around, rather than an unstated
assumption that every operation is request/response-cycle-fast.

---

## 9. Future Extension Points

Every listed extension is a **new `Adapter`**, not a change to `ingest()`'s
signature or to `providers/`, `retrieval/`, or `graph/`:

| Extension | Fits as | Notes |
|---|---|---|
| PDF | `adapters/pdf.py` (stubbed now, per `ARCHITECTURE.md`'s PyMuPDF choice) | Pure text-extraction adapter; no ontology change needed. |
| URL | `adapters/url.py` (stubbed now) | Fetching is the backend's job (§1.2); the adapter receives already-fetched HTML/text. |
| GitHub | new `adapters/github.py` | Likely needs a **new entity type** (e.g. `CodeCommit`/`Repository`) — an `ontology/vocabulary.py` change, deliberately, not an automatic one. `ONTOLOGY.md`'s closed-vocabulary philosophy (§2, §8) means this is a reviewed schema decision, same weight as adding `CONTRADICTS` was. |
| Slack | new `adapters/slack.py` | Same as GitHub — probably needs a `Message`/`Thread` entity type; ontology change, not just a new adapter. |
| Video / meeting transcripts | new `adapters/transcript.py` | Transcription itself (audio → text) happens *inside* the adapter or upstream of it — `memory_core` only ever receives plain text + metadata, per the `Adapter` Protocol (§3). No design change required as long as the adapter's output is text. |
| Research notes | already covered | `adapters/markdown.py`/`text.py`, validated in Milestone 1. |

The pattern holds because `ingestion/pipeline.py` dispatches on
`source.source_type` to an `Adapter.load()` call whose contract is fixed
(`raw input → (text, metadata)`); adding a case to that dispatch and a new
adapter module is the entire integration cost for anything that can be
reduced to text. The only extensions that touch more than `adapters/` are
ones that need genuinely new *relationships* the closed 8-edge vocabulary
doesn't cover — those are product decisions, correctly gated behind a
deliberate ontology review, not something this design tries to make
automatic.

---

## 10. Tradeoffs

### 10.1 Module-level functions, not a `MemoryCore` class

Chosen: `memory_core.ingest(...)`, not `MemoryCore().ingest(...)`. There is
no per-instance state to hold beyond the active provider, which is a
single, process-wide config resolved once (`config.py`). Mirrors Cognee's
own top-level function API and the PRD's `remember`/`recall`/`forget`
framing. **Real limitation, named rather than hidden:** if MemoryOS ever
needs multiple *concurrently different* provider configurations in one
process (not just different `project_id`s under one config — e.g. two
projects simultaneously on Mode A and Mode B), this design breaks and needs
to become instance-based. Not a concern for the hackathon MVP; worth
revisiting if that requirement ever appears.

### 10.2 `improve()` is a stable public function that delegates to `ingest()`

**Revised from this document's v1.0 draft**, which argued `improve()`
shouldn't exist as a separate function at all — Cognee's `improve` is
mechanically `add()` + `cognify()` again, identical to `ingest()`, and a
pure alias risks either staying pointless or accumulating divergent logic
for no principled reason. That argument is still correct about the
*mechanism*; it was wrong about what follows from it. Two things it
under-weighted:

1. **Product narrative weight.** `CLAUDE.md` requires `remember`/`recall`/
   `improve`/`forget` to each be demonstrable as a first-class Cognee
   lifecycle operation, and the PRD names "Memory Evolution (`improve`)" as
   a core feature, not an implementation detail of ingestion. A demo
   script — and any future analytics/logging that wants to distinguish
   "you uploaded your first paper" from "your memory just grew" — needs a
   real symbol to point at, not a comment explaining that `improve` is
   secretly `ingest`.
2. **API stability.** Exposing `improve()` now, even as a thin wrapper,
   gives callers who reasonably expect a named `improve` operation (matching
   the product's own vocabulary) a stable contract today. If real
   behavioral divergence is ever needed — e.g. `improve()` re-checking
   existing `Hypothesis` stance against newly-ingested evidence, which
   plain re-`ingest()` doesn't currently do — it lands inside an already-
   public function signature, not as a breaking API addition.

Both functions still call one internal orchestration function
(`ingestion/pipeline.py`, §3) — the mechanism argument wasn't wrong, it was
just answering the wrong question. Two public names sharing one
implementation is a defensible, common pattern as long as the duplication
is *documented as deliberate*, not accidental — which is what this
revision does, rather than silently dropping the earlier reasoning (per
this project's rule against silently changing direction — §0 follows the
same discipline).

### 10.3 `search()` is not public; `update()` is not designed

Covered in §2.5. `search()`: exposing Cognee's own primitive breaks the
provider-opacity goal. `update()`: no demo-critical query needs source
editing; `forget()` + `ingest()` covers the rare case; and its real
semantics (does an edit preserve node identity across cognify runs, or
create a new generation?) are genuinely unresolved design questions not
worth answering speculatively. Better to leave it absent than to ship a
half-considered contract.

### 10.4 `SourceRecord` unifies `Paper`/`Experiment`/`ResearchNote`

Rejected: three near-identical dataclasses (`Paper`, `Experiment`,
`ResearchNote`), each with `id`/`title`/`date`/`source_uri`/`node_set` and
one or two type-specific fields. Chosen instead: one `SourceRecord` with a
`source_type` discriminator, because `ONTOLOGY.md` §3.2 *itself* already
defines these three as behaviorally identical — "source-anchored,"
"unit of forget()," "carries a `node_set` tag" — the unification mirrors
the ontology's own boundary rather than inventing one. **Named risk:** if a
source type later needs a genuinely distinct field with real behavioral
weight (e.g. `Experiment.config` driving different extraction logic), the
unification should be undone for that type specifically — acceptable,
flagged YAGNI, not a silent gamble.

### 10.5 Async-only, no sync wrapper

Cognee's API is async top-to-bottom; the only planned caller (FastAPI) is
async-native (`ARCHITECTURE.md` §9); no synchronous caller exists in this
project. A `asyncio.run()`-wrapping sync facade is easy to add later and
would be pure unused surface today.

### 10.6 Mode B is scaffolded, not built

Covered in §4.4. Named again here because it's the tradeoff most directly
answering the user's original instruction ("keep the provider abstraction
intact... capable of switching... with minimal changes"): this design
delivers the *seam* (a typed `Protocol`, a capability-reporting contract, a
`recall()` degraded-mode path already wired) without spending Milestone 2
effort on an implementation nothing currently demos against. That is the
"minimal changes later" guarantee — not a working Mode B today, but zero
rearchitecture when Mode B is eventually built, whatever its actual
capabilities turn out to be by then (§4.1).

### 10.7 What would make this design wrong

Stated plainly, so it can be checked against reality as Milestone 2
proceeds:

- If `ingest()`/`improve()` latency (§2.1, §2.2) turns out to dominate the
  demo badly at real corpus size (not the 4-document spike scale), the
  "background operation" note in §2.1 stops being a footnote and becomes a
  Milestone 3 backend requirement, not optional. (See §8 for the explicit
  budget this would blow.)
- If a real multi-hypothesis corpus needs more than "the caller passes
  `active_hypotheses` explicitly" (§2.1's noted limitation) — e.g. dozens
  of hypotheses that don't fit in one `custom_prompt` — the extraction
  strategy needs revisiting before Milestone 2 is "done," not after.
- If Mode B ever becomes demo-critical (not just "nice to have live
  infra"), §4.5's degraded-answer UX needs actual product design, not just
  an honest `degraded: bool` flag — that flag defers a real UX problem, it
  doesn't solve one. (This may resolve itself if a future Cognee Cloud
  release closes the capability gap in §4.1 — but this design should not
  assume that will happen on any particular timeline.)
- If users routinely re-ingest *edited* versions of the same source
  (§2.1's content-hash idempotency creates a new `SourceRecord` per edit,
  never updates one in place), the accumulation of near-duplicate sources
  per project is a real UX and graph-cleanliness problem this design punts
  on, not solves — `update()` (§2.6, §10.3) was deferred precisely because
  this question doesn't have an answer yet, not because it doesn't matter.

This document is the contract Milestone 2 implements against. Where
implementation reveals one of these assumptions is wrong, the fix is to
update this document and explain the conflict — the same rule §0 followed
— not to silently drift the code away from what's written here.

---

## 11. Addendum — pre-2.2 architecture review

Performed after the Milestone 2.1 skeleton existed, by tracing the
Milestone 1 spike's 7 steps against the then-current public API and asking
whether each was reproducible. Two real gaps were found; four cheap,
additive interface changes were applied in response. Nothing in
`ingest`/`improve`/`recall`/`forget`'s signatures changed.

**Gap 1 — no LLM-free evidence lookup.** The spike's
`find_contradiction_evidence()` step is pure graph traversal, zero LLM
calls. The v1.1 public API only exposed evidence bundled inside `recall()`,
which always requires a query and always calls the LLM — undercutting
design §1.1's own trust principle (structural claims must be verifiable
without an LLM) and blocking spike reproducibility outright. **Added:**
`find_evidence(*, project_id, relationship=CONTRADICTS, hypothesis_id=None)
-> list[Evidence]` (§2.5-adjacent; lives next to the read-only accessors
conceptually, implemented in `retrieval/evidence.py` since it composes
`graph.query.get_graph()` with `retrieval.evidence.build_evidence()`).
Defaults reproduce the spike's exact behavior.

**Gap 2 — no project reset.** The spike's `reset()` step has no public-API
equivalent; `forget()` only removes one source at a time. Investigating the
fix surfaced a real correctness finding, not just a gap: the spike's own
`reset()` calls `cognee.prune.prune_data()`/`prune_system()`, both
**global** (verified by signature inspection — no dataset argument) — more
destructive than the spike needed. `cognee.datasets.empty_dataset(dataset_id)`
is properly project-scoped. **Added:** `reset_project(*, project_id) -> None`,
specified to use the scoped call — an improvement over the spike's
behavior, not just a port of it.

**Three type adjustments**, applied because `find_evidence()` exposed them:

- `Evidence.relationship` widened from `Literal["SUPPORTS", "CONTRADICTS"]`
  to `RelationshipType | str` — the narrower type only made sense while
  evidence was reachable solely through the two-relationship
  `SUPPORTS`/`CONTRADICTS` path inside `recall()`; a general-purpose
  `find_evidence()` needs the same width `MemoryEdge.relationship` already has.
- `RecallStrategy` moved from `providers/base.py` to `models.py`. It was
  originally placed in `providers/base.py` because `MemoryProvider.query()`
  needed the type; per §3's own module responsibilities, `retrieval/router.py`
  *owns* strategy selection and `providers/` should only consume the type.
  The import direction had it backwards. Fixed while the fix was five lines;
  would have been a real refactor later.
- `RecallResult` gained `raw_llm_context: str | None = None`. The provider
  Protocol already had a place for this (`ProviderQueryResult.raw_context`,
  mirroring the spike's `only_context=True` capture) but nothing in the
  public model surfaced it — it would have been captured and silently
  dropped. Kept for the transparency/demo value of "show exactly what the
  LLM saw," consistent with the project's memory-transparency thesis; not
  used to compute `evidence`/`evidence_graph`, which remain strictly
  deterministic per §1.1.

**Findings surfaced but deliberately not acted on** (named for the record,
not fixed — no current requirement forces them, per the project's own
YAGNI discipline): `project_id: str` may need to become a richer type if
project metadata is ever needed; `SourceInput.content: str | bytes` may
need to become stream-based for large files; `active_hypotheses: list[str]`
and the module-level-function/no-`MemoryCore`-class design were already
named as breaking-change risks in §10.1/§10.7 and are reaffirmed, not
re-litigated.
