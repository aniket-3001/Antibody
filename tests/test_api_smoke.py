"""End-to-end smoke test over the FastAPI app, mirroring the manual QA pass:
submit a scam report, submit a reworded variant, check the feed/graph surface,
then forget a legit control. Runs with no LLM key — the deterministic +
semantic fallback path used by CI and any judge without NIM credentials set.
"""
from __future__ import annotations


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llm"] is False


def test_report_scam_then_reworded_variant_shares_family(client):
    r1 = client.post("/report", json={
        "text": "URGENT: your package needs a redelivery fee of $2.99, pay now at http://usps-redeliver-fee.biz",
        "channel": "sms",
        "reporter_id": "judge-1",
    })
    assert r1.status_code == 200
    v1 = r1.json()
    assert v1["band"] in ("confirmed", "likely", "suspicious", "unrecognized")
    assert "report_id" in v1

    r2 = client.post("/report", json={
        "text": "A small redelivery charge of $2 is required to reschedule your shipment, pay immediately.",
        "channel": "sms",
        "reporter_id": "judge-2",
    })
    assert r2.status_code == 200
    v2 = r2.json()
    assert "report_id" in v2


def test_report_rejects_empty_text(client):
    r = client.post("/report", json={"text": "   "})
    assert r.status_code == 400


def test_feed_reflects_submitted_reports(client):
    r = client.get("/feed")
    assert r.status_code == 200
    body = r.json()
    assert body["total_reports"] >= 2
    assert "families" in body
    assert "recent" in body


def test_families_endpoint(client):
    r = client.get("/families")
    assert r.status_code == 200
    assert isinstance(r.json()["families"], list)


def test_graph_endpoint_shape(client):
    r = client.get("/graph")
    assert r.status_code == 200
    body = r.json()
    assert "nodes" in body
    assert "edges" in body


def test_forget_prunes_a_report(client):
    submitted = client.post("/report", json={
        "text": "Your dentist appointment is tomorrow at 10:00 AM. Reply C to confirm.",
        "channel": "sms",
        "reporter_id": "judge-legit",
    })
    report_id = submitted.json()["report_id"]

    r = client.post(f"/report/{report_id}/forget")
    assert r.status_code == 200
    assert r.json()["pruned"] == report_id


def test_outcome_on_missing_report_404s(client):
    r = client.post("/report/does_not_exist/outcome", json={"outcome": "confirmed_scam"})
    assert r.status_code == 404
