"""Ops DB — the de-identified operational store that lives BESIDE Cognee's graph.

Spec §10: the scam knowledge (families, tactics, indicators) is the durable
value and lives in Cognee's de-identified graph. This SQLite DB holds the
operational rows — the report log, reporter trust, known-bad indicator lookup,
per-family guidance — that power the deterministic signals feeding confidence
fusion (§6) and the live threat feed (§8). Reporter PII never enters Cognee;
deleting a reporter here is a normal DB delete, never graph surgery.

Plain synchronous sqlite3 (single-user hackathon scale) guarded by one lock;
called from async endpoints via a tiny threadpool hop where it matters.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_conn: Optional[sqlite3.Connection] = None
_lock = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(data_dir: Path) -> None:
    global _conn
    data_dir.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(str(data_dir / "antibody_ops.db"), check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    with _lock, _conn:
        _conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS reporters (
                id TEXT PRIMARY KEY,
                trust REAL NOT NULL DEFAULT 0.3,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS families (
                name TEXT PRIMARY KEY,
                summary TEXT,
                first_seen TEXT,
                last_seen TEXT,
                tactics_json TEXT DEFAULT '[]',
                lures_json TEXT DEFAULT '[]',
                channels_json TEXT DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                normalized_text TEXT NOT NULL,
                channel TEXT,
                family_name TEXT,
                reporter_id TEXT,
                reported_at TEXT NOT NULL,
                outcome TEXT,
                indicators_json TEXT DEFAULT '[]',
                tactics_json TEXT DEFAULT '[]',
                lures_json TEXT DEFAULT '[]',
                is_control INTEGER NOT NULL DEFAULT 0,
                pruned INTEGER NOT NULL DEFAULT 0,
                cognee_data_id TEXT
            );
            CREATE TABLE IF NOT EXISTS indicators (
                value TEXT NOT NULL,
                kind TEXT NOT NULL,
                family_name TEXT,
                PRIMARY KEY (value, kind)
            );
            CREATE TABLE IF NOT EXISTS guidance (
                family_name TEXT PRIMARY KEY,
                do_now_json TEXT DEFAULT '[]',
                report_to_json TEXT DEFAULT '[]',
                recovery_json TEXT DEFAULT '[]'
            );
            CREATE INDEX IF NOT EXISTS idx_reports_family ON reports(family_name);
            CREATE INDEX IF NOT EXISTS idx_reports_time ON reports(reported_at);
            """
        )
        # Migration for DBs created before cognee_data_id existed.
        cols = {r["name"] for r in _conn.execute("PRAGMA table_info(reports)").fetchall()}
        if "cognee_data_id" not in cols:
            with _lock, _conn:
                _conn.execute("ALTER TABLE reports ADD COLUMN cognee_data_id TEXT")


def _c() -> sqlite3.Connection:
    if _conn is None:
        raise RuntimeError("store not initialized — call init_db() first")
    return _conn


# ----- reporters / trust (spec §9 anti-poisoning) -----

def ensure_reporter(reporter_id: str) -> float:
    with _lock, _c() as c:
        row = c.execute("SELECT trust FROM reporters WHERE id=?", (reporter_id,)).fetchone()
        if row:
            return row["trust"]
        c.execute(
            "INSERT INTO reporters (id, trust, created_at) VALUES (?,?,?)",
            (reporter_id, 0.3, _now()),
        )
        return 0.3


def bump_trust(reporter_id: str, delta: float) -> None:
    with _lock, _c() as c:
        c.execute(
            "UPDATE reporters SET trust = MAX(0.0, MIN(1.0, trust + ?)) WHERE id=?",
            (delta, reporter_id),
        )


# ----- families -----

def upsert_family(
    name: str,
    summary: str = "",
    tactics: Optional[list] = None,
    lures: Optional[list] = None,
    channels: Optional[list] = None,
    seen_at: Optional[str] = None,
) -> None:
    seen = seen_at or _now()
    with _lock, _c() as c:
        row = c.execute("SELECT name, first_seen FROM families WHERE name=?", (name,)).fetchone()
        if row is None:
            c.execute(
                "INSERT INTO families (name, summary, first_seen, last_seen, tactics_json, lures_json, channels_json) "
                "VALUES (?,?,?,?,?,?,?)",
                (name, summary, seen, seen,
                 json.dumps(tactics or []), json.dumps(lures or []), json.dumps(channels or [])),
            )
        else:
            # merge tactics/lures/channels; keep earliest first_seen, latest last_seen
            existing = get_family(name) or {}
            merged_t = sorted(set((existing.get("tactics") or []) + (tactics or [])))
            merged_l = sorted(set((existing.get("lures") or []) + (lures or [])))
            merged_ch = sorted(set((existing.get("channels") or []) + (channels or [])))
            c.execute(
                "UPDATE families SET summary=COALESCE(NULLIF(?,''), summary), last_seen=?, "
                "tactics_json=?, lures_json=?, channels_json=? WHERE name=?",
                (summary, seen, json.dumps(merged_t), json.dumps(merged_l),
                 json.dumps(merged_ch), name),
            )


def get_family(name: str) -> Optional[dict]:
    with _lock, _c() as c:
        row = c.execute("SELECT * FROM families WHERE name=?", (name,)).fetchone()
    if not row:
        return None
    return {
        "name": row["name"],
        "summary": row["summary"],
        "first_seen": row["first_seen"],
        "last_seen": row["last_seen"],
        "tactics": json.loads(row["tactics_json"] or "[]"),
        "lures": json.loads(row["lures_json"] or "[]"),
        "channels": json.loads(row["channels_json"] or "[]"),
    }


def all_families() -> list[dict]:
    with _lock, _c() as c:
        rows = c.execute("SELECT name FROM families ORDER BY name").fetchall()
    return [get_family(r["name"]) for r in rows]


# ----- reports -----

def add_report(
    report_id: str,
    normalized_text: str,
    channel: Optional[str],
    family_name: Optional[str],
    reporter_id: Optional[str],
    indicators: Optional[list] = None,
    tactics: Optional[list] = None,
    lures: Optional[list] = None,
    outcome: Optional[str] = None,
    is_control: bool = False,
    reported_at: Optional[str] = None,
) -> None:
    with _lock, _c() as c:
        c.execute(
            "INSERT OR REPLACE INTO reports "
            "(id, normalized_text, channel, family_name, reporter_id, reported_at, outcome, "
            " indicators_json, tactics_json, lures_json, is_control, pruned) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,0)",
            (report_id, normalized_text, channel, family_name, reporter_id,
             reported_at or _now(), outcome,
             json.dumps(indicators or []), json.dumps(tactics or []),
             json.dumps(lures or []), 1 if is_control else 0),
        )


def set_outcome(report_id: str, outcome: str) -> tuple[bool, Optional[str]]:
    """Record an outcome. Returns (found, family_name).

    family_name is legitimately None for unrecognized reports that exist but
    were never assigned a family — callers must key off `found`, not the family,
    to detect a missing report (else outcomes on unrecognized reports 404)."""
    with _lock, _c() as c:
        row = c.execute("SELECT family_name FROM reports WHERE id=?", (report_id,)).fetchone()
        if row is None:
            return False, None
        c.execute("UPDATE reports SET outcome=? WHERE id=?", (outcome, report_id))
        return True, row["family_name"]


def get_report(report_id: str) -> Optional[dict]:
    with _lock, _c() as c:
        row = c.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    return _report_row(row) if row else None


def set_report_family(report_id: str, family_name: str) -> None:
    with _lock, _c() as c:
        c.execute("UPDATE reports SET family_name=? WHERE id=?", (family_name, report_id))


def set_cognee_data_id(report_id: str, data_id: str) -> None:
    """Record the real Cognee data_id for this report so forget() can later
    scope a deletion to exactly this document (spec §10)."""
    with _lock, _c() as c:
        c.execute("UPDATE reports SET cognee_data_id=? WHERE id=?", (data_id, report_id))


def prune_report(report_id: str) -> None:
    """Soft-delete for the forget() false-positive path (§10) — stops it
    poisoning semantic matches while leaving an audit trail."""
    with _lock, _c() as c:
        c.execute("UPDATE reports SET pruned=1 WHERE id=?", (report_id,))


def active_reports() -> list[dict]:
    with _lock, _c() as c:
        rows = c.execute("SELECT * FROM reports WHERE pruned=0").fetchall()
    return [_report_row(r) for r in rows]


def _report_row(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "normalized_text": r["normalized_text"],
        "channel": r["channel"],
        "family_name": r["family_name"],
        "reporter_id": r["reporter_id"],
        "reported_at": r["reported_at"],
        "outcome": r["outcome"],
        "indicators": json.loads(r["indicators_json"] or "[]"),
        "tactics": json.loads(r["tactics_json"] or "[]"),
        "lures": json.loads(r["lures_json"] or "[]"),
        "is_control": bool(r["is_control"]),
        "cognee_data_id": r["cognee_data_id"],
    }


def family_report_count(name: str) -> int:
    with _lock, _c() as c:
        row = c.execute(
            "SELECT COUNT(*) n FROM reports WHERE family_name=? AND pruned=0 "
            "AND (outcome IS NULL OR outcome != 'actually_legit')",
            (name,),
        ).fetchone()
    return int(row["n"])


def trust_weighted_reporters(name: str) -> float:
    """Sum of distinct reporters' trust for a family (spec §9: trust-weighted
    distinct reporters, not raw submission count — resists sockpuppet floods)."""
    with _lock, _c() as c:
        rows = c.execute(
            "SELECT DISTINCT reporter_id FROM reports WHERE family_name=? AND pruned=0 "
            "AND reporter_id IS NOT NULL "
            "AND (outcome IS NULL OR outcome != 'actually_legit')",
            (name,),
        ).fetchall()
        total = 0.0
        for r in rows:
            t = c.execute("SELECT trust FROM reporters WHERE id=?", (r["reporter_id"],)).fetchone()
            total += (t["trust"] if t else 0.3)
    return total


def family_first_seen(name: str) -> Optional[str]:
    with _lock, _c() as c:
        row = c.execute(
            "SELECT MIN(reported_at) m FROM reports WHERE family_name=? AND pruned=0", (name,)
        ).fetchone()
    return row["m"] if row else None


# ----- indicators (known-bad IOC lookup — the CONFIRMED fast path) -----

def upsert_indicator(value: str, kind: str, family_name: Optional[str]) -> None:
    with _lock, _c() as c:
        c.execute(
            "INSERT OR REPLACE INTO indicators (value, kind, family_name) VALUES (?,?,?)",
            (value.lower().strip(), kind, family_name),
        )


def lookup_indicator(value: str) -> Optional[dict]:
    with _lock, _c() as c:
        row = c.execute(
            "SELECT value, kind, family_name FROM indicators WHERE value=?",
            (value.lower().strip(),),
        ).fetchone()
    return {"value": row["value"], "kind": row["kind"], "family_name": row["family_name"]} if row else None


def all_indicators() -> list[dict]:
    with _lock, _c() as c:
        rows = c.execute("SELECT value, kind, family_name FROM indicators").fetchall()
    return [{"value": r["value"], "kind": r["kind"], "family_name": r["family_name"]} for r in rows]


# ----- guidance (curated per-family playbook) -----

def set_guidance(family_name: str, do_now: list, report_to: list, recovery: list) -> None:
    with _lock, _c() as c:
        c.execute(
            "INSERT OR REPLACE INTO guidance (family_name, do_now_json, report_to_json, recovery_json) "
            "VALUES (?,?,?,?)",
            (family_name, json.dumps(do_now), json.dumps(report_to), json.dumps(recovery)),
        )


def get_guidance(family_name: str) -> Optional[dict]:
    with _lock, _c() as c:
        row = c.execute("SELECT * FROM guidance WHERE family_name=?", (family_name,)).fetchone()
    if not row:
        return None
    return {
        "do_now": json.loads(row["do_now_json"] or "[]"),
        "report_to": json.loads(row["report_to_json"] or "[]"),
        "recovery": json.loads(row["recovery_json"] or "[]"),
    }


# ----- feed aggregation (spec §8 live threat feed) -----

def feed_stats(window_days: int = 30) -> dict[str, Any]:
    with _lock, _c() as c:
        total = c.execute("SELECT COUNT(*) n FROM reports WHERE pruned=0").fetchone()["n"]
        fam_rows = c.execute(
            "SELECT family_name, COUNT(*) n, MAX(reported_at) last "
            "FROM reports WHERE pruned=0 AND family_name IS NOT NULL "
            "GROUP BY family_name ORDER BY n DESC",
        ).fetchall()
        recent = c.execute(
            "SELECT id, normalized_text, channel, family_name, reported_at, outcome "
            "FROM reports WHERE pruned=0 ORDER BY reported_at DESC LIMIT 15"
        ).fetchall()
    families = [
        {"name": r["family_name"], "count": r["n"], "last_seen": r["last"]}
        for r in fam_rows
    ]
    recent_list = [
        {
            "id": r["id"],
            "preview": (r["normalized_text"] or "")[:140],
            "channel": r["channel"],
            "family": r["family_name"],
            "reported_at": r["reported_at"],
            "outcome": r["outcome"],
        }
        for r in recent
    ]
    return {"total_reports": total, "families": families, "recent": recent_list}


def shared_tactic_map() -> list[dict]:
    """For the graph beat (spec §16 beat 3): tactics shared across families.
    Pure traversal over the ops mirror of the ontology's shared Tactic nodes."""
    fams = all_families()
    tactic_to_families: dict[str, list[str]] = {}
    for f in fams:
        for t in f.get("tactics") or []:
            tactic_to_families.setdefault(t, []).append(f["name"])
    return [
        {"tactic": t, "families": sorted(set(fs))}
        for t, fs in sorted(tactic_to_families.items(), key=lambda kv: -len(set(kv[1])))
        if len(set(fs)) >= 2
    ]
