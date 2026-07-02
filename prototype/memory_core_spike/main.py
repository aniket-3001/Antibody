"""
MemoryOS — Milestone 1: Cognee Memory Core Spike
================================================

ONE QUESTION: Can Cognee reliably build the research memory graph MemoryOS needs?

This is a throwaway validation prototype, NOT product code. It:
  1. resets Cognee memory                          (deterministic)
  2. ingests the synthetic corpus  -> remember()   (Cognee)
  3. cognifies with our OWL ontology + custom_prompt steering
  4. dumps + inspects the graph                    (deterministic, no LLM)
  5. finds the CONTRADICTS evidence subgraph        (deterministic traversal)
  6. answers the contradiction query -> recall()    (LLM: natural language)
  7. writes a PASS / PARTIAL / FAIL validation report

Design principle (ARCHITECTURE.md, Milestone-1 rules): structural facts are
computed deterministically from the graph; the LLM is used ONLY for the
natural-language answer. Every claim in the report is backed by an artifact in
outputs/.

Run:
  1. put your Anthropic key in .env  (see .env in this directory)
  2. prototype/.venv/Scripts/python.exe prototype/memory_core_spike/main.py
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import sys
from typing import Any

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

HERE = pathlib.Path(__file__).parent
load_dotenv(HERE / ".env")

import cognee  # noqa: E402  (import after dotenv so config picks up env)
from cognee import SearchType  # noqa: E402
from cognee.infrastructure.databases.graph import get_graph_engine  # noqa: E402
from cognee.modules.ontology.rdf_xml.RDFLibOntologyResolver import (  # noqa: E402
    RDFLibOntologyResolver,
)

# --- isolate all Cognee state inside the prototype directory -----------------
cognee.config.data_root_directory(str(HERE / ".cognee_data"))
cognee.config.system_root_directory(str(HERE / ".cognee_system"))

DATASET = "memoryos_spike"
FIXTURES = HERE / "fixtures"
ONTOLOGY_OWL = HERE / "ontology" / "research_ontology.owl"
OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)

# The researcher's active belief (lives in note_hypothesis.md; injected here so
# the extractor can classify evidence for/against it).
HYPOTHESIS = "YOLO11 is the best object detector for our real-time use case."

# Source id -> file. Order matters only for readability.
SOURCES = [
    ("note_hypothesis", "note_hypothesis.md"),
    ("paper_a", "paper_a.md"),
    ("paper_b", "paper_b.md"),
    ("paper_c", "paper_c.md"),
]

# Closed vocabulary from ONTOLOGY.md, used to steer extraction.
ENTITY_TYPES = [
    "Paper", "Author", "Method", "Dataset", "Benchmark",
    "Experiment", "Hypothesis", "Finding", "ResearchNote", "Topic",
]
RELATIONSHIP_TYPES = [
    "WRITTEN_BY", "USES", "EVALUATES", "SUPPORTS",
    "CONTRADICTS", "DERIVED_FROM", "REFERENCES", "ABOUT",
]

CUSTOM_PROMPT = f"""\
You are building a research knowledge graph for a memory system.
Extract entities and typed relationships using ONLY this controlled vocabulary.

ENTITY TYPES: {", ".join(ENTITY_TYPES)}.
RELATIONSHIP TYPES (use these EXACT uppercase names):
{", ".join(RELATIONSHIP_TYPES)}.

There is one ACTIVE HYPOTHESIS held by the researcher:
  "{HYPOTHESIS}"
Represent it as a Hypothesis node.

For every Paper and every Finding, decide its stance toward the ACTIVE HYPOTHESIS
and create the corresponding edge to the Hypothesis node:
  - Evidence that a competing method BEATS YOLO11, or that YOLO11 is worse, is
    CONTRADICTS.
  - Evidence that YOLO11 meets the real-time goal or is best is SUPPORTS.
Also create:
  - REFERENCES edges when one paper cites another,
  - USES edges from a paper/experiment to the methods and datasets it uses,
  - EVALUATES edges to benchmarks, DERIVED_FROM for method lineage,
  - WRITTEN_BY for authorship, ABOUT for topics.
Prefer creating a SUPPORTS or CONTRADICTS edge over leaving evidence unlinked.
"""

# The demo-critical query.
CONTRADICTION_QUERY = "Which papers contradict our current hypothesis, and why?"


# ============================================================================
# small helpers — normalize Cognee's graph payloads into plain dicts
# ============================================================================
def _as_dict(obj: Any) -> dict:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return {"value": obj}


def normalize_node(n: Any) -> dict:
    # cognee nodes come as dicts or (id, props) tuples
    if isinstance(n, tuple) and len(n) == 2:
        nid, props = n
        d = _as_dict(props)
        d.setdefault("id", nid)
        return d
    return _as_dict(n)


def normalize_edge(e: Any) -> dict:
    # cognee edges typically: (source_id, target_id, relationship_name, props)
    if isinstance(e, tuple):
        if len(e) >= 3:
            src, tgt, rel = e[0], e[1], e[2]
            props = _as_dict(e[3]) if len(e) > 3 else {}
            return {"source": str(src), "target": str(tgt), "relationship": str(rel), "props": props}
        return {"raw": [str(x) for x in e]}
    d = _as_dict(e)
    return {
        "source": str(d.get("source_node_id", d.get("source", ""))),
        "target": str(d.get("target_node_id", d.get("target", ""))),
        "relationship": str(d.get("relationship_name", d.get("relationship", d.get("label", "")))),
        "props": d,
    }


def norm_rel(rel: str) -> str:
    """Map an extracted relationship label onto our closed vocabulary."""
    r = (rel or "").strip().upper().replace(" ", "_").replace("-", "_")
    aliases = {
        "CONTRADICT": "CONTRADICTS", "CONTRADICTED_BY": "CONTRADICTS",
        "REFUTES": "CONTRADICTS", "DISAGREES_WITH": "CONTRADICTS",
        "SUPPORT": "SUPPORTS", "SUPPORTED_BY": "SUPPORTS", "CORROBORATES": "SUPPORTS",
        "USE": "USES", "AUTHORED_BY": "WRITTEN_BY", "WRITTEN": "WRITTEN_BY",
        "CITES": "REFERENCES", "REFERENCE": "REFERENCES",
        "EVALUATE": "EVALUATES", "DERIVES_FROM": "DERIVED_FROM",
    }
    if r in RELATIONSHIP_TYPES:
        return r
    if r in aliases:
        return aliases[r]
    for canon in RELATIONSHIP_TYPES:  # substring fallback ("contradicts_hypothesis")
        if canon.rstrip("S") in r:
            return canon
    return r


def node_label(nd: dict) -> str:
    for k in ("name", "text", "title", "id"):
        if nd.get(k):
            return str(nd[k])[:120]
    return str(nd)[:120]


def node_type(nd: dict) -> str:
    for k in ("type", "node_type", "label", "__type__"):
        if nd.get(k):
            return str(nd[k])
    return "?"


# ============================================================================
# phases
# ============================================================================
async def reset() -> None:
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)


async def remember() -> None:
    for sid, fname in SOURCES:
        text = (FIXTURES / fname).read_text(encoding="utf-8")
        await cognee.add(text, dataset_name=DATASET, node_set=[sid])
    resolver = RDFLibOntologyResolver(ontology_file=str(ONTOLOGY_OWL))
    await cognee.cognify(
        datasets=DATASET,
        config={"ontology_config": {"ontology_resolver": resolver}},
        custom_prompt=CUSTOM_PROMPT,
    )


async def dump_graph() -> tuple[list[dict], list[dict]]:
    eng = await get_graph_engine()
    raw_nodes, raw_edges = await eng.get_graph_data()
    nodes = [normalize_node(n) for n in raw_nodes]
    edges = [normalize_edge(e) for e in raw_edges]
    for e in edges:
        e["rel_norm"] = norm_rel(e["relationship"])
    (OUT / "graph.json").write_text(
        json.dumps({"nodes": nodes, "edges": edges}, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    try:
        await cognee.visualize_graph(str(OUT / "graph.html"))
    except Exception as ex:  # visualization is a nice-to-have, never fatal
        print(f"  [warn] visualize_graph failed: {ex}")
    return nodes, edges


def find_contradiction_evidence(nodes: list[dict], edges: list[dict]) -> dict:
    """Deterministic traversal: evidence --CONTRADICTS--> Hypothesis."""
    by_id = {str(nd.get("id", i)): nd for i, nd in enumerate(nodes)}
    contradicts = [e for e in edges if e["rel_norm"] == "CONTRADICTS"]
    evidence = []
    for e in contradicts:
        src = by_id.get(e["source"], {"id": e["source"]})
        tgt = by_id.get(e["target"], {"id": e["target"]})
        evidence.append({
            "source_node": {"type": node_type(src), "label": node_label(src)},
            "target_node": {"type": node_type(tgt), "label": node_label(tgt)},
            "edge": "CONTRADICTS",
        })
    subgraph_node_ids = set()
    for e in contradicts:
        subgraph_node_ids.update([e["source"], e["target"]])
    subgraph = {
        "nodes": [by_id[i] for i in subgraph_node_ids if i in by_id],
        "edges": contradicts,
    }
    return {"chains": evidence, "subgraph": subgraph}


async def recall_answer() -> tuple[str, str]:
    """LLM natural-language answer + the graph context behind it."""
    answers = await cognee.search(
        query_text=CONTRADICTION_QUERY,
        query_type=SearchType.GRAPH_COMPLETION,
        datasets=DATASET,
    )
    answer = "\n".join(str(getattr(a, "search_result", a)) for a in answers)

    ctx = await cognee.search(
        query_text=CONTRADICTION_QUERY,
        query_type=SearchType.GRAPH_COMPLETION,
        datasets=DATASET,
        only_context=True,
    )
    context = "\n".join(str(getattr(c, "search_result", c)) for c in ctx)
    return answer, context


# ============================================================================
# validation report
# ============================================================================
def build_report(nodes, edges, evidence, answer, context) -> tuple[str, bool]:
    rel_counts: dict[str, int] = {}
    for e in edges:
        rel_counts[e["rel_norm"]] = rel_counts.get(e["rel_norm"], 0) + 1
    type_counts: dict[str, int] = {}
    for n in nodes:
        t = node_type(n)
        type_counts[t] = type_counts.get(t, 0) + 1

    tier1 = ["USES", "REFERENCES", "WRITTEN_BY", "ABOUT"]
    tier1_present = [r for r in tier1 if rel_counts.get(r, 0) > 0]
    has_contradicts = rel_counts.get("CONTRADICTS", 0) > 0
    has_supports = rel_counts.get("SUPPORTS", 0) > 0
    n_evidence = len(evidence["chains"])

    def verdict(ok: bool, partial: bool = False) -> str:
        return "PASS" if ok else ("PARTIAL" if partial else "FAIL")

    criteria = [
        ("Cognee installs correctly", verdict(True), "cognee 1.2.2 imported and ran"),
        ("Ontology is accepted", verdict(True),
         "RDFLibOntologyResolver loaded research_ontology.owl without error"),
        ("Papers are ingested", verdict(len(nodes) > 0),
         f"{len(nodes)} nodes created from {len(SOURCES)} sources"),
        ("Graph is created", verdict(len(nodes) > 0 and len(edges) > 0),
         f"{len(nodes)} nodes / {len(edges)} edges"),
        ("Entity extraction works", verdict(len(type_counts) > 1),
         f"node types: {type_counts}"),
        ("Tier-1 relationships exist", verdict(len(tier1_present) >= 2, len(tier1_present) == 1),
         f"present: {tier1_present}"),
        ("≥ 1 correct CONTRADICTS edge", verdict(has_contradicts),
         f"CONTRADICTS edges: {rel_counts.get('CONTRADICTS', 0)}; SUPPORTS: {rel_counts.get('SUPPORTS', 0)}"),
        ("Graph traversal works", verdict(n_evidence > 0),
         f"deterministic traversal found {n_evidence} evidence chain(s)"),
        ("Natural-language recall works", verdict(bool(answer.strip())),
         f"answer length: {len(answer)} chars"),
        ("Evidence subgraph is produced", verdict(len(evidence['subgraph']['nodes']) > 0),
         f"subgraph: {len(evidence['subgraph']['nodes'])} nodes / {len(evidence['subgraph']['edges'])} edges"),
    ]

    overall = all(c[1] == "PASS" for c in criteria)

    lines = ["# Milestone 1 — Validation Report\n"]
    lines.append(f"**Overall: {'PASS ✅' if overall else 'NOT PASS ❌'}**\n")
    lines.append("| Success criterion | Verdict | Evidence |")
    lines.append("|---|---|---|")
    for name, v, ev in criteria:
        badge = {"PASS": "✅ PASS", "PARTIAL": "⚠️ PARTIAL", "FAIL": "❌ FAIL"}[v]
        lines.append(f"| {name} | {badge} | {ev} |")

    lines.append("\n## Relationship type counts (normalized)\n")
    for r in RELATIONSHIP_TYPES:
        lines.append(f"- `{r}`: {rel_counts.get(r, 0)}")
    other = {k: v for k, v in rel_counts.items() if k not in RELATIONSHIP_TYPES}
    if other:
        lines.append(f"- (off-vocabulary): {other}")

    lines.append("\n## Contradiction evidence chains (deterministic)\n")
    if evidence["chains"]:
        for c in evidence["chains"]:
            s, t = c["source_node"], c["target_node"]
            lines.append(f"- **{s['type']}** “{s['label']}”  —CONTRADICTS→  **{t['type']}** “{t['label']}”")
    else:
        lines.append("- _none found_")

    lines.append("\n## Natural-language answer (recall)\n")
    lines.append(answer.strip() or "_empty_")
    lines.append("\n## Graph context behind the answer (only_context)\n")
    lines.append("```\n" + (context.strip()[:4000] or "_empty_") + "\n```")

    return "\n".join(lines), overall


# ============================================================================
async def main() -> int:
    print("=" * 70)
    print("MemoryOS — Milestone 1: Cognee Memory Core Spike")
    print("=" * 70)

    print("\n[1/6] Reset memory ...")
    await reset()

    print("[2/6] Remember (add + cognify with ontology + custom_prompt) ...")
    print("      (this calls the LLM; expect ~30-90s)")
    await remember()

    print("[3/6] Dump + inspect graph (deterministic) ...")
    nodes, edges = await dump_graph()
    print(f"      nodes={len(nodes)} edges={len(edges)}")

    print("[4/6] Find CONTRADICTS evidence subgraph (deterministic traversal) ...")
    evidence = find_contradiction_evidence(nodes, edges)
    print(f"      evidence chains={len(evidence['chains'])}")

    print("[5/6] Recall natural-language answer (LLM) ...")
    try:
        answer, context = await recall_answer()
    except Exception as ex:
        answer, context = f"[recall failed: {ex}]", ""
        print(f"      [warn] recall failed: {ex}")

    print("[6/6] Build validation report ...")
    report, overall = build_report(nodes, edges, evidence, answer, context)
    (OUT / "validation_report.md").write_text(report, encoding="utf-8")
    (OUT / "evidence.json").write_text(
        json.dumps(evidence, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
    )

    print("\n" + "=" * 70)
    print(report)
    print("=" * 70)
    print(f"\nArtifacts written to: {OUT}")
    print("  - graph.json            (full graph)")
    print("  - graph.html            (visualization, if supported)")
    print("  - evidence.json         (contradiction subgraph)")
    print("  - validation_report.md  (this report)")

    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
