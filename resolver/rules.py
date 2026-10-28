"""Escalation rules. Code-only; never calls the model."""

import re
from typing import Optional

from resolver import codes
from resolver.models import Case, ModelOutput, StrictModel

CONFIDENCE_MIN = 0.6

_LOG_REF = re.compile(r"^session_log\[(\d+)\]$")


class Decision(StrictModel):
    escalate: bool
    reasons: list[str]
    refund_draft: Optional[dict] = None
    technician_required: bool


def _log_ref_valid(ref: str, log_len: int) -> bool:
    match = _LOG_REF.match(ref)
    return match is not None and int(match.group(1)) < log_len


def evaluate(model_out: ModelOutput | None, case: Case,
             calc: dict | None, corpus_index: dict) -> Decision:
    """Evaluate the escalation rules in section 6.4 order.

    calc is None (no StartTransaction) or a dict with energy_kwh,
    owed_kes, refund_kes, estimated and underpaid. corpus_index is a
    mapping whose keys are known clause IDs.
    """
    reasons: list[str] = []
    if model_out is None:
        reasons.append("model failure")
    else:
        bad_clause = any(c not in corpus_index for c in model_out.clause_ids)
        bad_evidence = any(
            (e.source == "log" and not _log_ref_valid(e.ref, len(case.session_log)))
            or (e.source == "reference" and e.ref not in corpus_index)
            for e in model_out.evidence
        )
        if bad_clause or bad_evidence:
            reasons.append("unverified citation")
        if model_out.confidence < CONFIDENCE_MIN:
            reasons.append("low confidence")
        if model_out.side == "unknown":
            reasons.append("inconclusive evidence")
    if calc is None or case.payment.status not in ("held", "captured"):
        reasons.append("records disagree")
    if calc is not None and (calc["underpaid"] or calc["refund_kes"] > case.payment.held):
        reasons.append("amount anomaly")
    technician_required = bool(codes.hazard_codes(case.session_log))
    note = model_out.technician_note if model_out is not None else None
    if technician_required and not note:
        reasons.append("missing technician note")
    draft = None
    if (calc is not None and calc["refund_kes"] > 0
            and "records disagree" not in reasons
            and "amount anomaly" not in reasons):
        draft = {"amount_kes": calc["refund_kes"], "requires_approval": True}
    return Decision(escalate=bool(reasons), reasons=reasons,
                    refund_draft=draft, technician_required=technician_required)
