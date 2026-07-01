# MemoryOS — Architecture

Version: 1.0
Status: Draft for review (precedes the Cognee memory-core spike)

---

## 0. How to read this document

This document is organized **memory-core first**. The knowledge graph is the
product; the API and UI are thin layers that make the graph *visible* and
*queryable*. Read top-to-bottom:

1. Design principles — the non-negotiables every decision is measured against.
2. The research ontology — the single most important design artifact.
3. Data flow — how a raw PDF becomes a traversable graph and then an answer.
4. Cognee lifecycle mapping — remember / recall / improve / forget.
5. Components and why each exists.
6. Recall strategy — the `CONTRADICTS` centerpiece.
7. Backend API surface.
8. Frontend surfaces (deliberately reduced scope).
9. Tech stack, risks, milestones.

Where an exact Cognee API signature is asserted, it is marked **(verify in
spike)** — the spike (Milestone 1) exists precisely to confirm these before we
build anything on top of them.

---

## 1. Design principles

These are ranked. When two principles conflict, the higher one wins.

1. **The graph is the product.** Every feature must make persistent, relationship-aware memory more visible or more useful. If a feature would work identically on a stateless RAG app, it is not part of the MVP.
2. **Ontology-first, not extraction-first.** A generic entity graph ("entity soup") loses this hackathon. We commit to a small, explicit research ontology and force Cognee's extraction toward it. Meaningful edges (`CONTRADICTS`, `SUPPORTS`) are worth more than volume of nodes.
3. **One killer capability, proven early.** The demo spine is *"Which papers contradict our current research direction, and why?"* — a question a stateless LLM or vanilla RAG structurally cannot answer. Everything else is supporting cast.
4. **Cognee is the memory substrate, not a storage bucket.** We use its cognify pipeline, custom graph models, ontology hints, graph-traversal search, and deletion — not just `add()` + vector search.
5. **Separation of concerns.** Memory logic lives in one isolated module (`memory_core`). The backend orchestrates; the frontend presents. No Cognee calls leak into route handlers or React.
6. **De-risk before you build.** The hardest, least-certain part (graph quality) is proven in an isolated script before a single line of UI is written.

---

## 2. The research ontology (most important section)

### 2.1 Why a custom ontology at all

Out of the box, `cognee.cognify()` performs LLM-driven entity/relationship
extraction and produces a *generic* knowledge graph. For arbitrary text this is
impressive but unpredictable: it will not reliably produce a `CONTRADICTS` edge
between a hypothesis and a paper, because "contradiction" is a domain judgment,
not a surface-level co-occurrence.

MemoryOS therefore constrains extraction with a **domain ontology**: an explicit
vocabulary of entity types and a closed set of typed relationships, plus their
legal domain→range pairings. Cognee supports steering extraction toward a
provided ontology and/or custom graph models **(verify in spike)**; we exploit
this so the graph is *predictable enough to demo* and *rich enough to reason
over*.

### 2.2 Entity types (nodes)

| Entity | Definition | Key attributes |
|---|---|---|
| `Paper` | A research paper / article ingested as a source document. | title, authors[], year, source_uri, abstract |
| `Author` | A person credited on a paper. | name |
| `Method` | A technique, model, or algorithm (e.g., "YOLO11", "contrastive learning"). | name, aliases[] |
| `Dataset` | A named dataset used for training/evaluation (e.g., "COCO"). | name |
| `Benchmark` | A metric/task under which methods are compared (e.g., "mAP@0.5"). | name, task |
| `Experiment` | A researcher-run trial captured in notes/logs. | title, date, config |
| `Hypothesis` | A claim the researcher currently believes or is testing. | statement, status(active/retired) |
| `Finding` | A concrete result or conclusion (from a paper or an experiment). | statement, quantitative_value |
| `ResearchNote` | A freeform markdown note by the researcher. | title, body |
| `Topic` | A thematic cluster used for navigation/grouping. | name |

`Paper`, `Experiment`, `ResearchNote` are **source-anchored** (they map to an
ingested artifact and are the unit of `forget()`). The rest are **extracted**
entities that may be referenced by many sources.

### 2.3 Relationship types (typed edges)

Closed set. Each edge has a defined **domain** (source type) and **range**
(target type). Constraining domain/range is what keeps the graph legible and
makes traversal queries tractable.

| Relationship | Domain → Range | Meaning |
|---|---|---|
| `WRITTEN_BY` | Paper → Author | Authorship. |
| `USES` | Paper \| Experiment → Method \| Dataset | A source employs a method or dataset. |
| `EVALUATES` | Paper \| Experiment → Method (on) Benchmark | A source measures a method under a benchmark. |
| `SUPPORTS` | Paper \| Finding \| Experiment → Hypothesis | Evidence that strengthens a hypothesis. |
| `CONTRADICTS` | Paper \| Finding \| Experiment → Hypothesis | Evidence that weakens/refutes a hypothesis. |
| `DERIVED_FROM` | Method \| Finding → Method \| Paper | Lineage: a method/finding builds on a prior one. |
| `REFERENCES` | Paper → Paper | Citation / mention. |
| `ABOUT` | Paper \| Note \| Experiment → Topic | Thematic grouping. |

**The two edges that win the demo are `SUPPORTS` and `CONTRADICTS`**, because
they encode *agreement and disagreement across the corpus and across sessions* —
the thing persistent graph memory uniquely enables. The ontology is designed so
these edges always connect *evidence* (Paper/Finding/Experiment) to a
*Hypothesis*, giving us a clean, well-typed traversal target.

### 2.4 How the ontology is enforced in Cognee

> **Verified by runtime introspection of installed Cognee 1.2.2** (not just
> docs — the public docs and repo `skill.md` were both partly wrong for this
> version). Signatures confirmed via `_verify_api.py`.

Three levers exist in 1.2.2; we combine the first two:

1. **Extraction steering — `cognify(custom_prompt="…")` (primary lever).** The
   default extraction `graph_model` is `KnowledgeGraph{nodes, edges}` where each
   edge carries a free-form `relationship_name` chosen by the LLM. We use
   `custom_prompt` to inject (a) the closed relationship vocabulary
   (`SUPPORTS`/`CONTRADICTS`/`USES`/…), (b) the entity types, and (c) the active
   `Hypothesis` statement, instructing the extractor to classify evidence as
   SUPPORTS/CONTRADICTS/neutral. This is what actually drives the demo-critical
   edges.
2. **Ontology grounding — OWL resolver via `cognify(config=…)`.** Wiring:
   `RDFLibOntologyResolver(ontology_file="research_ontology.owl")` attached as
   `config={"ontology_config": {"ontology_resolver": resolver}}`. The resolver
   does **fuzzy entity matching** against the ontology (normalization/enrichment
   and consistency), not primary relation extraction. The OWL file is the
   projection of `ONTOLOGY.md`. Correction to an earlier assumption: there is
   **no `ontology_file_path=` argument** to cognify in 1.2.2 — it goes through
   the resolver+config path above.
3. **Custom `graph_model=` (pydantic BaseModel).** This argument *does* exist
   (contra `skill.md`). A subclass could hard-constrain node/edge types, but it
   risks over-fitting extraction and is heavier than `custom_prompt`. Held in
   reserve; not used unless (1)+(2) prove insufficient.

If (1)+(2) cannot produce reliable `CONTRADICTS` edges, the fallback is a
**two-pass ingestion**: cognify for base entities/findings, then a targeted pass
that asks the LLM to classify each (evidence, hypothesis) pair and writes those
edges via `DataPoint` + `add_data_points(custom_edges=…)`. Documented so the
decision is explicit, not improvised. The spike tells us which path we are on.

### 2.5 `node_set` tagging for scoped memory & forget

Every ingested artifact is tagged with a `node_set` (e.g., per project, and per
source document id) at `add()` time **(verify in spike)**. This gives us:

- **Scoped recall** — retrieval filtered to the active project.
- **Clean forget()** — deletion of a source by its node_set/document id, so the
  graph stays consistent after removal.

---

## 3. Data flow

### 3.1 Ingestion → graph (the `remember` + `improve` path)

```
          ┌─────────────┐
 PDF /    │  Ingestion   │  PyMuPDF extracts text (PDF); markdown/URL/text
 MD /  ─► │  Adapter     │  normalized to plain text + metadata
 URL      └──────┬───────┘
                 │  normalized document + node_set tag
                 ▼
          ┌─────────────┐
          │ cognee.add() │  document enters Cognee's data store, tagged
          └──────┬───────┘
                 ▼
          ┌───────────────────┐
          │ cognee.cognify()  │  LLM extraction steered by:
          │   + graph model   │   - custom pydantic graph models
          │   + ontology      │   - research ontology vocabulary
          └──────┬────────────┘
                 ▼
          ┌───────────────────┐
          │  Hybrid store      │  graph DB (entities+typed edges)
          │  graph + vectors   │  + vector index (chunk embeddings)
          └──────┬────────────┘
                 ▼
        graph grows & re-links across sessions  ──►  improve()
```

Each new artifact runs the same path; because Cognee resolves entities across
documents, ingesting a new paper *links into* the existing graph (a shared
`Method` node gains new edges) rather than creating an island. That emergent
re-linking **is** the visible "memory evolution" moment in the demo.

### 3.2 Query → answer (the `recall` path)

```
 user question
      │
      ▼
 ┌──────────────────┐   Router picks a Cognee SearchType based on intent:
 │  Recall Router    │   - relationship/why  → graph traversal (INSIGHTS/GRAPH)
 │  (backend)        │   - factual/summary   → graph-completion / semantic
 └───────┬──────────┘   - "contradicts?"     → dedicated traversal template
         ▼
 ┌──────────────────┐
 │ cognee.search()   │  returns nodes, edges, and/or synthesized answer
 └───────┬──────────┘
         ▼
 ┌──────────────────┐
 │  Answer + evidence│  LLM (Claude) narrates the traversal result;
 │  subgraph         │  backend returns BOTH prose AND the subgraph so the
 └───────┬──────────┘  UI can highlight the exact nodes/edges used.
         ▼
   frontend: prose answer + highlighted subgraph
```

Returning the **evidence subgraph alongside the prose** is deliberate: it is the
proof that the answer came from relationship-aware memory, not a black-box
vector lookup. This is a core UX/judging lever.

---

## 4. Cognee memory lifecycle mapping

> **API verified against Cognee 1.2.2.** Changes from earlier assumptions:
> `SearchType.INSIGHTS` no longer exists (use `GRAPH_COMPLETION` + `only_context`
> / `CYPHER`); there is no `cognee.delete()` (deletion is dataset-/prune-scoped).

| Lifecycle op | Triggered by | Cognee mechanism (verified 1.2) | Visible demo effect |
|---|---|---|---|
| `remember()` | Upload PDF / note / URL | `cognee.add(data, node_set=[…])` + `cognee.cognify(ontology_file_path=…, custom_prompt=…)` | New nodes/edges appear in the graph |
| `recall()` | User asks a question | `cognee.search(query_text, query_type=SearchType.GRAPH_COMPLETION, node_name=[…])`; `only_context=True` / `verbose=True` to capture the evidence subgraph | Prose answer + highlighted evidence subgraph |
| `improve()` | Ingesting *additional* research | re-`add()` + re-`cognify()`; cross-document entity resolution re-links shared nodes | Existing nodes gain new edges; graph densifies |
| `forget()` | Delete a source | **`cognee.delete(data_id, dataset_id, mode='soft'\|'hard')`** exists (verified). `mode='hard'` also removes now-orphaned entities. Fallback: dataset-per-source + `datasets` ops. | Source and its exclusive nodes vanish; shared nodes persist; graph stays consistent |

All four are first-class in the demo script; none is an afterthought. The single
most under-appreciated one is `improve()` — the *re-linking* of a previously
ingested `Method`/`Hypothesis` when a new paper arrives is the clearest visual
argument for "memory that gets better because it remembers."

---

## 5. Components & rationale

```
┌────────────────────────────────────────────────────────────┐
│ Frontend (Next.js / React / Tailwind)                       │
│   • Graph surface (Cytoscape.js)  • Recall panel            │
└───────────────▲────────────────────────────────────────────┘
                │ REST/JSON
┌───────────────┴────────────────────────────────────────────┐
│ Backend (FastAPI)                                           │
│   • routes/        thin HTTP handlers, no memory logic      │
│   • services/      orchestration (ingest, recall, forget)   │
│   • schemas/       pydantic request/response models         │
└───────────────▲────────────────────────────────────────────┘
                │ in-process calls
┌───────────────┴────────────────────────────────────────────┐
│ memory_core/  (isolated Cognee integration)                 │
│   • ontology.py    entity/edge models + vocabulary          │
│   • ingest.py      add() + cognify() orchestration          │
│   • recall.py      search routing + traversal templates     │
│   • forget.py      scoped deletion                          │
│   • adapters/      pdf (PyMuPDF), markdown, url, text        │
└───────────────▲────────────────────────────────────────────┘
                │
        ┌───────┴────────┐
        │     Cognee      │  hybrid graph + vector store, LLM extraction
        └────────────────┘
```

Why each exists:

- **`memory_core` is a standalone module, not backend code.** It must be
  runnable *without* FastAPI (that is exactly what the spike does). This keeps
  the risky part testable in isolation and prevents web concerns from
  contaminating memory logic.
- **`ontology.py` is separate from ingestion.** The ontology is a shared
  contract used by both ingestion (to steer extraction) and recall (to write
  traversal templates against known edge types). Isolating it makes the schema
  the single source of truth.
- **Backend `services/` vs `routes/`.** Handlers stay dumb (parse, call service,
  serialize). All orchestration is in services so it is unit-testable and the
  API can evolve without touching memory logic.
- **Frontend is presentation-only.** No business rules; it renders the subgraph
  and prose the backend returns.
- **Cytoscape.js** over heavier graph libs: purpose-built for interactive graph
  viz (zoom/pan/click/highlight), which is the entire point of the graph
  surface, with minimal integration cost.

---

## 6. Recall strategy — the `CONTRADICTS` centerpiece

The recall router maps question intent to a retrieval strategy. Cognee 1.2
`SearchType` values in parentheses (verified).

| Intent | Example | Strategy |
|---|---|---|
| Relationship / "why" | "Why do we prefer YOLO11?" | `GRAPH_COMPLETION`; subgraph via `only_context=True`. Traversal from the `Hypothesis`/`Method` node along `SUPPORTS`/`USES`/`EVALUATES` |
| Contradiction | "Which papers contradict our current direction?" | `GRAPH_COMPLETION` for the answer + `only_context=True` for the evidence subgraph. For a deterministic subgraph, `CYPHER` traversal: active `Hypothesis` ← `CONTRADICTS` ← evidence → source |
| Gap analysis | "Which datasets were never evaluated?" | `CYPHER` — `Dataset` nodes with no incoming `EVALUATES` edge (structural query; no LLM needed) |
| Factual / summary | "What does Paper A claim?" | `GRAPH_COMPLETION` / `RAG_COMPLETION` scoped via `node_name=[source_id]` |

**Evidence subgraph mechanism (verified):** the answer prose comes from
`GRAPH_COMPLETION`; the accompanying subgraph is obtained by re-issuing the query
with `only_context=True` (returns the graph context sent to the LLM) or, where we
need exact, deterministic triplets, via a `CYPHER` query against the same graph.
Per Principle 4 (determinism), structural queries (gap analysis, exact
contradiction traversal) prefer `CYPHER`; only genuinely semantic questions use
LLM completion.

The contradiction and gap queries are the demonstrations of capability that a
stateless model cannot replicate, because they require the *whole accumulated
graph*, not a single document in context. They are therefore the primary demo
beats and the recall router's first-class templates.

---

## 7. Backend API surface (MVP)

Minimal, resource-oriented. All under `/api`.

| Method | Path | Purpose | Lifecycle |
|---|---|---|---|
| `POST` | `/ingest` | Upload PDF/markdown/URL/text → remember | remember/improve |
| `GET` | `/graph` | Full (or project-scoped) graph for visualization | — |
| `POST` | `/recall` | Natural-language question → answer + evidence subgraph | recall |
| `DELETE` | `/sources/{id}` | Remove a source and reconcile the graph | forget |
| `GET` | `/stats` | Counts (papers, experiments, notes, hypotheses) for the header strip | — |

`GET /graph` returns nodes/edges in a Cytoscape-ready shape. `POST /recall`
returns `{ answer, evidence: { nodes, edges } }` so the UI can highlight exactly
what the traversal used.

> **`DELETE /sources/{id}` — mechanism verified.** Cognee 1.2 exposes
> `cognee.delete(data_id, dataset_id, mode='soft'|'hard')`. `soft` removes the
> source; `hard` also prunes orphaned entities — which matches ONTOLOGY.md §7's
> "exclusive extracted nodes go, shared nodes stay." The spike will confirm the
> exact orphan-handling behavior; target behavior is fixed in ONTOLOGY.md §7.

---

## 8. Frontend surfaces (reduced scope — decision recorded)

The PRD lists five pages (Dashboard, Upload, Graph, Chat, Timeline). For the
hackathon MVP we deliberately collapse to **two surfaces on one screen**:

1. **Knowledge Graph (the star).** Full-canvas interactive Cytoscape graph.
   Ingest is a drop-zone overlay on this canvas. A small header strip shows the
   `/stats` counts. Node click → inspector panel with attributes + neighbors.
2. **Recall panel (docked).** Natural-language input; renders the prose answer
   and, critically, **highlights the evidence subgraph in the main canvas**.

Postponed (explicitly, to protect scope): standalone Dashboard page, Timeline
page, multi-project switching UI. None of these improves the core demonstration
enough to justify the build cost; each can be added post-hackathon.

Rationale: two tightly-coupled surfaces (graph + recall that lights up the
graph) tell the "memory is visible and reasoned-over" story more forcefully than
five loosely-coupled pages.

---

## 9. Tech stack

| Layer | Choice | Note |
|---|---|---|
| Memory | Cognee | Hybrid graph + vector; ontology-steered cognify |
| Backend | FastAPI (Python) | Async, pydantic-native, pairs cleanly with Cognee |
| PDF parsing | PyMuPDF | Fast, reliable text extraction |
| LLM | Claude (latest Opus/Sonnet) | Extraction assist + answer narration |
| Frontend | Next.js + React + Tailwind | Standard, fast to build |
| Graph viz | Cytoscape.js | Interactive graph rendering |
| Store backends | Cognee defaults (local) | Local graph + vector stores for the demo; no cloud dependency |

### 9.1 Execution modes & provider abstraction

MemoryOS must run in two execution modes with **minimal code change** between
them. This is a deliberate architectural contract, verified against the
installed Cognee 1.2.2 source.

**Mode A — Local pipeline, direct LLM provider (Milestone 1 + default demo).**
The cognify/search pipeline runs in-process; only inference is delegated to an
external provider. Provider selection is **fully environment-driven** — no
provider name appears in code:

| Concern | Env var(s) | Notes |
|---|---|---|
| Extraction/recall LLM | `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY` | `anthropic`, `openai`, `ollama`, `gemini`, `mistral`, `azure`, `bedrock`, `llama_cpp`, `custom` all supported |
| Embeddings | `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS` | `fastembed` = local & free (no key); or a hosted provider |

Switching Anthropic ↔ OpenAI ↔ local Ollama is a `.env` edit, **zero code
change** — this is the provider abstraction, and it lives in configuration, not
in a hand-rolled adapter layer. The spike uses `anthropic` + local `fastembed`.

**Mode B — Cognee Cloud (managed backend, candidate for production).**
`await cognee.serve(url=..., api_key=...)` connects the SDK to a hosted Cognee
tenant and installs a module-level remote client
(`api/v1/serve/state.py`). Once connected, `cognee.cognify()` / `search()`
route to the cloud (`api/v1/cognify/cognify.py:201`); inference **and** the
graph live server-side, billed to Cognee Cloud credits — no local LLM key
needed.

**Verified caveats for Mode B (why it is *not* a drop-in env swap):**
- The remote `cognify()` branch forwards only
  `datasets, chunk_size, chunks_per_batch, custom_prompt, run_in_background`.
  It **drops `config` (our OWL `ontology_resolver`) and `graph_model`** — so
  two of our three extraction-quality levers do not reach the cloud; only
  `custom_prompt` survives.
- The knowledge graph is built and stored on the cloud tenant, so the local
  deterministic path (`get_graph_engine().get_graph_data()`, our evidence
  subgraph) sees nothing until the graph is pulled back via `sync`/`push`.

**Consequence for design:** the `memory_core` module (Milestone 2) exposes one
internal interface (`ingest / recall / forget / evidence`) with two
implementations behind a single config flag — Mode A (local) and Mode B
(cloud). Mode A is authoritative for the graph-quality demo (keeps the
ontology + deterministic evidence). Mode B is the "real deployed infrastructure"
option for the live demo, adopted only after Milestone 1 proves the graph, and
only if the ontology loss is acceptable or mitigated server-side.

---

## 10. Risks & mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Cognee won't reliably emit `CONTRADICTS`/`SUPPORTS` edges | Kills the centerpiece | **Spike first.** Ontology + graph models; documented two-pass extraction fallback (§2.4) |
| Entity resolution too weak → islands instead of re-linking | Undermines `improve()` demo | Validate cross-document linking in spike with 2–3 overlapping papers |
| Extraction latency makes live upload feel slow | Weak demo pacing | Pre-ingest most of the corpus; upload *one* paper live to show growth |
| Graph too dense/noisy to read on screen | Weak UX | Ontology constrains node/edge types; UI filters by type; highlight-on-recall focuses attention |
| Non-determinism between runs | Demo fragility | Freeze a prepared project state; script the exact demo queries |
| API-key / environment setup unknown | Blocks the spike | **Resolved:** `anthropic` LLM + local `fastembed` embeddings, env-driven (§9.1) |

---

## 11. Milestones

1. **Cognee memory-core spike (next).** Standalone script: ingest 2–3
   overlapping sample papers → cognify with ontology + graph models → run the
   `CONTRADICTS` and a "why" traversal → print nodes/edges. **Exit criterion:**
   we can produce a legible graph with at least one correct `CONTRADICTS` edge,
   and we know whether the fallback (§2.4) is needed. Everything else waits on
   this.
2. **`memory_core` module.** Promote the spike into `ingest/recall/forget` with
   the ontology as the shared contract; add adapters (pdf/md/url/text); unit
   tests on a fixed fixture corpus.
3. **Backend API.** FastAPI routes/services over `memory_core` (§7).
4. **Frontend.** Graph canvas + recall panel with subgraph highlighting (§8).
5. **Demo hardening.** Prepared project state, scripted queries, polish.

---

## 12. Open questions

- **Resolved — ontology & extraction APIs:** OWL via `cognify(ontology_file_path=)`, steering via `custom_prompt=`, `node_set` at `add()`, structured writes via `DataPoint` + `add_data_points`. (§2.4)
- **Resolved — corpus:** the three synthetic papers with a deliberate contradiction are specified in ONTOLOGY.md §9.
- **Resolved — LLM provider/key:** `anthropic` for extraction/recall, local `fastembed` (`BAAI/bge-small-en-v1.5`, 384-dim) for embeddings — env-driven, zero code coupling. Cognee Cloud evaluated and deferred to production (Mode B, §9.1): its remote `cognify()` drops our ontology resolver, so it is unsuitable for the graph-quality spike.
- **Open — scoped `forget()`:** no per-node delete in 1.2; dataset-per-source is the leading approach (§7, ONTOLOGY.md §7). Confirmed in spike / Milestone 2.
