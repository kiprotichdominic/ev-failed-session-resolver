"""Session 3 tests: one per rule in section 6.4, written before rules.py."""

from resolver.models import Case, ModelOutput
from resolver.rules import evaluate

INDEX = {"OCPP16-ERR-GroundFailure": {"title": "t", "text": "x", "source": "s"}}


def _case(**overrides):
    data = {
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
    data.update(overrides)
    return Case.model_validate(data)


def _model_out(**overrides):
    data = {
        "side": "charger",
        "cause": "A ground failure faulted the connector.",
        "evidence": [{"source": "log", "ref": "session_log[1]",
                      "note": "Faulted status"}],
        "clause_ids": ["OCPP16-ERR-GroundFailure"],
        "confidence": 0.86,
        "driver_message": {"language": "en",
                           "text": "Stopped after {{energy_kwh}} kWh."},
        "technician_note": "Isolate connector 1 and inspect for ground fault.",
    }
    data.update(overrides)
    return ModelOutput.model_validate(data)


def _calc(**overrides):
    data = {"energy_kwh": 1.2, "owed_kes": 30, "refund_kes": 970,
            "estimated": False, "underpaid": False}
    data.update(overrides)
    return data


def test_happy_path_no_escalation():
    d = evaluate(_model_out(), _case(), _calc(), INDEX)
    assert d.escalate is False
    assert d.reasons == []
    assert d.refund_draft == {"amount_kes": 970, "requires_approval": True}
    assert d.technician_required is True


def test_rule1_model_failure():
    d = evaluate(None, _case(), _calc(), INDEX)
    assert d.escalate is True
    assert d.reasons == ["model failure", "missing technician note"]
    assert d.technician_required is True
    assert d.refund_draft == {"amount_kes": 970, "requires_approval": True}


def test_rule2_unknown_clause_id():
    d = evaluate(_model_out(clause_ids=["FAKE-1"]), _case(), _calc(), INDEX)
    assert d.escalate is True
    assert d.reasons == ["unverified citation"]


def test_rule2_bad_log_evidence_ref():
    ev = [{"source": "log", "ref": "session_log[9]", "note": "x"}]
    d = evaluate(_model_out(evidence=ev), _case(), _calc(), INDEX)
    assert d.escalate is True
    assert d.reasons == ["unverified citation"]


def test_rule2_bad_reference_evidence_ref():
    ev = [{"source": "reference", "ref": "NOPE", "note": "x"}]
    d = evaluate(_model_out(evidence=ev), _case(), _calc(), INDEX)
    assert d.escalate is True
    assert d.reasons == ["unverified citation"]


def test_rule3_low_confidence_fires():
    d = evaluate(_model_out(confidence=0.59), _case(), _calc(), INDEX)
    assert d.escalate is True
    assert d.reasons == ["low confidence"]


def test_rule3_boundary_passes():
    d = evaluate(_model_out(confidence=0.6), _case(), _calc(), INDEX)
    assert d.escalate is False
    assert d.reasons == []


def test_rule4_unknown_side():
    d = evaluate(_model_out(side="unknown"), _case(), _calc(), INDEX)
    assert d.escalate is True
    assert d.reasons == ["inconclusive evidence"]


def test_rule5_pending_payment():
    payment = {"method": "mobile_money", "currency": "KES",
               "held": 1000, "captured": 0, "status": "pending"}
    d = evaluate(_model_out(), _case(payment=payment), _calc(), INDEX)
    assert d.escalate is True
    assert d.reasons == ["records disagree"]
    assert d.refund_draft is None


def test_rule5_no_start_transaction():
    log = [
        {"ts": "2026-10-21T10:00:00+03:00", "type": "Heartbeat",
         "connector_id": 1},
        {"ts": "2026-10-21T10:01:00+03:00", "type": "Heartbeat",
         "connector_id": 1},
    ]
    d = evaluate(_model_out(), _case(session_log=log), None, INDEX)
    assert d.escalate is True
    assert d.reasons == ["records disagree"]
    assert d.refund_draft is None


def test_rule6_underpaid():
    payment = {"method": "mobile_money", "currency": "KES",
               "held": 50, "captured": 50, "status": "captured"}
    calc = _calc(owed_kes=75, refund_kes=0, underpaid=True)
    d = evaluate(_model_out(), _case(payment=payment), calc, INDEX)
    assert d.escalate is True
    assert d.reasons == ["amount anomaly"]
    assert d.refund_draft is None


def test_rule6_refund_above_held():
    payment = {"method": "mobile_money", "currency": "KES",
               "held": 500, "captured": 1000, "status": "captured"}
    d = evaluate(_model_out(), _case(payment=payment), _calc(), INDEX)
    assert d.escalate is True
    assert d.reasons == ["amount anomaly"]
    assert d.refund_draft is None


def test_rule7_missing_technician_note():
    d = evaluate(_model_out(technician_note=None), _case(), _calc(), INDEX)
    assert d.escalate is True
    assert d.reasons == ["missing technician note"]
    assert d.technician_required is True
