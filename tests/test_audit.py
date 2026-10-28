"""Session 5 tests: section 6.5, written before audit.py."""

import pytest

from resolver import audit


def _log(db, case_id="C-014", prompt="p", raw="r"):
    audit.log_case(db, case_id, "hash", prompt, raw, "ok", "{}")


def test_log_then_get_returns_same_fields(tmp_path):
    db = str(tmp_path / "a.db")
    audit.init_db(db)
    _log(db)
    row = audit.get_case(db, "C-014")
    assert row["case_id"] == "C-014"
    assert row["input_hash"] == "hash"
    assert row["prompt"] == "p"
    assert row["raw_output"] == "r"
    assert row["validation"] == "ok"
    assert row["result_json"] == "{}"
    assert row["created_at"]
    assert row["decision"] is None


def test_get_returns_latest_of_two_logs(tmp_path):
    db = str(tmp_path / "a.db")
    _log(db, prompt="first")
    _log(db, prompt="second")
    assert audit.get_case(db, "C-014")["prompt"] == "second"


def test_record_decision_sets_fields(tmp_path):
    db = str(tmp_path / "a.db")
    _log(db)
    audit.record_decision(db, "C-014", "approve", "looks right")
    row = audit.get_case(db, "C-014")
    assert row["decision"] == "approve"
    assert row["note"] == "looks right"
    assert row["decided_at"]


def test_bad_decision_raises(tmp_path):
    db = str(tmp_path / "a.db")
    _log(db)
    with pytest.raises(ValueError):
        audit.record_decision(db, "C-014", "maybe", "x")


def test_get_unknown_case_returns_none(tmp_path):
    db = str(tmp_path / "a.db")
    audit.init_db(db)
    assert audit.get_case(db, "C-999") is None


def test_record_decision_on_unknown_case_raises(tmp_path):
    db = str(tmp_path / "a.db")
    audit.init_db(db)
    with pytest.raises(ValueError):
        audit.record_decision(db, "C-999", "approve", "x")


def test_list_cases_latest_first(tmp_path):
    db = str(tmp_path / "a.db")
    _log(db, case_id="C-001")
    _log(db, case_id="C-002")
    rows = audit.list_cases(db)
    assert [r["case_id"] for r in rows] == ["C-002", "C-001"]
