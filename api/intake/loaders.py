"""Multimodal extraction (spec §11) — best-effort local text extraction for the
deterministic + semantic layer, alongside handing the RAW file to Cognee's
native loaders for the graph (the 'multimodal at the Cognee layer' claim).

Every extractor is optional and degrades to "" if its lib/key is missing, so
intake never hard-fails on a screenshot or call clip — the raw file still flows
into Cognee, and the text layer uses whatever we could pull out.
"""
from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("antibody.loaders")


def extract_from_image(path: str) -> str:
    """OCR a screenshot. Uses pytesseract if installed; else empty."""
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore

        return pytesseract.image_to_string(Image.open(path)).strip()
    except Exception:
        log.debug("image OCR unavailable for %s", path, exc_info=True)
        return ""


def extract_from_audio(path: str) -> str:
    """Transcribe a scam-call clip. Uses faster-whisper if installed; else empty."""
    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(path)
        return " ".join(s.text for s in segments).strip()
    except Exception:
        log.debug("audio transcription unavailable for %s", path, exc_info=True)
        return ""


def extract_from_pdf(path: str) -> str:
    """Pull text out of a PDF (fake invoice, forwarded phishing chain saved as a
    doc, etc). Uses PyMuPDF if installed; else empty."""
    try:
        import fitz  # type: ignore  # PyMuPDF

        with fitz.open(path) as doc:
            return "\n".join(page.get_text() for page in doc).strip()
    except Exception:
        log.debug("PDF text extraction unavailable for %s", path, exc_info=True)
        return ""


def extract_text(path: str, content_type: str | None) -> str:
    """Dispatch on content type / extension. Reads a plain sidecar if present."""
    p = Path(path)
    ct = (content_type or "").lower()
    ext = p.suffix.lower()

    # A .txt with the same stem lets the demo ship deterministic transcripts.
    sidecar = p.with_suffix(".txt")
    if sidecar.exists() and sidecar != p:
        try:
            return sidecar.read_text(encoding="utf-8").strip()
        except Exception:
            pass

    if ct.startswith("image/") or ext in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return extract_from_image(path)
    if ct.startswith("audio/") or ext in {".wav", ".mp3", ".m4a", ".ogg", ".flac"}:
        return extract_from_audio(path)
    if ct == "application/pdf" or ext == ".pdf":
        return extract_from_pdf(path)
    if ext in {".txt", ".md", ".eml"}:
        try:
            return p.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            return ""
    return ""
