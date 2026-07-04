"""Live threat feed + shared-tactic graph (spec §8, §16 beats 3 & 5).

GET /feed      → totals, trending families, recent reports, emerging campaigns
GET /families  → all known families with signatures + guidance
GET /graph     → shared-tactic map (tactics used across ≥2 families)
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from api.memory import store

router = APIRouter(tags=["feed"])


def _hours_since(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
    except ValueError:
        return None


@router.get("/feed")
async def feed() -> dict:
    stats = store.feed_stats()
    # Enrich trending families with recency + first_seen for the timeline.
    families = []
    for f in stats["families"]:
        fam = store.get_family(f["name"]) or {}
        families.append({
            **f,
            "display": f["name"].replace("_", " ").title(),
            "first_seen": store.family_first_seen(f["name"]),
            "hours_since_last": _hours_since(f["last_seen"]),
            "tactics": fam.get("tactics", []),
        })

    # Emerging-campaign heuristic (spec §8, kept lightweight): a family whose
    # first report is recent AND is climbing fast.
    emerging = []
    for f in families:
        hrs = _hours_since(f.get("first_seen"))
        if hrs is not None and hrs <= 72 and f["count"] >= 3:
            emerging.append({
                "name": f["name"],
                "display": f["display"],
                "count": f["count"],
                "emerged_hours_ago": round(hrs, 1),
            })

    return {
        "total_reports": stats["total_reports"],
        "families": families,
        "recent": stats["recent"],
        "shared_tactics": store.shared_tactic_map(),
        "emerging": emerging,
    }


@router.get("/families")
async def families() -> dict:
    out = []
    for f in store.all_families():
        out.append({
            **f,
            "display": f["name"].replace("_", " ").title(),
            "report_count": store.family_report_count(f["name"]),
            "guidance": store.get_guidance(f["name"]),
        })
    out.sort(key=lambda x: x["report_count"], reverse=True)
    return {"families": out}


@router.get("/graph")
async def graph() -> dict:
    """Nodes = families + shared tactics; edges = family→tactic (for the viz)."""
    fams = store.all_families()
    shared = {e["tactic"] for e in store.shared_tactic_map()}
    nodes = []
    edges = []
    for f in fams:
        nodes.append({"id": f"family:{f['name']}", "label": f["name"].replace("_", " ").title(),
                      "type": "family", "count": store.family_report_count(f["name"])})
        for t in f.get("tactics", []):
            tid = f"tactic:{t}"
            nodes.append({"id": tid, "label": t.replace("_", " "), "type": "tactic",
                          "shared": t in shared})
            edges.append({"source": f"family:{f['name']}", "target": tid})
    # de-dup tactic nodes
    seen = set()
    uniq = []
    for n in nodes:
        if n["id"] in seen:
            continue
        seen.add(n["id"])
        uniq.append(n)
    return {"nodes": uniq, "edges": edges}
