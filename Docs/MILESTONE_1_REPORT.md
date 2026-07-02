# Milestone 1 Report — Cognee Memory Core Spike

**Status: PASS.** **Date: 2026-07-02.** **Author: MemoryOS engineering.**

This report documents the validation of MemoryOS's foundational assumption:
that Cognee's hybrid graph-vector memory can reliably build the research
knowledge graph the product depends on — including the one relationship type
that makes MemoryOS more than a chatbot with a database attached.

---

## 1. Why this spike exists

MemoryOS's thesis is that persistent, relationship-aware memory changes how
researchers work with AI. The single clearest demonstration of that thesis
is answering: *"which evidence contradicts what I currently believe?"* — a
question a stateless model, and a vanilla RAG pipeline, cannot answer,
because neither maintains typed relationships between claims over time.

Before committing to a backend, a frontend, or a demo script built on top of
Cognee, we needed to know — with evidence, not assumption — whether Cognee
1.2.2 can:

1. ingest a small research corpus and build a typed knowledge graph from it,
   constrained to a specific ontology;
2. extract the low-risk "connective tissue" relationships (authorship, usage,
   citation) that any graph extraction pipeline should get right;
3. extract the **high-risk** `SUPPORTS`/`CONTRADICTS` relationships that
   require the extractor to make a judgment call, not just find a fact; and
4. answer a natural-language question about the graph, backed by a
   deterministic (auditable, not LLM-hallucinated) evidence subgraph.

If (3) failed, the core product thesis would need to change before any other
code was written. This milestone exists to find that out early and cheaply.

---

## 2. The ontology

The full schema is `Docs/ONTOLOGY.md` (source of truth). Summary:

- **10 entity types**: `Paper`, `Author`, `Method`, `Dataset`, `Benchmark`,
  `Experiment`, `Hypothesis`, `Finding`, `ResearchNote`, `Topic`.
- **8 relationship types**, each with an explicit domain/range constraint:
  `WRITTEN_BY`, `USES`, `EVALUATES`, `SUPPORTS`, `CONTRADICTS`,
  `DERIVED_FROM`, `REFERENCES`, `ABOUT`.
- A closed, small vocabulary by design — an open vocabulary produces "entity
  soup" (many nodes, vague edges) that defeats the traversal queries
  MemoryOS is built around. See `ONTOLOGY.md` §2 and §8 for the full
  rationale and rejected alternatives.
- The ontology is projected into OWL 2
  (`prototype/memory_core_spike/ontology/research_ontology.owl`) and passed
  to Cognee via `RDFLibOntologyResolver`, so the graph extractor is
  constrained to this vocabulary rather than inventing its own labels.

`ONTOLOGY.md` §6.2 pre-classifies each relationship into an extraction
confidence tier — **this classification is what defined the spike's success
criteria before any code was run**, so the bar for "pass" was set in
advance, not adjusted after seeing results:

| Tier | Relationships | Expected difficulty |
|---|---|---|
| 1 (low risk) | `WRITTEN_BY`, `ABOUT`, `REFERENCES`, `USES` | Explicit in text/metadata |
| 2 (medium) | `EVALUATES`, `DERIVED_FROM` | Usually signposted |
| 3 (high risk) | `SUPPORTS`, `CONTRADICTS` | Requires judgment against a stated hypothesis |

---

## 3. Why `CONTRADICTS` was the highest-risk feature

`CONTRADICTS` is structurally different from every other edge in the schema:

- Every other relationship is a **fact extraction** — "who wrote this,"
  "what dataset was used," "what does this cite." The correct edge is stated
  or trivially inferable from the text.
- `CONTRADICTS` (and its counterpart `SUPPORTS`) is a **judgment**: the
  extractor must hold an active hypothesis in mind, read a separate claim,
  and decide whether that claim *weakens* the hypothesis — a form of
  reasoning, not lookup. Two papers can both be "about" the same method
  without one contradicting the other; the model has to understand the
  *stance* of a finding relative to a belief stated elsewhere in the corpus.
- It is also the edge the entire product narrative depends on. If
  `CONTRADICTS` extraction is unreliable, MemoryOS's headline demo query
  ("what contradicts my current direction?") is unreliable, and no amount of
  UI polish fixes that.

Because of this, `ONTOLOGY.md` names `CONTRADICTS` the single edge type with
its own explicit mitigation strategy (§6.2): provide the active hypothesis
verbatim in a `custom_prompt`, instruct the extractor to classify each claim
against it, and — if that proves unreliable — fall back to an explicit
two-pass classification step (`ARCHITECTURE.md` §2.4) that asks the LLM to
label each (`Finding`, `Hypothesis`) pair directly rather than hoping it
falls out of open-ended extraction.

---

## 4. How validation was performed

### 4.1 Fixture corpus (the acceptance test)

Four short synthetic documents (`prototype/memory_core_spike/fixtures/`),
specified in `ONTOLOGY.md` §9 before implementation began:

- **`note_hypothesis.md`** — states the active hypothesis: *"YOLO11 is the
  best object detector for our real-time use case."*
- **Paper A** ("YOLO11: Real-Time Detection at 2ms") — supports the
  hypothesis; establishes Tier-1/2 control edges (`USES`, `EVALUATES`,
  `DERIVED_FROM`).
- **Paper B** ("Latency-First Detection in Production") — supports the
  hypothesis; `REFERENCES` Paper A.
- **Paper C** ("RT-DETR: Transformers Beat YOLO on Accuracy") — **genuinely
  contradicts** the hypothesis: reports RT-DETR beating YOLO11 by 2.1 mAP at
  comparable latency. This is the demo-critical test case.

The corpus was deliberately engineered so the correct answer is known in
advance: exactly one paper (C) should produce a `CONTRADICTS` edge, and the
correct evidence chain is fully specified in `ONTOLOGY.md` §9. This gives
the spike a ground truth to grade against, rather than eyeballing plausible
output.

### 4.2 Pipeline

`prototype/memory_core_spike/main.py` runs a fixed, repeatable pipeline
(`reset → remember → dump_graph → find_contradiction_evidence →
recall_answer → build_report`). The design rule enforced throughout: **every
structural claim in the validation report is computed by deterministic graph
traversal over the raw graph data, never by asking an LLM to self-report.**
The LLM is used for exactly one step — producing the final natural-language
answer to the demo query. This matters for credibility: a report that says
"2 CONTRADICTS edges were found" is backed by literally filtering the edge
list for `rel_norm == "CONTRADICTS"`, not by trusting a model's claim that it
found some.

### 4.3 Provider configuration

LLM: **Anthropic** (Claude), via Cognee's dedicated `AnthropicAdapter`.
Embeddings: **`fastembed`** (`BAAI/bge-small-en-v1.5`), fully local, free,
no API key. This was chosen after directly verifying (via package
introspection, not documentation) which providers Cognee 1.2.2 has
first-class support for, and after confirming that Cognee Cloud — while
available — reroutes the entire pipeline server-side and drops the ontology
resolver used by this spike, making it unsuitable for a white-box validation
run. Full investigation and the production dual-mode plan (local execution
now, Cognee Cloud as an optional later mode behind one config flag):
`ARCHITECTURE.md` §9.1.

---

## 5. Success criteria and results

All 10 criteria were defined **before** the validated run, directly from the
ontology's confidence tiers and the spike's stated purpose (§1 above).

| # | Success criterion | Result | Evidence |
|---|---|---|---|
| 1 | Cognee installs and runs correctly | ✅ PASS | cognee 1.2.2 imported and executed end-to-end |
| 2 | Ontology is accepted | ✅ PASS | `RDFLibOntologyResolver` loaded `research_ontology.owl` without error |
| 3 | Sources are ingested | ✅ PASS | 58 nodes created from 4 source documents |
| 4 | Graph is created | ✅ PASS | 58 nodes / 180 edges |
| 5 | Entity extraction works | ✅ PASS | Entity types present: `TextSummary`(4), `NodeSet`(4), `DocumentChunk`(4), `TextDocument`(4), `Entity`(32), `EntityType`(10) |
| 6 | Tier-1 relationships exist | ✅ PASS | Present: `USES`, `REFERENCES`, `WRITTEN_BY`, `ABOUT` |
| 7 | **≥1 correct `CONTRADICTS` edge** | ✅ PASS | 2 `CONTRADICTS` edges extracted (see §6); 5 `SUPPORTS` edges |
| 8 | Graph traversal works | ✅ PASS | Deterministic traversal found 2 evidence chains |
| 9 | Natural-language recall works | ✅ PASS | `GRAPH_COMPLETION` produced a 797-character, correctly grounded answer |
| 10 | Evidence subgraph is produced | ✅ PASS | 3-node / 2-edge subgraph isolating the contradiction |

**Overall: PASS — 10/10.**

Raw relationship counts extracted from the corpus (normalized to the closed
vocabulary):

| Relationship | Count |
|---|---|
| `WRITTEN_BY` | 11 |
| `USES` | 11 |
| `EVALUATES` | 3 |
| `SUPPORTS` | 5 |
| `CONTRADICTS` | 2 |
| `DERIVED_FROM` | 2 |
| `REFERENCES` | 3 |
| `ABOUT` | 7 |

(A further set of structural/off-vocabulary edges — `BELONGS_TO_SET`,
`CONTAINS`, `IS_A`, `IS_PART_OF`, `MADE_FROM` — were also produced by
Cognee's underlying chunking/entity-typing machinery; these are expected
scaffolding edges outside the ontology's reasoning vocabulary and are not
part of the success criteria.)

### 6. The contradiction result

Both extracted `CONTRADICTS` edges correctly identify Paper C as
contradicting the stated hypothesis, matching the ground truth defined in
`ONTOLOGY.md` §9 exactly:

- *"RT-DETR: Transformers Beat YOLO on Accuracy"* **CONTRADICTS**
  *"YOLO11 is the best object detector for our real-time use case."*
- *"RT-DETR exceeds YOLO11 by 2.1 mAP points"* **CONTRADICTS** the same
  hypothesis.

The natural-language recall answer, generated independently via
`SearchType.GRAPH_COMPLETION` against the graph:

> "Based on the knowledge graph, **one paper contradicts the current
> hypothesis**: **RT-DETR: Transformers Beat YOLO on Accuracy** (Zhao and
> Lv, 2025). Why it contradicts: The current hypothesis states that 'YOLO11
> is the best object detector for our real-time use case' — RT-DETR
> contradicts this by demonstrating that it exceeds YOLO11 in accuracy by
> 2.1 mAP points on the COCO dataset at comparable latency..."

This is the correct answer, correctly attributed, with the correct
supporting number — produced from a graph built by unattended extraction,
not hand-authored.

---

## 7. Implementation notes

- **No two-pass fallback was needed.** `ONTOLOGY.md` §6.2 pre-specified a
  fallback (explicit `DataPoint` + `add_data_points(custom_edges=...)`
  classification pass) in case single-pass extraction of `SUPPORTS`/
  `CONTRADICTS` proved unreliable. It did not — the ontology resolver plus a
  `custom_prompt` naming the active hypothesis and instructing explicit
  stance classification was sufficient on the validated run.
- **Provider selection was a pure configuration decision.** Cognee 1.2.2
  reads `LLM_PROVIDER`/`EMBEDDING_PROVIDER` and related settings entirely
  from environment variables; no code in `main.py` branches on provider.
  Switching from OpenAI to Anthropic, or swapping embedding providers,
  requires editing `.env` only.
- **All structural findings in this report are reproducible from committed
  artifacts**: `prototype/memory_core_spike/outputs/graph.json` (full raw
  graph), `evidence.json` (the isolated contradiction subgraph), and
  `validation_report.md` (the auto-generated report this document
  summarizes) are checked into the repository as of this milestone.
- Three implementation bugs were found and fixed during this milestone (a
  missing SDK dependency, an incorrect import path for the ontology
  resolver caused by a Cognee package-naming collision, and a Windows
  console encoding issue on the final report print). None affected the
  correctness of the extracted graph — all three were fixed before the
  validated run whose results are reported above. Full detail:
  `Docs/PROGRESS.md`.

---

## 8. Remaining limitations

This milestone validates the *mechanism*, not the *product surface*. Known
gaps, to be addressed starting Milestone 2:

- **Small corpus.** 4 documents, one hypothesis, one designed contradiction.
  This proves the mechanism works; it does not yet prove it scales
  gracefully to a larger, messier corpus with multiple concurrent
  hypotheses, ambiguous evidence, or partial contradictions.
- **No `improve()` or `forget()` validation.** This spike exercises
  ingest + extract + recall only. Memory revision (`improve()`) and deletion
  (`forget()`) — both named as core Cognee lifecycle operations MemoryOS
  should demonstrate — are untested. `ONTOLOGY.md` §7 defines the *intended*
  deletion semantics at the schema level but flags that Cognee 1.2's actual
  deletion API is dataset-/prune-scoped, not a clean per-node delete; the
  mechanism to reconcile the two is open for Milestone 2.
- **No entity deduplication stress-test.** The ontology defines dedup keys
  per entity type (`ONTOLOGY.md` §3.1, §4), but this run's corpus doesn't
  exercise cross-document aliasing (e.g., "YOLO11" vs. "YOLOv11" mentioned
  differently across sources).
- **Single validated run.** The pipeline was run to a passing result once
  after fixing the three implementation bugs; it was not run repeatedly to
  measure extraction consistency across runs (LLM extraction is not
  guaranteed deterministic between calls).
- **This is a throwaway prototype**, by design (see `main.py`'s own
  docstring) — it is not wired into any application code, has no test
  suite of its own, and is not meant to be extended in place. Milestone 2's
  job is to promote the *validated pattern* (ontology + `custom_prompt` +
  deterministic traversal) into a proper `memory_core` module with real
  interfaces, not to keep building on this script.

---

## 9. Conclusion

Cognee 1.2.2, configured with an explicit closed ontology and a
hypothesis-aware `custom_prompt`, reliably builds a typed research knowledge
graph from a small corpus and correctly extracts the highest-risk,
judgment-requiring relationship type (`CONTRADICTS`) that the MemoryOS
product thesis depends on. All 10 pre-defined success criteria passed on the
validated run, with every structural claim traceable to a deterministic
graph query over committed evidence artifacts.

**Recommendation: proceed to Milestone 2** — promote this validated pattern
into the product's `memory_core` module.
