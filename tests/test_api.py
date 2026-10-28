"""API tests: cases list/detail, resolve, decision. Written before api.py."""

import pytest
from fastapi.testclient import TestClient

import api

FIXTURES = api.ROOT / "tests" / "fixtures"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "CASES_DIR", FIXTURES / "api_cases")
    monkeypatch.setattr(api, "CORPUS_PATH", FIXTURES / "index.json")
    monkeypatch.setattr(api, "AUDIT_DB", str(tmp_path / "audit.db"))
    monkeypatch.setenv("RESOLVER_CLIENT", "fake")
    return TestClient(api.app)


def test_list_cases(client):
    r = client.get("/api/cases")
    assert r.status_code == 200
    ids = [c["case_id"] for c in r.json()["cases"]]
    assert "c-900" in ids


def test_get_case(client):
    r = client.get("/api/cases/c-900")
    assert r.status_code == 200
    assert r.json()["complaint"]["text"] == "charger stopped early"


def test_get_missing_case_404(client):
    assert client.get("/api/cases/nope").status_code == 404


def test_resolve_case(client):
    r = client.post("/api/resolve/c-900")
    assert r.status_code == 200
    body = r.json()
    assert body["calc"]["refund_kes"] == 970
    assert body["refund_draft"] == {"amount_kes": 970, "requires_approval": True}
    assert body["escalate"] is True


def test_resolve_invalid_case_422(client):
    assert client.post("/api/resolve/c-bad").status_code == 422


def test_decision_flow(client):
    assert client.post("/api/resolve/c-900").status_code == 200
    r = client.post("/api/cases/c-900/decision",
                    json={"decision": "approve", "note": "ok"})
    assert r.status_code == 200
    assert r.json()["decision"] == "approve"


def test_bad_decision_rejected(client):
    client.post("/api/resolve/c-900")
    r = client.post("/api/cases/c-900/decision",
                    json={"decision": "maybe", "note": ""})
    assert r.status_code == 422


def test_status_reports_mode(client):
    r = client.get("/api/status")
    assert r.status_code == 200
    assert r.json()["mode"] == "fake"


def test_meta_mode_uses_live_client(client, monkeypatch):
    import json as jsonlib
    from unittest.mock import patch

    from resolver.model import MetaClient

    monkeypatch.setenv("RESOLVER_CLIENT", "meta")
    monkeypatch.setenv("META_API_KEY", "test-key")
    reply = jsonlib.dumps({
        "side": "charger",
        "cause": "A ground failure faulted the connector.",
        "evidence": [{"source": "log", "ref": "session_log[0]",
                      "note": "start"}],
        "clause_ids": ["OCPP16-ERR-GroundFailure"],
        "confidence": 0.9,
        "driver_message": {"language": "en",
                           "text": "Refund {{refund_kes}} KES."},
        "technician_note": None,
    })
    with patch.object(MetaClient, "complete", return_value=reply) as complete:
        r = client.post("/api/resolve/c-900")
    assert r.status_code == 200
    assert complete.call_count == 1
    assert r.json()["side"] == "charger"


def test_meta_mode_without_key_is_500(client, monkeypatch):
    monkeypatch.setenv("RESOLVER_CLIENT", "meta")
    monkeypatch.delenv("META_API_KEY", raising=False)
    r = client.post("/api/resolve/c-900")
    assert r.status_code == 500
