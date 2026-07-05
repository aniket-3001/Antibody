"""Multimodal intake dispatch (spec §11). The extractors degrade to "" when a
lib/binary is missing; here we pin the routing and the deterministic-transcript
sidecar path that make screenshot/audio/PDF intake safe to ship."""
from __future__ import annotations

from api.intake.loaders import extract_from_pdf, extract_text


def test_extract_text_reads_plain_txt(tmp_path):
    p = tmp_path / "report.txt"
    p.write_text("pay a small redelivery fee at scam-site.biz", encoding="utf-8")
    assert extract_text(str(p), "text/plain") == "pay a small redelivery fee at scam-site.biz"


def test_extract_text_prefers_txt_sidecar_for_media(tmp_path):
    """A .txt sidecar next to an image/audio file ships a deterministic
    transcript for the demo, taking priority over OCR/transcription."""
    img = tmp_path / "screenshot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n not a real image")
    (tmp_path / "screenshot.txt").write_text("URGENT verify your account now", encoding="utf-8")
    assert extract_text(str(img), "image/png") == "URGENT verify your account now"


def test_extract_text_unknown_extension_returns_empty(tmp_path):
    p = tmp_path / "mystery.bin"
    p.write_bytes(b"\x00\x01\x02")
    assert extract_text(str(p), "application/octet-stream") == ""


def test_extract_from_pdf_on_invalid_file_degrades_gracefully(tmp_path):
    """A corrupt/non-PDF must return "" rather than raising — intake never
    hard-fails on a bad upload."""
    p = tmp_path / "broken.pdf"
    p.write_bytes(b"this is not a pdf")
    assert extract_from_pdf(str(p)) == ""


def test_extract_text_image_without_sidecar_never_raises(tmp_path):
    """OCR on a non-image byte blob returns "" instead of crashing intake."""
    img = tmp_path / "fake.jpg"
    img.write_bytes(b"not an image")
    # No sidecar: dispatches to OCR, which must swallow the failure.
    assert extract_text(str(img), "image/jpeg") == ""
