"""Data models for memory_core.

Design reference: Docs/MEMORY_CORE_DESIGN.md §5.

Pure data, no logic and no Cognee imports — kept dependency-free so tests
can import this module without triggering Cognee's import-time setup (see
design §3's rationale for errors.py/models.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal


# ---------------------------------------------------------------------------
# §5.1 Graph primitives
# ---------------------------------------------------------------------------
class EntityType(str, Enum):
    """The 10 closed entity types. Mirrors Docs/ONTOLOGY.md §4."""

    PAPER = "Paper"
    AUTHOR = "Author"
    METHOD = "Method"
    DATASET = "Dataset"
    BENCHMARK = "Benchmark"
    EXPERIMENT = "Experiment"
    HYPOTHESIS = "Hypothesis"
    FINDING = "Finding"
    RESEARCH_NOTE = "ResearchNote"
    TOPIC = "Topic"


class RelationshipType(str, Enum):
    """The 8 closed relationship types. Mirrors Docs/ONTOLOGY.md §5."""

    WRITTEN_BY = "WRITTEN_BY"
    USES = "USES"
    EVALUATES = "EVALUATES"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    DERIVED_FROM = "DERIVED_FROM"
    REFERENCES = "REFERENCES"
    ABOUT = "ABOUT"


SourceType = Literal["paper", "experiment", "research_note", "text"]

RecallStrategy = Literal["relationship", "contradiction", "gap_analysis", "factual"]
"""Mirrors ARCHITECTURE.md §6's recall router intents. Owned by
retrieval/router.py (it decides the strategy); providers only consume the
name to know which Cognee search call to issue. Lives here, not in
providers/base.py, so the ownership direction (router defines, provider
consumes) is reflected in the import direction too."""


@dataclass
class MemoryNode:
    """A normalized graph node.

    `type` and the sibling MemoryEdge.relationship deliberately allow an
    off-vocabulary escape hatch (str / "unknown") rather than raising or
    dropping data — Milestone 1's real graph contained Cognee scaffolding
    nodes/edges outside the closed ontology (see design §5.1's rationale).
    """

    id: str
    type: EntityType | Literal["unknown"]
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)
    source_ids: list[str] = field(default_factory=list)


@dataclass
class MemoryEdge:
    source_id: str
    target_id: str
    relationship: RelationshipType | str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryGraph:
    nodes: list[MemoryNode] = field(default_factory=list)
    edges: list[MemoryEdge] = field(default_factory=list)


# ---------------------------------------------------------------------------
# §5.2 Source & domain models
# ---------------------------------------------------------------------------
@dataclass
class SourceInput:
    """ingest()/improve() argument — not extracted from the graph."""

    content: str | bytes
    source_type: SourceType
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceRecord:
    """Unifies Paper/Experiment/ResearchNote per design §5.2 / §10.4.

    ONTOLOGY.md §3.2 already groups these three as behaviorally identical
    ("source-anchored", "unit of forget()", "carries a node_set tag") —
    this model mirrors that boundary rather than inventing a new one.
    """

    id: str
    project_id: str
    source_type: SourceType
    title: str
    ingested_at: datetime
    node_set: str
    raw_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hypothesis:
    id: str
    statement: str
    status: Literal["active", "retired"]


@dataclass
class Finding:
    id: str
    statement: str
    quantitative_value: str | None = None
    source_id: str | None = None


@dataclass
class Evidence:
    """One edge of an evidence chain (typically SUPPORTS/CONTRADICTS, but
    typed as RelationshipType | str — matching MemoryEdge.relationship —
    since find_evidence() (design review, pre-2.2) is general-purpose, not
    hardcoded to those two relationships)."""

    evidence_node: MemoryNode
    hypothesis: Hypothesis
    relationship: RelationshipType | str
    source: SourceRecord | None = None


# ---------------------------------------------------------------------------
# §5.3 Operation results
# ---------------------------------------------------------------------------
@dataclass
class IngestResult:
    source_id: str
    project_id: str
    status: Literal["created", "skipped_duplicate", "degraded"]
    nodes_created: int
    edges_created: int
    duration_ms: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class RecallResult:
    """The design brief's "QueryResult" — named for the verb it pairs with (recall())."""

    query: str
    answer: str
    evidence: list[Evidence]
    evidence_graph: MemoryGraph | None
    degraded: bool
    strategy_used: str
    duration_ms: int
    raw_llm_context: str | None = None
    """The raw graph context the LLM was given (Cognee's only_context=True
    equivalent), captured for transparency/demo purposes — architecture
    review, pre-2.2. Not used to compute evidence/evidence_graph, which are
    always deterministic traversal (design §1.1); this is purely
    "show your work" for judges/debugging."""


@dataclass
class ForgetResult:
    source_id: str
    deleted: bool
    already_absent: bool
    orphans_pruned: int


@dataclass
class MemoryStats:
    project_id: str
    source_counts: dict[str, int] = field(default_factory=dict)
    entity_counts: dict[EntityType, int] | None = None
    active_hypotheses: int = 0
    last_ingest_at: datetime | None = None
