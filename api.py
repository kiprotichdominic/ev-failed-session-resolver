"""HTTP API for the Next.js UI. Imports the resolver modules directly."""

import json
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

from eval.baseline import build_model_output
from resolver import audit
from resolver.model import FakeModelClient, MetaClient
from resolver.models import Case
from resolver.pipeline import resolve_case

ROOT = Path(__file__).resolve().parent
CASES_DIR = ROOT / "eval" / "cases"
CORPUS_PATH = ROOT / "corpus" / "index.json"
AUDIT_DB = str(ROOT / "audit.db")


def _load_dotenv() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_dotenv()


def client_mode() -> str:
    mode = os.environ.get("RESOLVER_CLIENT", "fake").strip().lower()
    return mode if mode in ("fake", "meta") else "fake"


def make_client(case: Case):
    if client_mode() == "meta":
        try:
            return MetaClient()
        except ValueError as exc:
            raise HTTPException(500, str(exc))
    reply = build_model_output(case).model_dump_json()
    return FakeModelClient([reply])

app = FastAPI(title="Failed-Session Resolver")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DecisionIn(BaseModel):
    decision: Literal["approve", "reject"]
    note: str = ""


def _read_case(case_id: str) -> dict:
    path = CASES_DIR / f"{case_id}.json"
    if not path.exists():
        raise HTTPException(404, f"unknown case: {case_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_corpus() -> dict:
    if not CORPUS_PATH.exists():
        return {}
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


@app.get("/api/cases")
def list_cases():
    files = sorted(CASES_DIR.glob("*.json")) if CASES_DIR.exists() else []
    return {"cases": [{"case_id": f.stem} for f in files]}


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    raw = _read_case(case_id)
    try:
        Case.model_validate(raw)
    except ValidationError as exc:
        raise HTTPException(422, str(exc))
    return raw


@app.get("/api/status")
def status():
    return {"mode": client_mode(),
            "meta_key_present": bool(os.environ.get("META_API_KEY")),
            "model": os.environ.get("META_MODEL", MetaClient.DEFAULT_MODEL)}


@app.post("/api/resolve/{case_id}")
def resolve(case_id: str):
    raw = _read_case(case_id)
    try:
        case = Case.model_validate(raw)
    except ValidationError as exc:
        raise HTTPException(422, str(exc))
    result = resolve_case(case, make_client(case),
                          _load_corpus(), audit_path=AUDIT_DB)
    return result.model_dump(mode="json")


@app.post("/api/cases/{case_id}/decision")
def decide(case_id: str, body: DecisionIn):
    _read_case(case_id)
    try:
        audit.record_decision(AUDIT_DB, case_id, body.decision, body.note)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return audit.get_case(AUDIT_DB, case_id)
