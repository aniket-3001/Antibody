# Memory Core Spike (Milestone 1)

> **Superseded as of Milestone 2.2.** Everything this script does is now
> reproducible through the real `memory_core` public API — see
> `tests/reproduce_milestone_1.py`, which performs the same corpus/query
> using only `memory_core.ingest/find_evidence/recall/get_graph/reset_project`,
> and passes the same 10 structural criteria. This directory is retained for
> historical reference (it's the evidence behind `Docs/MILESTONE_1_REPORT.md`)
> but is no longer the way to exercise this functionality. Use `memory_core`.

Throwaway validation prototype. **Not product code.** It answers exactly one
question: *can Cognee reliably build the research memory graph MemoryOS needs?*

## What it does

1. Resets Cognee memory (deterministic).
2. Ingests 4 synthetic sources (`fixtures/`) — 1 research note stating the active
   hypothesis + 3 papers, one of which genuinely contradicts it.
3. `cognify()` with our OWL ontology (`ontology/research_ontology.owl`, a
   projection of `Docs/ONTOLOGY.md`) + a `custom_prompt` steering extraction to
   the closed relationship vocabulary.
4. Dumps the graph and inspects it **deterministically** (no LLM).
5. Traverses `evidence --CONTRADICTS--> Hypothesis` deterministically.
6. Answers *"Which papers contradict our current hypothesis, and why?"* via the
   LLM (`GRAPH_COMPLETION`) + captures the graph context (`only_context`).
7. Writes a PASS / PARTIAL / FAIL validation report.

Structural facts are computed from the graph; the LLM is used only for the
natural-language answer (Milestone-1 determinism rule).

## Run

```bash
# 1. paste your Anthropic key into .env (replace PASTE_ANTHROPIC_KEY_HERE)
# 2. from the repo root:
prototype/.venv/Scripts/python.exe prototype/memory_core_spike/main.py
```

**Provider config (lowest-cost, chosen deliberately):** LLM = Anthropic (Claude,
the project's designated LLM per `PRODUCT_PRD.md`) — the only paid dependency.
Embeddings = `fastembed` (`BAAI/bge-small-en-v1.5`, 384-dim) — runs fully
locally via ONNX, no API key, no per-call cost, just a one-time ~69MB model
download from Hugging Face on first run. Ollama/fully-local was considered and
rejected for this spike: not installed on this machine, and would add real
setup time (binary + multi-GB model pull) for a one-shot validation prototype.

Exit code `0` = all success criteria PASS, `1` = at least one did not.

## Outputs (`outputs/`)

| File | Contents |
|---|---|
| `validation_report.md` | PASS/PARTIAL/FAIL per success criterion + evidence |
| `graph.json` | full graph (nodes + normalized edges) |
| `graph.html` | Cognee graph visualization (if supported) |
| `evidence.json` | the contradiction evidence subgraph |

## Layout

```
memory_core_spike/
  main.py                       # the spike
  .env                          # Anthropic key + embedding config (git-ignored)
  _verify_api.py                # Step-2 API introspection probe
  fixtures/                     # 4 synthetic sources
  ontology/research_ontology.owl# OWL projection of Docs/ONTOLOGY.md
  outputs/                      # generated artifacts (git-ignored)
```
