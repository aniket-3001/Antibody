"""Live threat feed + shared-tactic graph (spec §8, §16 beats 3 & 5).

GET /feed      → totals, trending families, recent reports, emerging campaigns
GET /families  → all known families with signatures + guidance
GET /graph     → shared-tactic map (tactics used across ≥2 families)
"""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from api.memory import store

router = APIRouter(tags=["feed"])


def _hours_since(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=UTC)
        return (datetime.now(UTC) - dt).total_seconds() / 3600.0
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


_TYPE_COLOR = {"family": "#6b5cf0", "tactic_shared": "#ef4d63", "tactic": "#f2971b", "lure": "#14b083"}


@router.get("/graph")
async def graph() -> dict:
    """Single shared-tactic knowledge graph: family + tactic + lure nodes.

    Node shape: {id, label, type, props, color} — edge shape: {id, from, to,
    label, props}. `Tactic`/`Lure` nodes are de-duped so the same string is one
    node shared across families — that's the traversal the graph beat proves.
    """
    fams = store.all_families()
    tactic_families: dict[str, set[str]] = {}
    lure_families: dict[str, set[str]] = {}
    for f in fams:
        for t in f.get("tactics") or []:
            tactic_families.setdefault(t, set()).add(f["name"])
        for lure in f.get("lures") or []:
            lure_families.setdefault(lure, set()).add(f["name"])

    nodes = []
    edges = []
    edge_id = 0

    for f in fams:
        fid = f"family:{f['name']}"
        nodes.append({
            "id": fid,
            "label": f["name"].replace("_", " ").title(),
            "type": "family",
            "color": _TYPE_COLOR["family"],
            "props": {
                "summary": f.get("summary") or "",
                "report_count": store.family_report_count(f["name"]),
                "first_seen": f.get("first_seen"),
                "last_seen": f.get("last_seen"),
                "channels": ", ".join(f.get("channels") or []),
            },
        })
        for t in f.get("tactics") or []:
            edge_id += 1
            edges.append({"id": edge_id, "from": fid, "to": f"tactic:{t}", "label": "uses", "props": {}})
        for lure in f.get("lures") or []:
            edge_id += 1
            edges.append({"id": edge_id, "from": fid, "to": f"lure:{lure}", "label": "lures_with", "props": {}})

    for t, fams_using in tactic_families.items():
        shared = len(fams_using) >= 2
        nodes.append({
            "id": f"tactic:{t}",
            "label": t.replace("_", " "),
            "type": "tactic",
            "color": _TYPE_COLOR["tactic_shared" if shared else "tactic"],
            "props": {"shared": shared, "used_by": ", ".join(sorted(fams_using))},
        })

    for lure, fams_using in lure_families.items():
        nodes.append({
            "id": f"lure:{lure}",
            "label": lure.replace("_", " "),
            "type": "lure",
            "color": _TYPE_COLOR["lure"],
            "props": {"used_by": ", ".join(sorted(fams_using))},
        })

    return {"nodes": nodes, "edges": edges}
