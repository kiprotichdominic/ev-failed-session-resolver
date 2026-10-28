"""Code-only baseline resolver. Writes eval/baseline_results.json."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.run_eval import load_corpus, load_split, score_run, summarize  # noqa: E402
from resolver import codes  # noqa: E402
from resolver.model import FakeModelClient  # noqa: E402
from resolver.models import Case, ModelOutput  # noqa: E402
from resolver.pipeline import resolve_case  # noqa: E402


def build_model_output(case: Case) -> ModelOutput:
    """Baseline side/clause/confidence rules from section 7."""
    payment_ok = case.payment.status in ("held", "captured")
    match = None
    for i, entry in enumerate(case.session_log):
        if entry.error_code:
            info = codes.lookup(entry.error_code)
            if info is not None:
                match = (i, info)
                break
    if not payment_ok:
        side = "payment"
    elif match is not None:
        side = match[1].side_hint
    else:
        side = "unknown"
    clause_ids = [match[1].clause_id] if (payment_ok and match is not None) else []
    evidence = ([{"source": "log", "ref": f"session_log[{match[0]}]",
                  "note": case.session_log[match[0]].error_code}]
                if match is not None else [])
    hazards = codes.hazard_codes(case.session_log)
    return ModelOutput.model_validate({
        "side": side,
        "cause": "Code-only baseline diagnosis.",
        "evidence": evidence,
        "clause_ids": clause_ids,
        "confidence": 0.7 if match is not None else 0.3,
        "driver_message": {"language": "en",
                           "text": "Our team will review your case."},
        "technician_note": "Baseline: technician review required." if hazards else None,
    })


def resolve_baseline(case: Case, corpus: dict):
    """Baseline result via the same calc.py and rules.py logic as resolve_case."""
    reply = build_model_output(case).model_dump_json()
    return resolve_case(case, FakeModelClient([reply]), corpus)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the code-only baseline.")
    parser.add_argument("--split", required=True, choices=["dev", "heldout"])
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent
    cases, labels = load_split(root / "cases", root / "labels.json", args.split)
    corpus = load_corpus(root.parent / "corpus" / "index.json")
    per_run, failures = [], []
    for _ in range(args.runs):
        results = {cid: resolve_baseline(case, corpus)
                   for cid, case in cases.items()}
        metrics, failures = score_run(results, labels)
        per_run.append(metrics)
    payload = {"split": args.split, "runs": args.runs,
               "num_cases": len(cases), "metrics": summarize(per_run),
               "failures": failures}
    (root / "baseline_results.json").write_text(json.dumps(payload, indent=2))
    print(f"wrote {root / 'baseline_results.json'} "
          f"({len(cases)} cases, {args.runs} runs)")


if __name__ == "__main__":
    main()
