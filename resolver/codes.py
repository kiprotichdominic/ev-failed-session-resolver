"""Error-code table loader for corpus/error_codes.json."""

import json
from pathlib import Path

from resolver.models import LogEntry, StrictModel

ERROR_CODES_PATH = Path(__file__).resolve().parent.parent / "corpus" / "error_codes.json"


class CodeInfo(StrictModel):
    side_hint: str
    clause_id: str
    hazard: bool


def _load_table() -> dict:
    with open(ERROR_CODES_PATH, encoding="utf-8") as f:
        return json.load(f)


def lookup(code: str | None) -> CodeInfo | None:
    """Return the CodeInfo for an error code, or None when unknown."""
    if code is None or code.startswith("_"):
        return None
    table = _load_table()
    raw = table.get(code)
    if raw is None:
        return None
    return CodeInfo.model_validate(raw)


def hazard_codes(log: list[LogEntry]) -> list[str]:
    """Known hazard-flagged error codes in the log, deduped in order."""
    found: list[str] = []
    for entry in log:
        code = entry.error_code
        if code is None or code in found:
            continue
        info = lookup(code)
        if info is not None and info.hazard:
            found.append(code)
    return found
