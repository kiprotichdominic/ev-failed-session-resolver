"""SQLite audit log for cases and human decisions."""

import sqlite3
from datetime import datetime, timezone

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    prompt TEXT NOT NULL,
    raw_output TEXT,
    validation TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    decision TEXT,
    note TEXT,
    decided_at TEXT
)
"""


def _connect(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute(_SCHEMA)
    return con


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(path: str) -> None:
    con = _connect(path)
    con.commit()
    con.close()


def log_case(path: str, case_id: str, input_hash: str, prompt: str,
             raw_output: str | None, validation: str, result_json: str) -> None:
    con = _connect(path)
    con.execute(
        "INSERT INTO cases (case_id, input_hash, prompt, raw_output,"
        " validation, result_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (case_id, input_hash, prompt, raw_output, validation,
         result_json, _now()),
    )
    con.commit()
    con.close()


def record_decision(path: str, case_id: str, decision: str, note: str) -> None:
    if decision not in ("approve", "reject"):
        raise ValueError(f"decision must be approve or reject, got {decision!r}")
    con = _connect(path)
    row = con.execute(
        "SELECT id FROM cases WHERE case_id = ? ORDER BY id DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    if row is None:
        con.close()
        raise ValueError(f"unknown case: {case_id}")
    con.execute(
        "UPDATE cases SET decision = ?, note = ?, decided_at = ? WHERE id = ?",
        (decision, note, _now(), row["id"]),
    )
    con.commit()
    con.close()


def get_case(path: str, case_id: str) -> dict | None:
    con = _connect(path)
    row = con.execute(
        "SELECT * FROM cases WHERE case_id = ? ORDER BY id DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    con.close()
    return dict(row) if row is not None else None


def list_cases(path: str) -> list[dict]:
    """All runs, latest first. Needed by the Audit page in web/."""
    con = _connect(path)
    rows = con.execute("SELECT * FROM cases ORDER BY id DESC").fetchall()
    con.close()
    return [dict(r) for r in rows]
