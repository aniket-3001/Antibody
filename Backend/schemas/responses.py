"""Pydantic response models.

Spec reference: BACKEND_API_SPEC.md §5 (per-endpoint response shapes).

All datetimes are serialised as UTC ISO-8601 strings ("2026-07-02T11:00:00Z").
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# ── Shared Cytoscape graph type (spec §6) ─────────────────────────────────────

class CytoscapeNodeData(BaseModel):
    id: str
    label: str
    type: str
    source_ids: list[str] = []
    attributes: dict[str, Any] = {}


class CytoscapeEdgeData(BaseModel):
    id: str
    source: str
    target: str
    label: str
    relationship: str


class CytoscapeElement(BaseModel):
    data: CytoscapeNodeData | CytoscapeEdgeData
    classes: str


class CytoscapeGraph(BaseModel):
    """Cytoscape.js elements array format (spec §6.1)."""
    elements: list[dict[str, Any]]
    node_count: int
    edge_count: int


# ── /remember  /improve ───────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    """Spec §5.1 / §5.2 response.  Status codes 200 or 201 depending on status."""
    source_id: str
    status: str
    nodes_created: int
    edges_created: int
    duration_ms: int
    warnings: list[str]


# ── /recall ───────────────────────────────────────────────────────────────────

class RecallResponse(BaseModel):
    """Spec §5.3 response."""
    query: str
    answer: str
    strategy_used: str
    evidence_graph: CytoscapeGraph | None
    degraded: bool
    duration_ms: int


# ── /forget ───────────────────────────────────────────────────────────────────

class ForgetResponse(BaseModel):
    """Spec §5.4 response."""
    source_id: str
    deleted: bool
    orphans_pruned: int


# ── /sources ──────────────────────────────────────────────────────────────────

class SourceItem(BaseModel):
    source_id: str
    title: str
    source_type: str
    ingested_at: str


class SourcesResponse(BaseModel):
    """Spec §5.5 response."""
    sources: list[SourceItem]
    total: int


# ── /stats ────────────────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    """Spec §5.7 response."""
    total_sources: int
    active_hypotheses: int
    entity_counts: dict[str, int] | None
    last_ingest_at: str | None


# ── /health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Spec §5.8 response (200 OK)."""
    status: str
    memory_core_mode: str
    provider: str | None = None
    version: str


class HealthDegradedResponse(BaseModel):
    """Spec §5.8 response (503 Service Unavailable)."""
    status: str
    memory_core_mode: str
    error: dict[str, str]
