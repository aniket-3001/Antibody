"""API tests for the integrated features: read-only /scan, shareable
GET /report/{id}, and real reporter erasure (/reporter/forget)."""
from __future__ import annotations


def test_scan_returns_verdict_without_recording(client):
    r = client.post("/scan", json={
        "text": "URGENT: pay a $2.99 redelivery fee at http://usps-fee.biz",
        "channel": "sms",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["band"] in ("confirmed", "likely", "suspicious", "unrecognized")
    # Read-only: scan never records, so there is no report_id to fold back in.
    assert "report_id" not in body


def test_scan_empty_is_400(client):
    r = client.post("/scan", json={"text": "   "})
    assert r.status_code == 400
    assert r.json()["error"] == "empty_report"


def test_get_report_by_id_refetches_verdict(client):
    submitted = client.post("/report", json={
        "text": "Your parcel is held, pay a small toll fee now at http://toll-pay.biz",
        "channel": "sms",
        "reporter_id": "share-tester",
    })
    report_id = submitted.json()["report_id"]

    r = client.get(f"/report/{report_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["report_id"] == report_id
    assert body["transcript"]
    assert body["input_kind"] == "text"


def test_get_report_serves_cached_verdict(client):
    submitted = client.post("/report", json={
        "text": "Final notice: your account is suspended, verify at http://fake-bank.biz",
        "channel": "sms",
        "reporter_id": "cache-tester",
    })
    original = submitted.json()
    report_id = original["report_id"]

    r = client.get(f"/report/{report_id}")
    assert r.status_code == 200
    body = r.json()
    # Served from the verdict cached at submit time — same band and confidence.
    assert body["band"] == original["band"]
    assert body["confidence"] == original["confidence"]
    # The My Reports detail view fields ride along.
    assert "cognee_data_id" in body
    assert "outcome" in body


def test_get_missing_report_is_404(client):
    r = client.get("/report/does_not_exist")
    assert r.status_code == 404
    assert r.json()["error"] == "report_not_found"


def test_reporter_forget_erases_own_reports(client):
    rid = "erase-me-please"
    client.post("/report", json={"text": "scammy toll fee message one", "reporter_id": rid})
    client.post("/report", json={"text": "scammy toll fee message two", "reporter_id": rid})

    before = client.get("/reports/mine", params={"reporter_id": rid}).json()["reports"]
    assert len(before) >= 2

    r = client.post("/reporter/forget", json={"reporter_id": rid})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["deleted_reports"] >= 2

    after = client.get("/reports/mine", params={"reporter_id": rid}).json()["reports"]
    assert after == []


def test_extract_preview_does_not_record_a_report(client):
    files = {"file": ("scam.txt", b"pay a small redelivery fee at scam-site.biz", "text/plain")}
    r = client.post("/report/extract", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["transcript"] == "pay a small redelivery fee at scam-site.biz"
    assert body["input_kind"] == "image"  # .txt has no dedicated kind; falls back to the generic preview


def test_upload_honours_transcript_override(client):
    # The bytes are irrelevant here — transcript_override skips server-side
    # extraction entirely, letting the UI submit user-edited preview text.
    files = {"file": ("note.png", b"not a real image", "image/png")}
    r = client.post(
        "/report/upload",
        files=files,
        data={"channel": "sms", "transcript_override": "URGENT verify your account now"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["transcript"] == "URGENT verify your account now"
    assert body["input_kind"] == "image"
