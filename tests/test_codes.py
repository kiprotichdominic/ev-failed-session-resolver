"""Session 2 tests: section 6.2 expected values, written before codes.py."""

from resolver.codes import hazard_codes, lookup
from resolver.models import LogEntry


def test_lookup_ground_failure():
    info = lookup("GroundFailure")
    assert info is not None
    assert info.side_hint == "charger"
    assert info.clause_id == "OCPP16-ERR-GroundFailure"
    assert info.hazard is True


def test_lookup_connector_lock_failure_not_hazard():
    info = lookup("ConnectorLockFailure")
    assert info is not None
    assert info.side_hint == "charger"
    assert info.hazard is False


def test_lookup_unknown_returns_none():
    assert lookup(None) is None
    assert lookup("Nonsense") is None
    assert lookup("_note") is None


def test_hazard_codes_c014():
    log = [
        LogEntry.model_validate({"ts": "2026-10-21T18:31:02+03:00",
                                 "type": "StartTransaction",
                                 "connector_id": 1, "meter_wh": 0}),
        LogEntry.model_validate({"ts": "2026-10-21T18:33:10+03:00",
                                 "type": "StatusNotification",
                                 "connector_id": 1, "status": "Faulted",
                                 "error_code": "GroundFailure"}),
        LogEntry.model_validate({"ts": "2026-10-21T18:33:41+03:00",
                                 "type": "StopTransaction",
                                 "connector_id": 1, "meter_wh": 1200,
                                 "reason": "EmergencyStop"}),
    ]
    assert hazard_codes(log) == ["GroundFailure"]


def test_hazard_codes_skips_non_hazard_unknown_and_dupes():
    log = [
        LogEntry.model_validate({"ts": "2026-10-21T18:31:02+03:00",
                                 "type": "StatusNotification",
                                 "connector_id": 1, "status": "Faulted",
                                 "error_code": "GroundFailure"}),
        LogEntry.model_validate({"ts": "2026-10-21T18:32:00+03:00",
                                 "type": "StatusNotification",
                                 "connector_id": 1, "status": "Faulted",
                                 "error_code": "ConnectorLockFailure"}),
        LogEntry.model_validate({"ts": "2026-10-21T18:33:00+03:00",
                                 "type": "StatusNotification",
                                 "connector_id": 1, "status": "Faulted",
                                 "error_code": "Nonsense"}),
        LogEntry.model_validate({"ts": "2026-10-21T18:34:00+03:00",
                                 "type": "StatusNotification",
                                 "connector_id": 1, "status": "Faulted",
                                 "error_code": "GroundFailure"}),
    ]
    assert hazard_codes(log) == ["GroundFailure"]
