"""API tests: cases list/detail, resolve, decision. Written before api.py."""

import json

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


def test_results_missing_is_404(client, tmp_path, monkeypatch):
    monkeypatch.setattr(api, "RESULTS_PATH", tmp_path / "results.json")
    assert client.get("/api/results").status_code == 404


def test_results_present(client, tmp_path, monkeypatch):
    payload = {"split": "dev", "runs": 1, "num_cases": 1,
               "metrics": {"side_accuracy": {"values": [1.0], "min": 1.0, "max": 1.0}},
               "failures": []}
    path = tmp_path / "results.json"
    path.write_text(json.dumps(payload))
    monkeypatch.setattr(api, "RESULTS_PATH", path)
    r = client.get("/api/results")
    assert r.status_code == 200
    assert r.json()["metrics"]["side_accuracy"]["values"] == [1.0]


def test_baseline_missing_is_404(client, tmp_path, monkeypatch):
    monkeypatch.setattr(api, "BASELINE_PATH", tmp_path / "baseline_results.json")
    assert client.get("/api/baseline").status_code == 404


def test_audit_lists_runs(client):
    assert client.get("/api/audit").json() == {"runs": []}
    client.post("/api/resolve/c-900")
    rows = client.get("/api/audit").json()["runs"]
    assert [r["case_id"] for r in rows] == ["c-900"]


def _fixture_case(name="c-900"):
    return json.loads((FIXTURES / "api_cases" / f"{name}.json").read_text())


def test_analyse_pasted_case(client):
    r = client.post("/api/analyse", json=_fixture_case())
    assert r.status_code == 200
    body = r.json()
    assert body["case_id"] == "c-900"
    assert body["calc"]["refund_kes"] == 970
    assert body["escalate"] is True


def test_analyse_invalid_body_422(client):
    assert client.post("/api/analyse", json={"case_id": "x"}).status_code == 422


def test_decision_on_pasted_case(client):
    raw = _fixture_case()
    raw["case_id"] = "pasted-1"
    assert client.post("/api/analyse", json=raw).status_code == 200
    r = client.post("/api/cases/pasted-1/decision",
                    json={"decision": "approve", "note": "ok"})
    assert r.status_code == 200
    assert r.json()["decision"] == "approve"


def test_decision_unknown_case_404(client):
    r = client.post("/api/cases/nope/decision",
                    json={"decision": "approve", "note": ""})
    assert r.status_code == 404


def test_generate_complaint_fake(client):
    r = client.post("/api/generate-complaint", json={
        "scenario": "fault", "fault_code": "GroundFailure",
        "language": "sw", "paid_kes": 1000})
    assert r.status_code == 200
    assert r.json() == {
        "text": "Chaji ilisimama na hitilafu kabla gari haijajaa."}


def test_generate_complaint_needs_fault_code(client):
    r = client.post("/api/generate-complaint",
                    json={"scenario": "fault", "language": "en"})
    assert r.status_code == 422


def test_generate_complaint_meta(client, monkeypatch):
    from unittest.mock import patch

    from resolver.model import MetaClient

    monkeypatch.setenv("RESOLVER_CLIENT", "meta")
    monkeypatch.setenv("META_API_KEY", "test-key")
    with patch.object(MetaClient, "complete",
                      return_value="  umeme umekatika  ") as complete:
        r = client.post("/api/generate-complaint", json={
            "scenario": "never", "language": "sw", "paid_kes": 500})
    assert r.status_code == 200
    assert complete.call_count == 1
    assert r.json() == {"text": "umeme umekatika"}
    user_arg = complete.call_args[0][1]
    assert "never started" in user_arg and "sw" in user_arg


def test_generate_complaint_fake_french(client):
    r = client.post("/api/generate-complaint", json={
        "scenario": "never", "language": "fr", "paid_kes": 500})
    assert r.status_code == 200
    assert r.json() == {"text": "J'ai payé mais le chargeur n'a jamais démarré."}


def test_generate_complaint_dropped_language_422(client):
    r = client.post("/api/generate-complaint", json={
        "scenario": "never", "language": "es", "paid_kes": 500})
    assert r.status_code == 422
