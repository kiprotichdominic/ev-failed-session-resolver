"""Evaluation runner. Reads eval/cases/ and eval/labels.json; writes eval/results.json.

Usage: python eval/run_eval.py --split dev|heldout --runs 3 --client fake|meta
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from resolver.model import FakeModelClient, MetaClient  # noqa: E402
from resolver.models import Case, Result  # noqa: E402
from resolver.pipeline import resolve_case  # noqa: E402

GENERIC_REPLY = json.dumps({
    "side": "unknown",
    "cause": "The fake client cannot diagnose this case.",
    "evidence": [],
    "clause_ids": [],
    "confidence": 0.4,
    "driver_message": {"language": "en", "text": "We are reviewing your case."},
    "technician_note": None,
})

METRICS = ("side_accuracy", "clause_match", "citation_pass_rate",
           "escalation_precision", "escalation_recall",
           "high_confidence_wrong", "refund_correct")


def load_split(cases_dir: Path, labels_path: Path, split: str):
    if not labels_path.exists():
        raise SystemExit(f"labels file not found: {labels_path}. "
                         "The human writes eval/labels.json by hand.")
    labels = {cid: lab for cid, lab in json.loads(labels_path.read_text()).items()
              if lab["split"] == split}
    cases = {}
    for cid in labels:
        path = cases_dir / f"{cid}.json"
        if not path.exists():
            raise SystemExit(f"case file missing for {cid}: {path}")
        cases[cid] = Case.model_validate(json.loads(path.read_text()))
    return cases, labels


def load_corpus(index_path: Path) -> dict:
    if not index_path.exists():
        return {}
    return json.loads(index_path.read_text())


def score_run(results: dict[str, Result], labels: dict):
    n = len(labels)
    side_ok = clause_ok = cite_ok = refund_ok = 0
    tp = pred_pos = act_pos = 0
    hcw = 0
    failures = []
    for cid, lab in labels.items():
        r = results[cid]
        good_side = r.side == lab["side"]
        good_clause = set(r.clause_ids) == set(lab["clause_ids"])
        good_esc = r.escalate == lab["escalate"]
        draft_amt = r.refund_draft.amount_kes if r.refund_draft else None
        good_refund = draft_amt == lab["refund_kes"]
        side_ok += good_side
        clause_ok += good_clause
        cite_ok += "unverified citation" not in r.escalate_reasons
        refund_ok += good_refund
        tp += r.escalate and lab["escalate"]
        pred_pos += r.escalate
        act_pos += lab["escalate"]
        hcw += (r.confidence is not None and r.confidence >= 0.8
                and not good_side)
        if not good_side:
            failures.append({"case_id": cid, "field": "side",
                             "expected": lab["side"], "got": r.side})
        if not good_clause:
            failures.append({"case_id": cid, "field": "clause_ids",
                             "expected": lab["clause_ids"], "got": r.clause_ids})
        if not good_esc:
            failures.append({"case_id": cid, "field": "escalate",
                             "expected": lab["escalate"], "got": r.escalate})
        if not good_refund:
            failures.append({"case_id": cid, "field": "refund_kes",
                             "expected": lab["refund_kes"], "got": draft_amt})
    metrics = {
        "side_accuracy": side_ok / n if n else None,
        "clause_match": clause_ok / n if n else None,
        "citation_pass_rate": cite_ok / n if n else None,
        "escalation_precision": tp / pred_pos if pred_pos else None,
        "escalation_recall": tp / act_pos if act_pos else None,
        "high_confidence_wrong": hcw,
        "refund_correct": refund_ok / n if n else None,
    }
    return metrics, failures


def summarize(per_run: list[dict]) -> dict:
    summary = {}
    for name in METRICS:
        values = [run[name] for run in per_run]
        present = [v for v in values if v is not None]
        summary[name] = {"values": values,
                         "min": min(present) if present else None,
                         "max": max(present) if present else None}
    return summary


def evaluate(cases, labels, make_client, corpus, runs):
    """Run the split `runs` times. Failures reported are from the last run."""
    per_run, failures = [], []
    for _ in range(runs):
        client = make_client()
        results = {cid: resolve_case(case, client, corpus)
                   for cid, case in cases.items()}
        metrics, failures = score_run(results, labels)
        per_run.append(metrics)
    return {"metrics": summarize(per_run), "failures": failures}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the dev/heldout evaluation.")
    parser.add_argument("--split", required=True, choices=["dev", "heldout"])
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--client", required=True, choices=["fake", "meta"])
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent
    cases, labels = load_split(root / "cases", root / "labels.json", args.split)
    corpus = load_corpus(root.parent / "corpus" / "index.json")
    if args.client == "fake":
        replies = [GENERIC_REPLY] * max(len(cases), 1)
        make_client = lambda: FakeModelClient(list(replies))  # noqa: E731
    else:
        make_client = MetaClient
    out = evaluate(cases, labels, make_client, corpus, args.runs)
    payload = {"split": args.split, "runs": args.runs,
               "num_cases": len(cases), "metrics": out["metrics"],
               "failures": out["failures"]}
    (root / "results.json").write_text(json.dumps(payload, indent=2))
    print(f"wrote {root / 'results.json'} "
          f"({len(cases)} cases, {args.runs} runs)")


if __name__ == "__main__":
    main()
