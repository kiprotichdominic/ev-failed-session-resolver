"""Pipeline: resolve_case() ties calc, retrieve, model, rules, and audit together."""

import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP

from resolver import audit, calc, codes
from resolver import model as model_mod
from resolver import retrieve, rules
from resolver.models import Case, Result

NO_VALUE = "to be confirmed"


def _fmt_energy(energy: float) -> str:
    rounded = Decimal(str(energy)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    text = format(rounded, "f").rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _fill(text: str, energy: str, owed: str, refund: str) -> str:
    return (text.replace("{{energy_kwh}}", energy)
                .replace("{{owed_kes}}", owed)
                .replace("{{refund_kes}}", refund))


def resolve_case(case: Case | dict, client: model_mod.ModelClient,
                 corpus: dict, audit_path: str | None = None) -> Result:
    """Resolve one case. corpus maps clause IDs to index entries for rules.

    Chunk retrieval reads retrieve.INDEX_PATH; tests point it at a fixture.
    """
    if isinstance(case, dict):
        case = Case.model_validate(case)
    try:
        energy, estimated = calc.energy_kwh(case.session_log)
        owed = calc.owed_kes(energy, case.tariff_kes_per_kwh)
        refund_kes, underpaid = calc.refund(case.payment.captured, owed)
        calc_dict: dict | None = {"energy_kwh": energy, "owed_kes": owed,
                                  "refund_kes": refund_kes, "estimated": estimated,
                                  "underpaid": underpaid}
    except ValueError:
        calc_dict = None
    is_open = calc.still_open(case.session_log)
    facts = {
        "still_open": is_open,
        "estimated": calc_dict["estimated"] if calc_dict else False,
        "underpaid": calc_dict["underpaid"] if calc_dict else False,
        "hazard_codes": codes.hazard_codes(case.session_log),
        "payment_status": case.payment.status,
        "payment_method": case.payment.method,
    }
    error_codes = [e.error_code for e in case.session_log if e.error_code]
    chunks = retrieve.chunks_for(error_codes, case.complaint.text)
    model_out, attempts = model_mod.run_model(client, case, facts, chunks)
    decision = rules.evaluate(model_out, case, calc_dict, corpus)
    if calc_dict is not None:
        energy_txt, owed_txt = _fmt_energy(calc_dict["energy_kwh"]), str(calc_dict["owed_kes"])
    else:
        energy_txt = owed_txt = NO_VALUE
    refund_txt = (str(decision.refund_draft["amount_kes"])
                  if decision.refund_draft else NO_VALUE)
    if model_out is not None:
        driver_message = model_out.driver_message.model_copy(update={
            "text": _fill(model_out.driver_message.text, energy_txt, owed_txt, refund_txt)})
        note = model_out.technician_note
        technician_note = _fill(note, energy_txt, owed_txt, refund_txt) if note else note
    else:
        driver_message = technician_note = None
    result = Result(
        case_id=case.case_id,
        side=model_out.side if model_out else None,
        cause=model_out.cause if model_out else None,
        evidence=model_out.evidence if model_out else [],
        clause_ids=model_out.clause_ids if model_out else [],
        confidence=model_out.confidence if model_out else None,
        driver_message=driver_message,
        technician_note=technician_note,
        calc=calc_dict,
        still_open=is_open,
        refund_draft=decision.refund_draft,
        escalate=decision.escalate,
        escalate_reasons=decision.reasons,
        verification={c: c in corpus for c in (model_out.clause_ids if model_out else [])},
        usage=getattr(client, "usage_total", None),
    )
    if audit_path is not None:
        input_hash = hashlib.sha256(case.model_dump_json().encode("utf-8")).hexdigest()
        audit.log_case(audit_path, case.case_id, input_hash,
                       attempts[0]["user_message"], attempts[-1]["raw_output"],
                       json.dumps(attempts), result.model_dump_json())
    return result
