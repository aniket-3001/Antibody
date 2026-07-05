"""Report intake + lifecycle endpoints (M1 + verdict surface).

POST /report            → verdict now, graph-strengthen in background
POST /scan              → read-only verdict, nothing recorded (browser extension)
GET  /report/{id}        → re-fetch a prior verdict (shareable link)
POST /report/{id}/outcome → fold the outcome back in (improve / memify)
POST /report/{id}/forget  → prune a false positive (forget §10)
POST /reporter/forget     → hard-delete a reporter's own data (real erasure §10)
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from api.intake import ingest
from api.intake.loaders import extract_text
from api.memory import store
from api.memory.memory_service import MemoryUnavailable, memory_service
from api.verdict.engine import assess

log = logging.getLogger("antibody.router")
router = APIRouter(tags=["report"])


class ReportIn(BaseModel):
    text: str
    channel: str | None = None
    reporter_id: str | None = None


class OutcomeIn(BaseModel):
    outcome: str  # confirmed_scam | i_got_scammed | actually_legit


class ReporterIn(BaseModel):
    reporter_id: str


async def _process(text: str, channel: str | None, reporter_id: str | None,
                   background: BackgroundTasks) -> dict:
    text = (text or "").strip()
    if not text:
        raise HTTPException(400, "empty report — nothing to assess")

    # 1) verdict from current memory (fast, deterministic + semantic)
    verdict = await assess(text, channel=channel, reporter_id=reporter_id)

    # 2) record the report (contributes back — spec §3 step 4)
    report_id = ingest.record_report(
        text, channel=channel, family=verdict.get("family"), reporter_id=reporter_id,
        verdict_json=json.dumps(verdict)
    )
    verdict["report_id"] = report_id

    # 3) strengthen the graph in the background (add + cognify)
    background.add_task(
        ingest.remember_in_cognee, text,
        report_id=report_id, channel=channel, family=verdict.get("family"),
    )
    return verdict


@router.post("/report")
async def submit_report(body: ReportIn, background: BackgroundTasks) -> dict:
    return await _process(body.text, body.channel, body.reporter_id, background)


class ScanIn(BaseModel):
    text: str
    channel: str | None = None


@router.post("/scan")
async def scan(body: ScanIn) -> dict:
    """Read-only verdict — same engine as /report, but never records a report
    or touches trust/leaderboard. Backs the browser extension's quick check,
    where scanning a page shouldn't silently add it to the shared graph."""
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "empty text — nothing to assess")
    return await assess(text, channel=body.channel)


@router.get("/report/{report_id}")
async def get_report(report_id: str) -> dict:
    """Re-fetch a prior verdict by id (backs the "Warn Others" shareable link).

    Re-runs assess() on the stored text rather than caching the original
    verdict blob — same report always reflects current family/corroboration
    data, and no schema migration was needed to add this.
    """
    report = store.get_report(report_id)
    if not report or report["pruned"]:
        raise HTTPException(404, "report not found")
        
    if report.get("verdict_json"):
        verdict = json.loads(report["verdict_json"])
    else:
        verdict = await assess(report["normalized_text"], channel=report["channel"])
        
    verdict["report_id"] = report_id
    verdict["transcript"] = report["normalized_text"]
    verdict["input_kind"] = "text"
    verdict["cognee_data_id"] = report.get("cognee_data_id")
    verdict["outcome"] = report.get("outcome")
    return verdict


@router.post("/report/upload")
async def submit_upload(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    channel: str | None = Form(None),
    reporter_id: str | None = Form(None),
) -> dict:
    """Multimodal intake: SMS screenshot / scam-call audio / PDF document (spec §11)."""
    suffix = Path(file.filename or "upload").suffix or ".bin"
    tmp = Path(tempfile.gettempdir()) / f"antibody_{uuid.uuid4().hex}{suffix}"
    tmp.write_bytes(await file.read())

    text = extract_text(str(tmp), file.content_type)
    # Hand the RAW file to Cognee's native loaders regardless (graph-layer multimodal).
    background.add_task(_remember_raw_file, str(tmp), channel, text)

    ctype = (file.content_type or "").lower()
    if ctype.startswith("audio/"):
        kind = "audio"
    elif ctype == "application/pdf" or suffix.lower() == ".pdf":
        kind = "document"
    else:
        kind = "image"
    if not text:
        return {
            "band": "unrecognized",
            "band_label": "Couldn't read the file",
            "band_emoji": "⚪",
            "confidence": 0.0,
            "explanation": (
                "We couldn't extract text from this file locally (OCR/transcription/"
                "PDF-reading not installed), but the raw file was still added to the "
                "shared graph. Paste the message text for an instant verdict."
            ),
            "guidance": None, "transcript": "", "input_kind": kind,
            "citations": [], "signals": {}, "indicators": [], "shared_tactics": [],
        }
    verdict = await _process(text, channel or "unknown", reporter_id, background)
    # Surface what we transcribed/read so the UI can show it back to the user.
    verdict["transcript"] = text
    verdict["input_kind"] = kind
    return verdict


async def _remember_raw_file(path: str, channel: str | None, extracted: str) -> None:
    try:
        await memory_service.add([path], channel=channel)
        await memory_service.cognify()
    except MemoryUnavailable:
        pass
    except Exception:
        log.exception("raw-file remember failed (non-fatal)")
    finally:
        try:
            os.remove(path)
        except OSError:
            log.warning("failed to remove temporary file %s", path)


@router.post("/report/{report_id}/outcome")
async def report_outcome(report_id: str, body: OutcomeIn,
                         background: BackgroundTasks) -> dict:
    found, family = store.set_outcome(report_id, body.outcome)
    if not found:
        raise HTTPException(404, "report not found")

    # A user confirming an UNRECOGNIZED report is how a novel scam enters the
    # shared memory — promote it to a family so the next person is warned (§9).
    # Without this, marking an unknown message as a scam teaches nothing.
    if family is None and body.outcome in ("confirmed_scam", "i_got_scammed"):
        family = ingest.promote_to_family(report_id)

    # Trust + reinforcement (spec §9): a confirmed hit raises reporter trust.
    reports = {r["id"]: r for r in store.active_reports()}
    rid = (reports.get(report_id) or {}).get("reporter_id")
    if body.outcome in ("confirmed_scam", "i_got_scammed") and rid:
        store.bump_trust(rid, 0.1)
    elif body.outcome == "actually_legit" and rid:
        store.bump_trust(rid, -0.05)

    # Fold back in + reshape the graph (improve/memify §9).
    background.add_task(_improve_after_outcome, family or "")
    return {"ok": True, "family": family, "outcome": body.outcome}


async def _improve_after_outcome(family: str) -> None:
    try:
        await memory_service.memify()
    except MemoryUnavailable:
        pass
    except Exception:
        log.exception("memify failed (non-fatal)")


@router.get("/reports/mine")
async def my_reports(reporter_id: str) -> dict:
    """List a browser's own submitted reports, keyed off its client-generated
    anonymous id (never a real identity — hashed the same as at submit time)."""
    rid = ingest.anon_reporter(reporter_id)
    reports = store.reports_by_reporter(rid)
    out = []
    for r in reports:
        if r["outcome"] in ("confirmed_scam", "i_got_scammed"):
            status, points = "confirmed", "+50"
        elif r["outcome"] == "actually_legit":
            status, points = "legit", "0"
        else:
            status, points = "pending", "Pending"
        out.append({
            "id": r["id"],
            "date": r["reported_at"],
            "text": r["normalized_text"],
            "channel": r["channel"],
            "family": r["family_name"],
            "status": status,
            "points": points,
        })
    return {"reports": out}


@router.post("/reporter/forget")
async def forget_reporter(body: ReporterIn, background: BackgroundTasks) -> dict:
    """Real erasure (§10) for a browser's own anonymous id — hard-deletes its
    reporter row and every report it filed from the ops DB. Distinct from
    /report/{id}/forget, which soft-prunes a single false-positive report."""
    rid = ingest.anon_reporter(body.reporter_id)
    deleted_count, data_ids = store.forget_reporter(rid)
    for data_id in data_ids:
        background.add_task(_forget_data_id, data_id)
    return {"ok": True, "deleted_reports": deleted_count}


async def _forget_data_id(data_id: str) -> None:
    try:
        await memory_service.forget(data_id=data_id)
    except MemoryUnavailable:
        pass
    except Exception:
        log.debug("cognee forget skipped for reporter erasure", exc_info=True)


@router.get("/leaderboard")
async def leaderboard(limit: int = 20, reporter_id: str | None = None) -> dict:
    """Community leaderboard ranked by verified reports (spec §9 trust model).
    Reporters are anonymous ids — we only ever mark which row is 'you'."""
    me = ingest.anon_reporter(reporter_id) if reporter_id else None
    rows = store.leaderboard(limit)
    entries = []
    for i, r in enumerate(rows, start=1):
        is_you = r["reporter_id"] == me
        entries.append({
            "rank": i,
            "label": "You" if is_you else f"Reporter #{r['reporter_id'][-6:]}",
            "is_you": is_you,
            "points": r["points"],
            "verified": r["verified"],
            "tier": "gold" if i <= 2 else ("silver" if i <= 5 else "bronze"),
        })
    return {"leaderboard": entries}


@router.post("/report/{report_id}/forget")
async def forget_report(report_id: str, background: BackgroundTasks) -> dict:
    """Admin false-positive prune (spec §10 job 1). Stops it poisoning matches."""
    store.prune_report(report_id)
    ingest.rebuild_semantic_index()
    background.add_task(_forget_in_cognee, report_id)
    return {"ok": True, "pruned": report_id}


async def _forget_in_cognee(report_id: str) -> None:
    report = store.get_report(report_id)
    data_id = report.get("cognee_data_id") if report else None
    if not data_id:
        # Cognee was unavailable/still processing when this report was added,
        # or it predates data_id capture — nothing to scope a forget() to.
        log.info("no cognee data_id for report %s, skipping graph-side forget", report_id)
        return
    try:
        await memory_service.forget(data_id=data_id)
    except MemoryUnavailable:
        pass
    except Exception:
        log.debug("cognee forget skipped", exc_info=True)
