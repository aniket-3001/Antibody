"""The error contract: every failure leaves the API in one stable JSON shape
({error, message, request_id, path}) and every response echoes its correlation
id. Exercises api/core (typed exceptions + centralized handlers + request-id
middleware)."""
from __future__ import annotations

from api.core.logging import REQUEST_ID_HEADER


def test_empty_report_is_typed_400(client):
    r = client.post("/report", json={"text": "   "})
    assert r.status_code == 400
    body = r.json()
    assert body["error"] == "empty_report"
    assert body["path"] == "/report"
    assert body["request_id"]  # non-empty correlation id


def test_outcome_on_missing_report_is_typed_404(client):
    r = client.post("/report/nope/outcome", json={"outcome": "confirmed_scam"})
    assert r.status_code == 404
    assert r.json()["error"] == "report_not_found"


def test_validation_error_has_stable_envelope(client):
    # Missing required `text` field -> pydantic validation -> 422 envelope.
    r = client.post("/report", json={"channel": "sms"})
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "validation_error"
    assert "text" in body["message"]


def test_unknown_route_is_envelope_404(client):
    r = client.get("/does-not-exist")
    assert r.status_code == 404
    assert r.json()["error"] == "http_error"


def test_response_echoes_request_id_header(client):
    supplied = "trace123"
    r = client.get("/health", headers={REQUEST_ID_HEADER: supplied})
    assert r.headers.get(REQUEST_ID_HEADER) == supplied


def test_response_mints_request_id_when_absent(client):
    r = client.get("/health")
    assert r.headers.get(REQUEST_ID_HEADER)  # server-generated
