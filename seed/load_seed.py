"""Seed loader — populate the ops store (and optionally Cognee) so recall never
demos against an empty graph (spec §14). Idempotent: no-op if already seeded.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from api.intake.ingest import record_report
from api.memory import store
from seed.seed_data import FAMILIES, LEGIT_CONTROLS

log = logging.getLogger("antibody.seed")


def _ts(days_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def load_seed_if_empty() -> int:
    """Load seed data if the store has no families yet. Returns #reports added."""
    if store.all_families():
        return 0
    return _load()


def _load() -> int:
    count = 0
    for name, fam in FAMILIES.items():
        # 1) family signature + guidance + known-bad indicators
        store.upsert_family(
            name,
            summary=fam["summary"],
            tactics=fam["tactics"],
            lures=fam["lures"],
            channels=fam.get("channels", []),
            seen_at=_ts(14),
        )
        g = fam["guidance"]
        store.set_guidance(name, g["do_now"], g["report_to"], g["recovery"])
        for value, kind in fam.get("indicators", []):
            store.upsert_indicator(value, kind, name)

        # 2) reports — spread over time, distinct reporters
        variants = fam["reports"]
        emerging = fam.get("emerging", False)
        target = fam.get("hero_count") or (9 if emerging else len(variants) * 2)
        span_days = 2.0 if emerging else 12.0
        channel = (fam.get("channels") or ["sms"])[0]

        for i in range(target):
            text = variants[i % len(variants)]
            # newest first: report 0 is most recent
            days_ago = (i / max(1, target - 1)) * span_days if target > 1 else 0.0
            record_report(
                text,
                channel=channel,
                family=name,
                reporter_id=f"seed-user-{name}-{i}",
                reported_at=_ts(days_ago),
            )
            count += 1

    # 3) legit controls — recorded as controls (no family), must NOT be flagged
    for i, text in enumerate(LEGIT_CONTROLS):
        record_report(
            text,
            channel="sms",
            family=None,
            reporter_id=f"seed-control-{i}",
            is_control=True,
            reported_at=_ts(1.0),
        )
        count += 1

    log.info("seed loaded: %d reports, %d families", count, len(FAMILIES))
    return count


async def cognify_seed() -> int:
    """Push every seeded report into Cognee and build the graph once.

    Requires an LLM key. Run standalone: `python -m seed.load_seed`.
    """
    from api.intake.ingest import remember_in_cognee
    from api.memory.memory_service import memory_service

    reports = [r for r in store.active_reports() if not r["is_control"]]
    for r in reports:
        await remember_in_cognee(
            r["normalized_text"], channel=r["channel"],
            family=r["family_name"], cognify=False,  # batch: cognify once at the end
        )
    await memory_service.cognify()
    return len(reports)


if __name__ == "__main__":
    import asyncio

    from api.config import settings

    store.init_db(settings.data_dir)
    n = load_seed_if_empty()
    print(f"ops store: {n} reports seeded (0 = already present)")
    if settings.has_llm:
        print("cognifying seed into Cognee graph (this calls the LLM)...")
        pushed = asyncio.run(cognify_seed())
        print(f"cognified {pushed} reports into the shared graph")
    else:
        print("no LLM key set — skipping Cognee cognify (local matching still works)")
