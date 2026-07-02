"""The research ontology's vocabulary, as data.

Design reference: Docs/MEMORY_CORE_DESIGN.md §3 ("ontology/"). Source of
truth: Docs/ONTOLOGY.md — kept in sync with that document by review
discipline, same as research_ontology.owl already is.

Deliberately data, not logic (design §3): a future ontology change (new
entity type, new relationship) touches this one module, not ingestion and
retrieval code scattered across the package.
"""

from __future__ import annotations

from memory_core.models import EntityType, RelationshipType

# ---------------------------------------------------------------------------
# Domain -> range constraints. Mirrors Docs/ONTOLOGY.md §6.1.
# An extracted edge whose endpoints violate this matrix is a schema error.
# ---------------------------------------------------------------------------
DOMAIN_RANGE: dict[RelationshipType, tuple[frozenset[EntityType], frozenset[EntityType]]] = {
    RelationshipType.WRITTEN_BY: (
        frozenset({EntityType.PAPER}),
        frozenset({EntityType.AUTHOR}),
    ),
    RelationshipType.USES: (
        frozenset({EntityType.PAPER, EntityType.EXPERIMENT}),
        frozenset({EntityType.METHOD, EntityType.DATASET}),
    ),
    RelationshipType.EVALUATES: (
        frozenset({EntityType.PAPER, EntityType.EXPERIMENT}),
        frozenset({EntityType.BENCHMARK}),
    ),
    RelationshipType.SUPPORTS: (
        frozenset({EntityType.PAPER, EntityType.FINDING, EntityType.EXPERIMENT}),
        frozenset({EntityType.HYPOTHESIS}),
    ),
    RelationshipType.CONTRADICTS: (
        frozenset({EntityType.PAPER, EntityType.FINDING, EntityType.EXPERIMENT}),
        frozenset({EntityType.HYPOTHESIS}),
    ),
    RelationshipType.DERIVED_FROM: (
        frozenset({EntityType.METHOD, EntityType.FINDING}),
        frozenset({EntityType.METHOD, EntityType.PAPER}),
    ),
    RelationshipType.REFERENCES: (
        frozenset({EntityType.PAPER}),
        frozenset({EntityType.PAPER}),
    ),
    RelationshipType.ABOUT: (
        frozenset({EntityType.PAPER, EntityType.RESEARCH_NOTE, EntityType.EXPERIMENT}),
        frozenset({EntityType.TOPIC}),
    ),
}

# ---------------------------------------------------------------------------
# Extraction confidence tiers. Mirrors Docs/ONTOLOGY.md §6.2 — drives which
# relationships are treated as controls (Tier 1) vs. the demo-critical,
# judgment-requiring edges (Tier 3).
# ---------------------------------------------------------------------------
TIER_1: frozenset[RelationshipType] = frozenset(
    {
        RelationshipType.WRITTEN_BY,
        RelationshipType.ABOUT,
        RelationshipType.REFERENCES,
        RelationshipType.USES,
    }
)
TIER_2: frozenset[RelationshipType] = frozenset(
    {RelationshipType.EVALUATES, RelationshipType.DERIVED_FROM}
)
TIER_3: frozenset[RelationshipType] = frozenset(
    {RelationshipType.SUPPORTS, RelationshipType.CONTRADICTS}
)


def is_valid_edge(
    relationship: RelationshipType, domain_type: EntityType, range_type: EntityType
) -> bool:
    """Check a (relationship, source_type, target_type) triple against the constraint matrix.

    Pure function, no I/O — a Tier 1 unit test target per design §7.
    """
    domain_types, range_types = DOMAIN_RANGE[relationship]
    return domain_type in domain_types and range_type in range_types
