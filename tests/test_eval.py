"""Session 8 tests: section 7 fixture metrics, written before the harness."""

import json
from pathlib import Path

import pytest

from eval.baseline import build_model_output, resolve_baseline
from eval.run_eval import evaluate, load_split
from resolver.model import FakeModelClient
from resolver.models import Case

FIXTURES = Path(__file__).parent / "fixtures"
CORPUS = {"T-CLAUSE": {"title": "t", "text": "x", "source": "s"}}


def _load_case(name):
    return Case.model_validate(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


def _label(side):
    return {"split": "dev", "side": side, "clause_ids": ["T-CLAUSE"],
            "escalate": False, "refund_kes": 970}


def _reply(side, confidence=0.86):
    return json.dumps({
        "side": side,
        "cause": "Test reply.",
        "evidence": [{"source": "log", "ref": "session_log[0]", "note": "start"}],
        "clause_ids": ["T-CLAUSE"],
        "confidence": confidence,
        "driver_message": {"language": "en", "text": "Refund {{refund_kes}} KES."},
        "technician_note": None,
    })


def test_side_accuracy_two_thirds():
    cases = {f"eval_case_{i}": _load_case(f"eval_case_{i}.json") for i in (1, 2, 3)}
    labels = {"eval_case_1": _label("charger"),
              "eval_case_2": _label("network"),
              "eval_case_3": _label("network")}
    replies = [_reply("charger"), _reply("charger"), _reply("network")]
    make_client = lambda: FakeModelClient(list(replies))
    out = evaluate(cases, labels, make_client, CORPUS, runs=2)
    assert out["metrics"]["side_accuracy"]["values"] == pytest.approx([2 / 3, 2 / 3])
    assert out["metrics"]["refund_correct"]["values"] == pytest.approx([1.0, 1.0])
    json.dumps(out)


def test_high_confidence_wrong_counted():
    cases = {"eval_case_4": _load_case("eval_case_4.json")}
    labels = {"eval_case_4": _label("network")}
    make_client = lambda: FakeModelClient([_reply("charger", confidence=0.9)])
    out = evaluate(cases, labels, make_client, CORPUS, runs=1)
    assert out["metrics"]["high_confidence_wrong"]["values"] == [1]


def test_missing_labels_exits_with_message(tmp_path):
    with pytest.raises(SystemExit) as exc:
        load_split(tmp_path, tmp_path / "labels.json", "dev")
    assert "labels.json" in str(exc.value)


def test_baseline_side_rules():
    raw = json.loads((FIXTURES / "eval_case_1.json").read_text(encoding="utf-8"))
    raw["payment"] = {"method": "mobile_money", "currency": "KES",
                      "held": 1000, "captured": 0, "status": "pending"}
    assert build_model_output(Case.model_validate(raw)).side == "payment"
    clean = _load_case("eval_case_1.json")
    out = build_model_output(clean)
    assert (out.side, out.confidence) == ("unknown", 0.3)
    assert resolve_baseline(clean, CORPUS).escalate is True
