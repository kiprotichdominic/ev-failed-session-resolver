"""Session 2 tests: section 6.3 expected values, written before retrieve.py.

All tests run against the small fixture index in tests/fixtures/,
never the real corpus.
"""

from pathlib import Path

import pytest

from resolver import retrieve

FIXTURE_INDEX = Path(__file__).parent / "fixtures" / "index.json"


@pytest.fixture(autouse=True)
def fixture_index(monkeypatch):
    monkeypatch.setattr(retrieve, "INDEX_PATH", FIXTURE_INDEX)


def clause_ids(chunks):
    return [c.clause_id for c in chunks]


def test_error_code_chunk_comes_first():
    chunks = retrieve.chunks_for(["GroundFailure"], "refund please")
    assert chunks
    assert chunks[0].clause_id == "OCPP16-ERR-GroundFailure"


def test_k_limits_total_chunks():
    chunks = retrieve.chunks_for(["GroundFailure"], "refund please", k=1)
    assert clause_ids(chunks) == ["OCPP16-ERR-GroundFailure"]


def test_unknown_code_and_empty_complaint_returns_empty():
    assert retrieve.chunks_for(["Nonsense"], "") == []


def test_keyword_refund_matches_policy_chunk():
    chunks = retrieve.chunks_for(["Nonsense"], "I want a refund")
    assert clause_ids(chunks) == ["POL-REFUND-1"]


def test_keyword_ranking_by_match_count():
    chunks = retrieve.chunks_for([], "refund request charger")
    assert clause_ids(chunks) == ["POL-REFUND-1", "OCPP16-ERR-GroundFailure"]


def test_keyword_tie_broken_by_clause_id():
    chunks = retrieve.chunks_for([], "refund charger")
    assert clause_ids(chunks) == ["OCPP16-ERR-GroundFailure", "POL-REFUND-1"]


def test_error_code_chunk_deduplicated():
    chunks = retrieve.chunks_for(["GroundFailure"], "charger problem")
    assert clause_ids(chunks) == ["OCPP16-ERR-GroundFailure"]
