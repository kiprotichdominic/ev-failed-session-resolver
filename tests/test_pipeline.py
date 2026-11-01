"""Session 6 tests: section 6.7, written before pipeline.py."""

import json
import sqlite3
from pathlib import Path

import pytest

from resolver import retrieve
from resolver.audit import get_case
from resolver.model import FakeModelClient
from resolver.pipeline import resolve_case

FIXTURE_INDEX = Path(__file__).parent / "fixtures" / "index.json"


@pytest.fixture(autouse=True)
def fixture_corpus(monkeypatch):
    monkeypatch.setattr(retrieve, "INDEX_PATH", FIXTURE_INDEX)
    return json.loads(FIXTURE_INDEX.read_text(encoding="utf-8"))


def _c014():
    return {
        "case_id": "C-014",
        "complaint": {"text": "nimelipa 1000 lakini hakuna power",
                      "received_at": "2026-10-21T18:42:00+03:00"},
        "session_log": [
            {"ts": "2026-10-21T18:31:02+03:00", "type": "StartTransaction",
             "connector_id": 1, "meter_wh": 0},
            {"ts": "2026-10-21T18:33:10+03:00", "type": "StatusNotification",
             "connector_id": 1, "status": "Faulted", "error_code": "GroundFailure"},
            {"ts": "2026-10-21T18:33:41+03:00", "type": "StopTransaction",
             "connector_id": 1, "meter_wh": 1200, "reason": "EmergencyStop"},
        ],
        "payment": {"method": "mobile_money", "currency": "KES",
                    "held": 1000, "captured": 1000, "status": "captured"},
        "tariff_kes_per_kwh": 25,
    }


def _c021():
    return {
        "case_id": "C-021",
        "complaint": {"text": "paid but no charge",
                      "received_at": "2026-10-22T09:00:00+03:00"},
        "session_log": [
            {"ts": "2026-10-22T08:00:00+03:00", "type": "Heartbeat",
             "connector_id": 1},
            {"ts": "2026-10-22T08:01:00+03:00", "type": "MeterValues",
             "connector_id": 1, "meter_wh": 0},
        ],
        "payment": {"method": "mobile_money", "currency": "KES",
                    "held": 1000, "captured": 0, "status": "pending"},
        "tariff_kes_per_kwh": 25,
    }


def _reply(**overrides):
    data = {
        "side": "charger",
        "cause": "A ground failure faulted the connector.",
        "evidence": [{"source": "log", "ref": "session_log[1]",
                      "note": "Faulted status"}],
        "clause_ids": ["OCPP16-ERR-GroundFailure"],
        "confidence": 0.86,
        "driver_message": {"language": "en",
                           "text": "Delivered {{energy_kwh}} kWh, owed "
                                   "{{owed_kes}} KES, refund {{refund_kes}} KES."},
        "technician_note": "Isolate connector 1.",
    }
    data.update(overrides)
    return json.dumps(data)


def test_c014_full_resolution(fixture_corpus):
    result = resolve_case(_c014(), FakeModelClient([_reply()]), fixture_corpus)
    assert result.calc == {"energy_kwh": 1.2, "owed_kes": 30,
                           "refund_kes": 970, "estimated": False,
                           "underpaid": False}
    assert "1.2" in result.driver_message.text
    assert "970" in result.driver_message.text
    assert "{{" not in result.driver_message.text
    assert result.refund_draft.amount_kes == 970
    assert result.refund_draft.requires_approval is True
    assert result.escalate is False
    assert result.verification == {"OCPP16-ERR-GroundFailure": True}


def test_c021_no_start_pending_payment(fixture_corpus):
    reply = _reply(side="charger", confidence=0.8, clause_ids=[],
                   evidence=[{"source": "complaint", "ref": "complaint",
                              "note": "paid but no charge"}],
                   technician_note=None)
    result = resolve_case(_c021(), FakeModelClient([reply]), fixture_corpus)
    assert result.escalate is True
    assert result.escalate_reasons == ["records disagree"]
    assert result.refund_draft is None
    assert result.calc is None
    assert "to be confirmed" in result.driver_message.text


def test_fake_clause_escalates(fixture_corpus):
    result = resolve_case(_c014(), FakeModelClient([_reply(clause_ids=["FAKE-1"])]),
                          fixture_corpus)
    assert result.escalate is True
    assert "unverified citation" in result.escalate_reasons


def test_audit_row_written(fixture_corpus, tmp_path):
    db = str(tmp_path / "a.db")
    raw = _reply()
    resolve_case(_c014(), FakeModelClient([raw]), fixture_corpus, audit_path=db)
    count = sqlite3.connect(db).execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    assert count == 1
    assert get_case(db, "C-014")["raw_output"] == raw


def test_resolve_includes_client_usage(fixture_corpus):
    from resolver.models import Usage

    client = FakeModelClient([_reply()])
    client.usage_total = Usage(prompt_tokens=10, completion_tokens=5,
                               total_tokens=15)
    result = resolve_case(_c014(), client, fixture_corpus)
    assert result.usage is not None
    assert result.usage.total_tokens == 15


def test_resolve_usage_none_without_model_call(fixture_corpus):
    result = resolve_case(_c014(), FakeModelClient([_reply()]), fixture_corpus)
    assert result.usage is None
