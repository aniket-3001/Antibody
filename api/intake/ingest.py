"""Ingest service — the write path shared by the API router and the seeder.

Splits the fast op (record to the ops store + local semantic index → instant
verdict) from the slow op (Cognee add + cognify → graph enrichment), so the
user gets a verdict immediately while the graph strengthens in the background.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone

from api.memory import indicators as ind
from api.memory import store
from api.memory.memory_service import MemoryUnavailable, memory_service
from api.memory.semantic import semantic_index

log = logging.getLogger("antibody.ingest")


def anon_reporter(raw: str | None) -> str:
    """Hash any reporter handle so PII never lands in the graph (spec §10)."""
    if not raw:
        raw = "anon-" + uuid.uuid4().hex[:8]
    return "r_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def record_report(
    normalized_text: str,
    *,
    channel: str | None = None,
    family: str | None = None,
    reporter_id: str | None = None,
    outcome: str | None = None,
    is_control: bool = False,
    reported_at: str | None = None,
) -> str:
    """Fast path: write to ops store + semantic index. Returns report_id."""
    report_id = "rep_" + uuid.uuid4().hex[:12]
    rid = anon_reporter(reporter_id)
    store.ensure_reporter(rid)

    indicators = ind.extract_indicators(normalized_text)
    tactics = ind.tag_tactics(normalized_text)
    lures = ind.tag_lures(normalized_text)

    store.add_report(
        report_id=report_id,
        normalized_text=normalized_text,
        channel=channel,
        family_name=family,
        reporter_id=rid,
        indicators=indicators,
        tactics=tactics,
        lures=lures,
        outcome=outcome,
        is_control=is_control,
        reported_at=reported_at,
    )
    # Known-bad indicators become fast-path CONFIRMED keys for their family.
    if family and not is_control:
        for i in indicators:
            store.upsert_indicator(i["value"], i["kind"], family)
        store.upsert_family(
            family, tactics=tactics, lures=lures,
            channels=[channel] if channel else [],
            seen_at=reported_at,
        )
    semantic_index.add(report_id, None if is_control else family, normalized_text,
                       is_control=is_control)
    return report_id


def _derive_family_name(tactics: list[str], lures: list[str]) -> str:
    """Human-readable family stem for a newly-surfaced scam: prefer its dominant
    lure, then a tactic, so similar future reports cluster under the same name."""
    stem = lures[0] if lures else (tactics[0] if tactics else "community_reported")
    return stem if stem.endswith("_scam") else f"{stem}_scam"


def promote_to_family(report_id: str) -> str | None:
    """Turn a user-confirmed *unrecognized* report into a recognizable family.

    This is the improve loop's entry point for NOVEL scams (spec §9): without it,
    marking an unknown message as a scam changes nothing and the next person who
    receives it is still told "not recognized". Promotion registers the report's
    text (via the semantic index), indicators, and tactic/lure signature under a
    new family so the community is warned on the next sighting.

    Idempotent — returns the existing family if one is already assigned.
    """
    rep = store.get_report(report_id)
    if rep is None:
        return None
    if rep["family_name"]:
        return rep["family_name"]

    fam = _derive_family_name(rep["tactics"], rep["lures"])
    store.set_report_family(report_id, fam)
    store.upsert_family(
        fam,
        summary="Community-flagged scam pattern (first surfaced by user reports).",
        tactics=rep["tactics"], lures=rep["lures"],
        channels=[rep["channel"]] if rep["channel"] else [],
        seen_at=rep["reported_at"],
    )
    for i in rep["indicators"]:
        store.upsert_indicator(i["value"], i["kind"], fam)
    # Re-index so this report now matches future look-alikes under `fam`.
    rebuild_semantic_index()
    log.info("promoted report %s → new family %s", report_id, fam)
    return fam


async def remember_in_cognee(text: str, *, report_id: str, channel: str | None,
                             family: str | None, cognify: bool = True) -> None:
    """Slow path: hand the report to Cognee's graph. Safe to call in background.

    Persists the returned data_id back onto the report row so a later
    forget() can scope its delete to exactly this document (spec §10)."""
    try:
        data_id = await memory_service.add(text, channel=channel, family=family)
        if data_id:
            store.set_cognee_data_id(report_id, data_id)
        if cognify:
            await memory_service.cognify()
    except MemoryUnavailable as exc:
        log.info("Cognee unavailable, running in local-only mode: %s", exc)
    except Exception:
        log.exception("Cognee remember failed (non-fatal)")


def rebuild_semantic_index() -> None:
    """Rebuild the in-memory semantic index from active (non-pruned) reports."""
    semantic_index.clear()
    for r in store.active_reports():
        fam = None if r["is_control"] else r["family_name"]
        semantic_index.add(r["id"], fam, r["normalized_text"], is_control=r["is_control"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
