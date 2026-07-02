# MemoryOS — Progress Log

Session handoff doc. Read this first when resuming work — it says exactly
where things stand and what the next action is. `CLAUDE.md` has the durable
project charter (role, principles, philosophy); this file has the current
state, which changes often.

Last updated: 2026-07-02.

---

## Milestone 1 (Memory Core Spike) — COMPLETE ✅

**Verdict: PASS. All 10 success criteria passed**, including the one
genuinely uncertain criterion (`CONTRADICTS` edge extraction). Full polished
writeup: [`Docs/MILESTONE_1_REPORT.md`](MILESTONE_1_REPORT.md). Raw run
evidence: `prototype/memory_core_spike/outputs/` (`validation_report.md`,
`evidence.json`, `graph.json` — committed as checkpoint evidence, an
explicit exception to the normal "outputs are regenerable, don't commit
them" rule).

### Objective

Prove — before any backend/frontend work starts — that Cognee 1.2.2 can
reliably build the research knowledge graph defined in `Docs/ONTOLOGY.md`
from a small synthetic corpus, and in particular that it can extract the
**demo-critical `CONTRADICTS` relationship** (evidence that disagrees with an
active hypothesis). Per project rules, Milestone 2 does not start until this
is validated with evidence, not assumption.

### Implementation decisions

- **Low-level Cognee API** (`add`/`cognify`/`search`/`prune`) over the
  high-level `remember()`/`recall()` — needed direct control over the
  ontology resolver and `custom_prompt`.
- **Synthetic corpus** (1 hypothesis note + 3 papers) over real PDFs —
  deterministic, guaranteed to contain a genuine contradiction, no
  OCR/parsing noise. Full corpus spec: `ONTOLOGY.md` §9 ("Worked example").
- **Ontology-first extraction**: the OWL projection of `ONTOLOGY.md`
  (`prototype/memory_core_spike/ontology/research_ontology.owl`) is passed
  as `RDFLibOntologyResolver`, and a `custom_prompt` explicitly names the
  active hypothesis and instructs the extractor how to classify evidence
  (`SUPPORTS` vs `CONTRADICTS`) — see §6.2 of `ONTOLOGY.md` for the
  reasoning ("Tier 3" edges need explicit steering, not just a schema).
- **Provider config** (verified against the installed package, not
  assumed): LLM = **Anthropic** (`LLM_PROVIDER=anthropic`, dedicated adapter
  using the real `anthropic` SDK, not a litellm shim); Embeddings =
  **`fastembed`** (`BAAI/bge-small-en-v1.5`, local, free, no API key).
  Cognee Cloud was investigated and deliberately deferred to production —
  its remote `cognify()` path drops the ontology resolver and `graph_model`
  (verified in `cognify.py:201`), which would blind the deterministic
  evidence-subgraph traversal this spike depends on. Full reasoning:
  `ARCHITECTURE.md` §9.1.
- **Design principle enforced throughout `main.py`**: structural facts
  (node/edge counts, relationship types, the evidence subgraph) are computed
  **deterministically by graph traversal**, never by asking the LLM. The LLM
  is used for exactly one thing: the final natural-language answer. This
  means the validation report's PASS/FAIL claims are backed by inspectable
  graph data, not by trusting a model's self-report.

### Validation methodology

`prototype/memory_core_spike/main.py` runs a single deterministic pipeline:

1. `reset()` — prune data + system state, so every run starts clean.
2. `remember()` — `cognee.add()` the 4 fixtures (each tagged with a
   `node_set` for provenance), then `cognee.cognify()` with the OWL
   ontology resolver + `custom_prompt`.
3. `dump_graph()` — pull the raw graph via `get_graph_engine().get_graph_data()`,
   normalize nodes/edges into plain dicts, write `outputs/graph.json`.
4. `find_contradiction_evidence()` — **pure graph traversal**, no LLM: filter
   edges to `rel_norm == "CONTRADICTS"`, build the evidence subgraph.
5. `recall_answer()` — the one LLM step: `cognee.search(SearchType.GRAPH_COMPLETION)`
   for a natural-language answer to *"Which papers contradict our current
   hypothesis, and why?"*, plus `only_context=True` to capture the graph
   context the LLM actually saw.
6. `build_report()` — scores 10 explicit success criteria as PASS/PARTIAL/FAIL,
   each with a concrete evidence string, and writes `outputs/validation_report.md`.

The 10 criteria (installs, ontology accepted, ingestion, graph creation,
entity extraction, Tier-1 relationships present, ≥1 correct `CONTRADICTS`
edge, graph traversal works, NL recall works, evidence subgraph produced)
are listed in full with results in `MILESTONE_1_REPORT.md`.

### Bugs encountered & fixes (all applied, all in the committed `main.py`)

1. **`ModuleNotFoundError: No module named 'anthropic'`** — the `anthropic`
   SDK wasn't installed in `prototype/.venv` even though Cognee's
   `AnthropicAdapter` imports it directly (not a litellm passthrough).
   Fix: `pip install anthropic` into the venv.
2. **`TypeError: 'module' object is not callable`** on
   `RDFLibOntologyResolver(...)`** — Cognee's package layout has a submodule
   literally named `RDFLibOntologyResolver.py` inside the
   `cognee.modules.ontology.rdf_xml` package, which shadows the class of the
   same name at the package's `__init__` level for a plain
   `from ... import RDFLibOntologyResolver`. Fix: import from the fully
   qualified submodule path,
   `from cognee.modules.ontology.rdf_xml.RDFLibOntologyResolver import RDFLibOntologyResolver`.
3. **`UnicodeEncodeError` on the final `print(report)`** — Windows' default
   console codepage (cp1252) can't render the ✅ emoji used in the report.
   This happened *after* all artifacts were already written to disk
   correctly (UTF-8 file writes are unaffected) — only the console echo
   crashed. Fix: reconfigure `sys.stdout` to UTF-8 at the top of `main.py`
   when the platform default isn't already UTF-8.
4. **Billing, not a code bug**: the first authenticated run failed everywhere
   with `Your credit balance is too low to access the Anthropic API`. Not a
   spike defect — required adding credits to the Anthropic account before
   any LLM call could succeed.

### Final result

**Overall: PASS.** 58 nodes / 180 edges from 4 short source documents.
`CONTRADICTS`: 2 edges (both correctly identifying the RT-DETR paper as
contradicting the YOLO11 hypothesis, per the fixture design). `SUPPORTS`: 5
edges. All Tier-1 control relationships (`WRITTEN_BY`, `USES`, `REFERENCES`,
`ABOUT`) present. The `GRAPH_COMPLETION` natural-language answer correctly
named the contradicting paper and cited the specific 2.1 mAP finding.
Full table and raw evidence: `MILESTONE_1_REPORT.md` and
`prototype/memory_core_spike/outputs/validation_report.md`.

### Lessons learned

- **Runtime introspection beat documentation** repeatedly this milestone —
  the correct import path for the ontology resolver, the Anthropic adapter's
  exact dependency, and the Cognee Cloud routing behavior were all only
  discoverable by reading the installed package source, not by trusting web
  docs (which are stale/wrong for 1.2.2 on several points; see
  `ARCHITECTURE.md` for the specific deltas).
  Practical rule going forward: **when integrating an unfamiliar Cognee
  surface, verify the exact import path / call signature against the
  installed package before writing code that depends on it.**
- **Ontology + `custom_prompt` steering was sufficient** to get correct
  `CONTRADICTS` extraction on the first successful run — the two-pass
  `DataPoint`/`add_data_points` fallback documented in `ARCHITECTURE.md`
  §2.4 was never needed. Worth remembering if Milestone 2's real corpus
  (more sources, subtler contradictions) turns out to need it after all.
- **Environment/dependency errors and logic errors look identical in a
  Rich traceback** — the `anthropic` import failure and the resolver
  import-path failure both surfaced as generic exceptions deep in Cognee's
  pipeline; isolating "is this my code or the environment" required reading
  the traceback's innermost frame each time, not the outermost one.
- **File writes happened before the crash** in the Unicode bug — a reminder
  that `build_report()` writing to disk and `print(report)` echoing to
  console are two independent operations; the artifacts were valid even
  while the process still exited non-zero. Worth checking `outputs/` before
  assuming a non-zero exit code means the run produced nothing.

### Architectural implications for Milestone 2

- The provider split (env-driven `LLM_PROVIDER`/`EMBEDDING_PROVIDER`, no
  custom adapter code) worked with zero code changes across the whole
  milestone — confirms the plan in `ARCHITECTURE.md` §9.1 (Mode A local /
  Mode B cloud behind one config flag) is the right shape for
  `memory_core`'s provider boundary.
- The ontology resolver + `custom_prompt` pairing is now a proven pattern —
  `memory_core`'s `ingest()` should keep both as first-class, versioned
  inputs (not hardcoded like the spike), since they are what made Tier-3
  edge extraction reliable.
- The deterministic-traversal / LLM-only-for-NL-answer split
  (`find_contradiction_evidence()` never touches the LLM) should carry
  forward unchanged into `memory_core.recall()` and any UI evidence-subgraph
  feature — it is the reason the validation report's claims are trustworthy,
  and the same trustworthiness matters for the product's judge-facing demo.

---

## Where we are now

**Milestone 1 is done and checkpointed.** Milestone 2 (`memory_core` module)
has **not** been started — per explicit instruction, no architectural work
begins until this checkpoint is committed. See the assistant's proposed
Milestone 2 plan in the conversation for the next-session starting point, and
`ARCHITECTURE.md` §11 for the originally planned milestone sequence
(`memory_core` → Backend API → Frontend → Demo hardening).

---

## Decisions log (don't re-litigate these without a reason)

- Low-level Cognee API (`add`/`cognify`/`search`) chosen over high-level
  `remember()`/`recall()` for the spike — more control over ontology/config.
- Synthetic corpus (3 papers + 1 hypothesis note) chosen over real PDFs for
  the spike — deterministic, guaranteed contradiction, no OCR/parsing noise.
- UI scope reduced from 5 pages to 2 surfaces early in the project (before
  this log started) — protect against scope creep per `CLAUDE.md`.
- Provider abstraction lives in environment config (`LLM_PROVIDER`,
  `EMBEDDING_PROVIDER`, etc.), not a hand-rolled adapter layer — switching
  providers is a `.env` edit. Do not build a custom provider abstraction on
  top of this; Cognee already provides one.
- Milestone 1's `outputs/` (`validation_report.md`, `evidence.json`,
  `graph.json`) are committed as a one-time checkpoint exception to the
  general "spike outputs are regenerable, don't commit them" `.gitignore`
  rule — they are the evidence backing `MILESTONE_1_REPORT.md`'s claims.
  Future re-runs of the spike still shouldn't be committed by default.
