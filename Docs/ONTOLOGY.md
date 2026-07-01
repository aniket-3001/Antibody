# MemoryOS — Research Ontology

Version: 1.0
Status: Draft for review (blocks the Cognee memory-core spike)
Scope: This is the **source of truth** for the MemoryOS research knowledge graph.
Related: `ARCHITECTURE.md` (§2 summarizes; this document is authoritative).

---

## 1. Purpose

This document formally defines the schema of the MemoryOS knowledge graph: the
entity types (nodes), the relationship types (typed edges), the domain/range
constraints on those edges, and — most importantly — the **reasoning** behind
each modeling decision.

It is deliberately human-readable and technology-neutral. It does **not** contain
OWL, pydantic, or any Cognee-specific code. Those are downstream *projections* of
this document. If the graph and this document ever disagree, this document wins
and the projection is corrected.

### 1.1 Why the ontology is a first-class artifact

MemoryOS's entire differentiation is that it answers **relationship-aware**
questions a stateless model or vanilla RAG cannot — above all *"which evidence
contradicts our current direction?"*. That capability is only as good as the
edges in the graph. An unconstrained extraction produces "entity soup": many
nodes, vague edges, no semantics to reason over. A small, explicit, well-typed
ontology is what turns extraction into *reasoning substrate*. Therefore the
ontology is designed before, and constrains, the extraction — not the reverse.

---

## 2. Design principles for the ontology

1. **Small and closed beats large and open.** A closed set of 10 entity types
   and 8 relationship types is easier to extract reliably, easier to visualize,
   and easier to reason over than an open vocabulary. We would rather have fewer,
   trustworthy edge types than many unreliable ones.
2. **Every edge is typed and directional.** No generic "related_to". Direction
   carries meaning (evidence → hypothesis, not hypothesis → evidence).
3. **Domain/range are constrained.** Each relationship declares which entity
   types it may connect. Constraints make traversal queries writable and make
   extraction errors detectable.
4. **Separate what is *anchored* from what is *extracted*.** Some nodes map 1:1
   to an ingested artifact (a paper, a note); these are the unit of deletion.
   Others are concepts mentioned by many artifacts (a method, a hypothesis).
   This distinction governs identity, deduplication, and `forget()`.
5. **Model for the demo-critical questions first.** The schema is shaped so the
   three highest-value queries — *contradiction*, *justification ("why")*, and
   *gap analysis* — map to clean, short graph traversals.
6. **Prefer reification through `Finding` over overloaded edges.** Rather than
   attaching quantitative claims to edges, we promote claims to first-class
   `Finding` nodes. This keeps edges simple and makes evidence inspectable.

---

## 3. Conventions

### 3.1 Node identity & deduplication

| Aspect | Rule |
|---|---|
| Entity naming | Entity types are `PascalCase` (e.g., `ResearchNote`). |
| Relationship naming | Relationship types are `UPPER_SNAKE_CASE` (e.g., `WRITTEN_BY`). |
| Identity key | Each entity declares a **dedup key** — the attribute(s) used to decide whether two mentions are the same node. |
| Normalization | Names are matched case-insensitively and alias-aware (e.g., "YOLO11" ≡ "YOLOv11"). Aliases are stored on the node. |

### 3.2 Source-anchored vs. extracted entities

- **Source-anchored** (`Paper`, `Experiment`, `ResearchNote`): each instance
  corresponds to exactly one ingested artifact. It is the unit of `forget()` and
  carries a `source_uri`/document id and a `node_set` tag.
- **Extracted** (`Author`, `Method`, `Dataset`, `Benchmark`, `Hypothesis`,
  `Finding`, `Topic`): mentioned *by* sources and shared *across* them. Deleting
  one source must not delete an extracted node still referenced by another
  source. (See §7 on deletion semantics.)

---

## 4. Entity types (nodes)

For each: definition, attributes, dedup key, anchored?, example, and rationale.

---

### 4.1 `Paper`  *(source-anchored)*

- **Definition:** A research paper, article, or preprint ingested as a source.
- **Attributes:** `title`, `authors[]`, `year`, `source_uri`, `abstract`,
  `node_set`.
- **Dedup key:** `title` (normalized) + `year`.
- **Example:** *"YOLO11: An Improved Real-Time Object Detector" (2024)*.
- **Rationale:** The primary evidence-bearing unit of a research corpus. Anchored
  because a user ingests and later removes *a paper*, not an abstract concept.

---

### 4.2 `Author`  *(extracted)*

- **Definition:** A person credited on a paper.
- **Attributes:** `name`, `aliases[]`.
- **Dedup key:** normalized `name`.
- **Example:** *"Jocher, G."*
- **Rationale:** Enables provenance and "who works on what" navigation. Kept
  minimal — affiliation/ORCID are out of scope for the MVP (they add extraction
  cost without serving the demo-critical queries).

---

### 4.3 `Method`  *(extracted)*

- **Definition:** A technique, model, architecture, or algorithm.
- **Attributes:** `name`, `aliases[]`, `category` (optional; e.g., "detector").
- **Dedup key:** normalized `name` (+ alias set).
- **Example:** *"YOLO11"*, *"contrastive learning"*.
- **Rationale:** The connective tissue of a research graph — methods are what
  papers and experiments *share*, so a `Method` node is the join point that makes
  cross-document memory (and `improve()` re-linking) visible.

---

### 4.4 `Dataset`  *(extracted)*

- **Definition:** A named dataset used for training or evaluation.
- **Attributes:** `name`, `aliases[]`.
- **Dedup key:** normalized `name`.
- **Example:** *"COCO"*, *"ImageNet"*.
- **Rationale:** Required for the gap-analysis query ("which datasets were never
  evaluated?"), which is a distinctive graph-only capability.

---

### 4.5 `Benchmark`  *(extracted)*

- **Definition:** A metric-on-task under which methods are compared.
- **Attributes:** `name`, `task` (optional).
- **Dedup key:** normalized `name` (+ `task`).
- **Example:** *"mAP@0.5"* on *"object detection"*.
- **Rationale:** Separating *benchmark* from *dataset* and *method* is what lets
  us represent "Method M scored X on Benchmark B" precisely, via `EVALUATES` +
  `Finding`, instead of collapsing everything into one fuzzy edge.

---

### 4.6 `Experiment`  *(source-anchored)*

- **Definition:** A researcher-run trial captured in notes or logs.
- **Attributes:** `title`, `date`, `config`, `source_uri`, `node_set`.
- **Dedup key:** `title` + `date`.
- **Example:** *"Fine-tune YOLO11 on internal dataset, 2026-06-14"*.
- **Rationale:** Experiments are *first-party evidence* and are what make
  MemoryOS about a researcher's own accumulating work, not just literature.
  Anchored, because a user adds/removes an experiment as a unit.

---

### 4.7 `Hypothesis`  *(extracted)*

- **Definition:** A claim the researcher currently believes or is testing.
- **Attributes:** `statement`, `status` ∈ {`active`, `retired`}.
- **Dedup key:** normalized `statement` (semantic; may require human curation).
- **Example:** *"YOLO11 is the best detector for our real-time use case."*
- **Rationale:** The **pivot of the entire graph.** `SUPPORTS`/`CONTRADICTS`
  edges terminate here. A hypothesis with `status=active` is the anchor for the
  contradiction and justification queries. Modeling it explicitly (rather than as
  free text) is what makes "why do we believe X?" a graph traversal.

---

### 4.8 `Finding`  *(extracted)*

- **Definition:** A concrete result or conclusion asserted by a paper or
  experiment (often quantitative).
- **Attributes:** `statement`, `quantitative_value` (optional), `polarity`
  (optional; positive/negative w.r.t. a hypothesis).
- **Dedup key:** `statement` (normalized) + originating source.
- **Example:** *"On COCO, RT-DETR exceeds YOLO11 mAP by 2.1 points."*
- **Rationale:** Reification of a claim. Instead of overloading an edge with
  quantitative detail, we make the claim a node. This lets a single `Finding`
  simultaneously (a) belong to its source, and (b) `SUPPORTS`/`CONTRADICTS` a
  hypothesis — giving us *inspectable evidence* the UI can surface verbatim.

---

### 4.9 `ResearchNote`  *(source-anchored)*

- **Definition:** A freeform markdown note authored by the researcher.
- **Attributes:** `title`, `body`, `source_uri`, `node_set`.
- **Dedup key:** `title` + content hash.
- **Example:** *"Why we picked YOLO11 over RT-DETR — latency budget."*
- **Rationale:** Captures human reasoning and decisions that never appear in
  papers — a key reason persistent memory beats re-reading PDFs. Anchored.

---

### 4.10 `Topic`  *(extracted)*

- **Definition:** A thematic cluster for navigation and grouping.
- **Attributes:** `name`.
- **Dedup key:** normalized `name`.
- **Example:** *"real-time object detection"*.
- **Rationale:** Lightweight organization so the graph is navigable at a glance.
  Intentionally thin — `Topic` is for grouping, not reasoning; the reasoning
  edges are `SUPPORTS`/`CONTRADICTS`/`EVALUATES`.

---

## 5. Relationship types (typed edges)

Closed set of 8. For each: domain→range, cardinality, meaning, example,
rationale, and an **extraction-difficulty** note (how confidently we expect an
LLM to infer it), because that difficulty directly informs the spike's
success criteria and fallback plan.

---

### 5.1 `WRITTEN_BY`

- **Domain → Range:** `Paper` → `Author`
- **Cardinality:** many-to-many
- **Meaning:** Authorship/credit.
- **Example:** `Paper("YOLO11…") —WRITTEN_BY→ Author("Jocher, G.")`
- **Rationale:** Provenance; enables author-centric navigation.
- **Extraction difficulty:** **Low.** Authorship is explicit in metadata.

---

### 5.2 `USES`

- **Domain → Range:** `Paper | Experiment` → `Method | Dataset`
- **Cardinality:** many-to-many
- **Meaning:** The source employs a method or dataset.
- **Example:** `Experiment("Fine-tune…") —USES→ Method("YOLO11")`
- **Rationale:** Establishes the `Method`/`Dataset` join points that connect the
  corpus; foundational for both `improve()` re-linking and gap analysis.
- **Extraction difficulty:** **Low–medium.** Usually stated plainly.

---

### 5.3 `EVALUATES`

- **Domain → Range:** `Paper | Experiment` → `Benchmark`
  *(the evaluated `Method` and the resulting `Finding` are attached separately —
  see note)*
- **Cardinality:** many-to-many
- **Meaning:** The source measures performance under a benchmark.
- **Note on modeling:** A full evaluation is the triple *(method, benchmark,
  result)*. We represent it as: source `—USES→` Method, source `—EVALUATES→`
  Benchmark, and a `Finding` node carrying the quantitative result that
  `SUPPORTS`/`CONTRADICTS` the relevant `Hypothesis`. We deliberately do **not**
  create an n-ary "Evaluation" node in the MVP (see §8, rejected alternatives).
- **Example:** `Paper("RT-DETR…") —EVALUATES→ Benchmark("mAP@0.5")`
- **Rationale:** Enables gap analysis (benchmarks/datasets with no incoming
  evaluation) and grounds quantitative comparison.
- **Extraction difficulty:** **Medium.** Requires linking a metric to a source.

---

### 5.4 `SUPPORTS`  ⭐

- **Domain → Range:** `Paper | Finding | Experiment` → `Hypothesis`
- **Cardinality:** many-to-one (many evidences → one hypothesis)
- **Meaning:** The evidence strengthens/corroborates the hypothesis.
- **Example:** `Finding("YOLO11 hits 54.7 mAP at 2ms") —SUPPORTS→ Hypothesis("YOLO11 is best for our real-time use case")`
- **Rationale:** Half of the demo centerpiece. Powers "why do we believe X?" as a
  one-hop reverse traversal from an active hypothesis.
- **Extraction difficulty:** **High.** Requires the extractor to judge that a
  claim *supports* a stated hypothesis. This is guided by `custom_prompt` and, if
  needed, the two-pass fallback (see §6.2 and ARCHITECTURE.md §2.4).

---

### 5.5 `CONTRADICTS`  ⭐⭐

- **Domain → Range:** `Paper | Finding | Experiment` → `Hypothesis`
- **Cardinality:** many-to-one
- **Meaning:** The evidence weakens/refutes the hypothesis.
- **Example:** `Finding("RT-DETR exceeds YOLO11 mAP by 2.1 pts on COCO") —CONTRADICTS→ Hypothesis("YOLO11 is best for our real-time use case")`
- **Rationale:** **The single most important edge in MemoryOS.** It encodes
  disagreement across the accumulated corpus — the capability a stateless model
  cannot reproduce. The primary demo query is a reverse traversal along this
  edge.
- **Extraction difficulty:** **High (highest risk in the project).** This is the
  edge the spike exists to validate. Success criterion: at least one correct
  `CONTRADICTS` edge is produced from the fixture corpus. If unreliable, the
  two-pass fallback classifies each (evidence, hypothesis) pair explicitly.

---

### 5.6 `DERIVED_FROM`

- **Domain → Range:** `Method | Finding` → `Method | Paper`
- **Cardinality:** many-to-one
- **Meaning:** Lineage — a method or finding builds on a prior one.
- **Example:** `Method("YOLO11") —DERIVED_FROM→ Method("YOLOv8")`
- **Rationale:** Captures research genealogy, enabling "what does this build on?"
  and evolution narratives.
- **Extraction difficulty:** **Medium.** Often signposted ("based on", "extends").

---

### 5.7 `REFERENCES`

- **Domain → Range:** `Paper` → `Paper`
- **Cardinality:** many-to-many
- **Meaning:** One paper cites/mentions another.
- **Example:** `Paper("RT-DETR…") —REFERENCES→ Paper("YOLO11…")`
- **Rationale:** Citation structure; lets the graph connect papers directly and
  supports "what cites this?". Included in the spike's minimum edge set as a
  low-risk control (if `REFERENCES` fails to extract, extraction is broken in
  general, not just for hard edges).
- **Extraction difficulty:** **Low–medium**, when both papers are in the corpus.

---

### 5.8 `ABOUT`

- **Domain → Range:** `Paper | ResearchNote | Experiment` → `Topic`
- **Cardinality:** many-to-many
- **Meaning:** Thematic grouping.
- **Example:** `Paper("YOLO11…") —ABOUT→ Topic("real-time object detection")`
- **Rationale:** Navigation/clustering only; keeps the graph legible. Lowest
  reasoning value, so it is explicitly *not* part of the spike's success
  criteria.
- **Extraction difficulty:** **Low.**

---

## 6. Domain/range constraint matrix & extraction plan

### 6.1 Constraint matrix

| Relationship | Legal domain(s) | Legal range(s) |
|---|---|---|
| `WRITTEN_BY` | Paper | Author |
| `USES` | Paper, Experiment | Method, Dataset |
| `EVALUATES` | Paper, Experiment | Benchmark |
| `SUPPORTS` | Paper, Finding, Experiment | Hypothesis |
| `CONTRADICTS` | Paper, Finding, Experiment | Hypothesis |
| `DERIVED_FROM` | Method, Finding | Method, Paper |
| `REFERENCES` | Paper | Paper |
| `ABOUT` | Paper, ResearchNote, Experiment | Topic |

Any extracted edge whose endpoints violate this matrix is a **schema error** and
is dropped (and logged) during ingestion. This is how we keep the graph clean.

### 6.2 Extraction confidence tiers (drives spike success criteria)

- **Tier 1 (low risk):** `WRITTEN_BY`, `ABOUT`, `REFERENCES`, `USES`. Expected to
  extract from ontology + a plain prompt. Serve as controls.
- **Tier 2 (medium):** `EVALUATES`, `DERIVED_FROM`. Guided by `custom_prompt`.
- **Tier 3 (high risk):** `SUPPORTS`, `CONTRADICTS`. The crux. Strategy:
  1. Provide the active `Hypothesis` statement(s) explicitly in `custom_prompt`.
  2. Instruct the extractor to classify each evidential claim as supporting,
     contradicting, or neutral w.r.t. those hypotheses.
  3. If Tier-3 recall is unreliable, invoke the **two-pass fallback**: cognify
     for Tier-1/2 entities and findings, then a dedicated pass that asks the LLM
     to label each (Finding, Hypothesis) pair and writes the typed edge directly.

The spike's PASS bar: **Tier-1 edges present, and ≥1 correct `CONTRADICTS`
edge**. Anything less triggers the fallback and a written recommendation before
Milestone 2.

---

## 7. Deletion / `forget()` semantics at the schema level

Because extracted nodes are shared, deleting a source must preserve graph
consistency:

- Deleting a source-anchored node (`Paper`/`Experiment`/`ResearchNote`) removes
  that node and any **extracted node exclusively referenced by it** (orphans).
- Extracted nodes still referenced by another surviving source are **retained**.
- Edges incident only to removed nodes are removed; edges to surviving nodes are
  preserved.

> **Implementation caveat (from API verification):** Cognee 1.2 does not expose a
> clean per-node `delete()`; deletion is dataset-/prune-scoped (see
> ARCHITECTURE.md delta #3). The *schema-level* semantics above are the target;
> the *mechanism* to achieve them is an open question the spike/Milestone 2 must
> resolve. This section defines the desired behavior so the mechanism can be
> judged against it.

---

## 8. Rejected alternatives & non-goals (reasoning trail)

- **N-ary `Evaluation` node** (method × benchmark × result as one node): rejected
  for the MVP. It is more "correct" but adds a node type and extraction burden
  without improving any demo-critical query. We approximate with `USES` +
  `EVALUATES` + `Finding`. Revisit post-hackathon.
- **Open relationship vocabulary** (let the LLM invent edge labels): rejected.
  Produces entity soup; defeats traversal queries. Closed set is deliberate.
- **`Author` affiliation / ORCID, `Paper` venue/DOI:** out of scope. No
  demo-critical query needs them.
- **Confidence weights on `SUPPORTS`/`CONTRADICTS`:** postponed. Attractive for a
  "strength of evidence" view, but not required for the MVP demo. Noted as a
  natural extension (would live as an edge attribute).
- **Direction reversal of evidence edges** (Hypothesis → evidence): rejected.
  Evidence → Hypothesis reads naturally ("this finding contradicts that
  hypothesis") and makes the reverse-traversal query uniform.

---

## 9. Worked example — the spike fixture corpus

This concrete instance doubles as the specification for the three synthetic
"papers" the memory-core spike will ingest. It is intentionally engineered to
contain Tier-1 controls **and** a genuine contradiction.

**Active hypothesis (H1):**
> "YOLO11 is the best object detector for our real-time use case."

**Paper A — "YOLO11: Real-Time Detection at 2ms" (2024)**
- `USES` Method `YOLO11`; `USES` Dataset `COCO`; `EVALUATES` Benchmark `mAP@0.5`.
- Finding A1: *"YOLO11 reaches 54.7 mAP at 2ms latency."* → **`SUPPORTS` H1**.
- `Method YOLO11 —DERIVED_FROM→ Method YOLOv8`.

**Paper B — "Latency-First Detection in Production" (2025)**
- `USES` Method `YOLO11`. Finding B1: *"YOLO11's low latency met our real-time
  budget where transformer detectors did not."* → **`SUPPORTS` H1**.
- `REFERENCES` Paper A.

**Paper C — "RT-DETR: Transformers Beat YOLO on Accuracy" (2025)**
- `USES` Method `RT-DETR`; `USES` Dataset `COCO`; `EVALUATES` Benchmark `mAP@0.5`.
- Finding C1: *"On COCO, RT-DETR exceeds YOLO11 mAP by 2.1 points."* →
  **`CONTRADICTS` H1** (the demo-critical edge).
- `REFERENCES` Paper A.

**Expected demo query:** *"Which papers contradict our current hypothesis, and
why?"* → traversal `H1 ←CONTRADICTS← Finding C1 ←(source)← Paper C`, returning the
NL answer ("Paper C contradicts H1 because RT-DETR beats YOLO11 by 2.1 mAP on
COCO") **and** the evidence subgraph `{Paper C, Finding C1, H1}`.

This example is the acceptance test for Milestone 1.

---

## 10. Change log

| Version | Change |
|---|---|
| 1.0 | Initial formal ontology: 10 entities, 8 relationships, constraint matrix, extraction tiers, deletion semantics, rejected alternatives, worked fixture example. |
