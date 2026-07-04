"""Report intake + lifecycle endpoints (M1 + verdict surface).

POST /report            → verdict now, graph-strengthen in background
POST /report/{id}/outcome → fold the outcome back in (improve / memify)
POST /report/{id}/forget  → prune a false positive (forget §10)
"""
from __future__ import annotations

import logging
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


async def _process(text: str, channel: str | None, reporter_id: str | None,
                   background: BackgroundTasks) -> dict:
    text = (text or "").strip()
    if not text:
        raise HTTPException(400, "empty report — nothing to assess")

    # 1) verdict from current memory (fast, deterministic + semantic)
    verdict = await assess(text, channel=channel, reporter_id=reporter_id)

    # 2) record the report (contributes back — spec §3 step 4)
    report_id = ingest.record_report(
        text, channel=channel, family=verdict.get("family"), reporter_id=reporter_id
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


@router.post("/report/upload")
async def submit_upload(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    channel: str | None = Form(None),
    reporter_id: str | None = Form(None),
) -> dict:
    """Multimodal intake: SMS screenshot / scam-call audio (spec §11)."""
    suffix = Path(file.filename or "upload").suffix or ".bin"
    tmp = Path(tempfile.gettempdir()) / f"antibody_{uuid.uuid4().hex}{suffix}"
    tmp.write_bytes(await file.read())

    text = extract_text(str(tmp), file.content_type)
    # Hand the RAW file to Cognee's native loaders regardless (graph-layer multimodal).
    background.add_task(_remember_raw_file, str(tmp), channel, text)

    kind = "audio" if (file.content_type or "").startswith("audio/") else "image"
    if not text:
        return {
            "band": "unrecognized",
            "band_label": "Couldn't read the file",
            "band_emoji": "⚪",
            "confidence": 0.0,
            "explanation": (
                "We couldn't extract text from this file locally (OCR/transcription "
                "not installed), but the raw file was still added to the shared graph. "
                "Paste the message text for an instant verdict."
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
