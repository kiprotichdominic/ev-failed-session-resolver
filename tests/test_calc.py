"""Session 1 tests: section 6.1 expected values, written before calc.py.

Expected values are taken verbatim from the brief and must not change.
Extra tests pin down rules stated in the brief (latest-ts MeterValues,
ROUND_HALF_UP) and the section 4 contracts (unknown fields rejected).
"""

import pytest

from resolver.calc import energy_kwh, owed_kes, refund, still_open, offline_minutes
from resolver.models import Case, LogEntry


def entry(ts, type, **kwargs):
    return LogEntry(ts=ts, type=type, connector_id=1, **kwargs)


# --- energy_kwh ---

def test_energy_start_0_stop_1200():
    log = [
        entry("2026-10-21T18:31:02+03:00", "StartTransaction", meter_wh=0),
        entry("2026-10-21T18:33:41+03:00", "StopTransaction", meter_wh=1200),
    ]
    assert energy_kwh(log) == (pytest.approx(1.2), False)


def test_energy_start_500_stop_8000():
    log = [
        entry("2026-10-21T18:31:02+03:00", "StartTransaction", meter_wh=500),
        entry("2026-10-21T18:33:41+03:00", "StopTransaction", meter_wh=8000),
    ]
    assert energy_kwh(log) == (pytest.approx(7.5), False)


def test_energy_no_stop_uses_latest_meter_values():
    log = [
        entry("2026-10-21T18:31:02+03:00", "StartTransaction", meter_wh=0),
        entry("2026-10-21T18:32:00+03:00", "MeterValues", meter_wh=800),
        entry("2026-10-21T18:33:00+03:00", "MeterValues", meter_wh=3000),
    ]
    assert energy_kwh(log) == (pytest.approx(3.0), True)


def test_energy_meter_values_uses_latest_ts_not_position():
    log = [
        entry("2026-10-21T18:31:02+03:00", "StartTransaction", meter_wh=0),
        entry("2026-10-21T18:33:00+03:00", "MeterValues", meter_wh=3000),
        entry("2026-10-21T18:32:00+03:00", "MeterValues", meter_wh=800),
    ]
    assert energy_kwh(log) == (pytest.approx(3.0), True)


def test_energy_no_start_raises():
    with pytest.raises(ValueError):
        energy_kwh([entry("2026-10-21T18:33:41+03:00", "StopTransaction", meter_wh=1200)])
    with pytest.raises(ValueError):
        energy_kwh([])


def test_energy_no_stop_and_no_meters_raises():
    log = [entry("2026-10-21T18:31:02+03:00", "StartTransaction", meter_wh=0)]
    with pytest.raises(ValueError):
        energy_kwh(log)


# --- owed_kes ---

@pytest.mark.parametrize(
    "energy, tariff, expected",
    [(1.2, 25, 30), (7.5, 25, 188), (0, 25, 0), (3.0, 25, 75)],
)
def test_owed(energy, tariff, expected):
    assert owed_kes(energy, tariff) == expected


def test_owed_rounds_half_up():
    # 0.1 * 25 = 2.5 -> 3 under ROUND_HALF_UP (banker's rounding would give 2).
    assert owed_kes(0.1, 25) == 3


# --- refund ---

@pytest.mark.parametrize(
    "captured, owed, expected",
    [(1000, 30, (970, False)), (1000, 188, (812, False)),
     (50, 75, (0, True)), (1000, 0, (1000, False))],
)
def test_refund(captured, owed, expected):
    assert refund(captured, owed) == expected


# --- still_open ---

def _faulted_log():
    return [
        entry("2026-10-21T18:31:02+03:00", "StartTransaction", meter_wh=0),
        entry("2026-10-21T18:33:10+03:00", "StatusNotification",
              status="Faulted", error_code="GroundFailure"),
        entry("2026-10-21T18:33:41+03:00", "StopTransaction",
              meter_wh=1200, reason="EmergencyStop"),
    ]


def test_still_open_fault_with_no_recovery():
    assert still_open(_faulted_log()) is True


def test_still_open_recovered_session():
    log = _faulted_log() + [
        entry("2026-10-21T19:00:00+03:00", "StartTransaction", meter_wh=1200),
        entry("2026-10-21T19:20:00+03:00", "StopTransaction", meter_wh=9000),
    ]
    assert still_open(log) is False


def test_still_open_zero_energy_restart():
    log = _faulted_log() + [
        entry("2026-10-21T19:00:00+03:00", "StartTransaction", meter_wh=9000),
        entry("2026-10-21T19:20:00+03:00", "StopTransaction", meter_wh=9000),
    ]
    assert still_open(log) is True


def test_still_open_no_fault():
    log = [
        entry("2026-10-21T18:31:02+03:00", "StartTransaction", meter_wh=0),
        entry("2026-10-21T18:33:41+03:00", "StopTransaction", meter_wh=1200),
    ]
    assert still_open(log) is False


# --- offline_minutes ---

def test_offline_minutes():
    log = [
        entry("2026-10-21T10:00:00+03:00", "Heartbeat"),
        entry("2026-10-21T10:01:00+03:00", "Heartbeat"),
        entry("2026-10-21T10:11:00+03:00", "Heartbeat"),
    ]
    assert offline_minutes(log, 60) == 10


# --- section 4 input contract ---

def test_case_c014_parses():
    case = Case.model_validate({
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
    })
    assert case.case_id == "C-014"
    assert len(case.session_log) == 3


def test_unknown_fields_rejected():
    with pytest.raises(Exception):
        LogEntry.model_validate(
            {"ts": "2026-10-21T10:00:00+03:00", "type": "Heartbeat",
             "connector_id": 1, "bogus": 1})
    with pytest.raises(Exception):
        Case.model_validate({
            "case_id": "C-014",
            "complaint": {"text": "x", "received_at": "2026-10-21T18:42:00+03:00"},
            "session_log": [], "payment": {"method": "m", "currency": "KES",
                                           "held": 0, "captured": 0, "status": "held"},
            "tariff_kes_per_kwh": 25, "bogus": 1})
