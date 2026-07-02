"""custom_prompt template builder.

Design reference: Docs/MEMORY_CORE_DESIGN.md §2.1, §3 ("ontology/").

Generalizes the CUSTOM_PROMPT pattern validated in Milestone 1
(prototype/memory_core_spike/main.py) — which produced correct
CONTRADICTS extraction on its first successful run (Docs/MILESTONE_1_REPORT.md
§7) — from a single hardcoded hypothesis to zero or more caller-supplied
`active_hypotheses`.

Pure string templating: no I/O, a Tier 1 unit test target per design §7.
"""

from __future__ import annotations

from memory_core.ontology.vocabulary import TIER_3


def build_custom_prompt(
    entity_types: list[str],
    relationship_types: list[str],
    active_hypotheses: list[str] | None,
) -> str:
    """Build the extraction-steering prompt for cognee.cognify(custom_prompt=...).

    If `active_hypotheses` is empty/None, the Tier-3 stance-classification
    instructions are omitted — Tier 1/2 edges still extract normally (see
    design §2.1's documented limitation: this does not auto-discover
    hypotheses already in the graph).
    """
    lines = [
        "You are building a research knowledge graph for a memory system.",
        "Extract entities and typed relationships using ONLY this controlled vocabulary.",
        "",
        f"ENTITY TYPES: {', '.join(entity_types)}.",
        "RELATIONSHIP TYPES (use these EXACT uppercase names):",
        f"{', '.join(relationship_types)}.",
    ]

    if active_hypotheses:
        tier3_names = ", ".join(r.value if hasattr(r, "value") else str(r) for r in TIER_3)
        lines += [
            "",
            "There are ACTIVE HYPOTHESES held by the researcher:",
            *[f'  - "{h}"' for h in active_hypotheses],
            "Represent each as a Hypothesis node.",
            "",
            "For every Paper and every Finding, decide its stance toward each ACTIVE",
            f"HYPOTHESIS and create the corresponding edge ({tier3_names}):",
            "  - Evidence that weakens/refutes a hypothesis is CONTRADICTS.",
            "  - Evidence that strengthens/corroborates a hypothesis is SUPPORTS.",
            "Prefer creating a SUPPORTS or CONTRADICTS edge over leaving evidence unlinked.",
        ]

    lines += [
        "",
        "Also create:",
        "  - REFERENCES edges when one paper cites another,",
        "  - USES edges from a paper/experiment to the methods and datasets it uses,",
        "  - EVALUATES edges to benchmarks, DERIVED_FROM for method lineage,",
        "  - WRITTEN_BY for authorship, ABOUT for topics.",
    ]
    return "\n".join(lines)
