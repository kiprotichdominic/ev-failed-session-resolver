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
RESULTS_PATH = ROOT / "eval" / "results.json"
BASELINE_PATH = ROOT / "eval" / "baseline_results.json"
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


class ComplaintIn(BaseModel):
    scenario: Literal["fault", "never"]
    fault_code: str | None = None
    language: Literal["en", "sw", "sheng", "fr", "de", "it", "zh", "pt"]
    paid_kes: int = 0


# Mirrors GEN_COMPLAINTS in web/app/page.tsx (fake-mode path).
CANNED_COMPLAINTS = {
    ("fault", "en"):
        "The charging session stopped with an error before my car was full.",
    ("fault", "sw"): "Chaji ilisimama na hitilafu kabla gari haijajaa.",
    ("fault", "sheng"): "Chaji ilistop na error kabla gari ijaze.",
    ("fault", "fr"):
        "La session de charge s'est arrêtée sur une erreur avant que "
        "ma voiture soit chargée.",
    ("fault", "de"):
        "Der Ladevorgang wurde mit einem Fehler abgebrochen, bevor mein "
        "Auto vollständig geladen war.",
    ("fault", "it"):
        "La sessione di ricarica si è interrotta con un errore prima che "
        "la mia auto fosse carica.",
    ("fault", "pt"):
        "A sessão de carregamento parou com um erro antes de o meu carro "
        "estar carregado.",
    ("fault", "zh"): "我的车还没充满，充电就出错停止了。",
    ("never", "en"): "I paid but the charger never started.",
    ("never", "sw"): "Nimelipa lakini chaja haijaanza.",
    ("never", "sheng"): "Nimelipa lakini chaja haija-start.",
    ("never", "fr"): "J'ai payé mais le chargeur n'a jamais démarré.",
    ("never", "de"): "Ich habe bezahlt, aber das Ladegerät ist nie gestartet.",
    ("never", "it"): "Ho pagato ma il caricatore non è mai partito.",
    ("never", "pt"): "Paguei mas o carregador nunca arrancou.",
    ("never", "zh"): "我付了钱，但充电桩一直没启动。",
}

LANG_NAMES = {
    "en": "English", "sw": "Swahili", "sheng": "Sheng",
    "fr": "French", "de": "German", "it": "Italian",
    "zh": "Chinese", "pt": "Portuguese",
}

GEN_SYSTEM = (
    "You write one short driver complaint for testing an EV charging "
    "support tool. Reply with the complaint text only: no quotes, "
    "no commentary, no JSON."
)


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


@app.post("/api/analyse")
def analyse(raw: dict):
    try:
        case = Case.model_validate(raw)
    except ValidationError as exc:
        raise HTTPException(422, str(exc))
    result = resolve_case(case, make_client(case),
                          _load_corpus(), audit_path=AUDIT_DB)
    return result.model_dump(mode="json")


@app.post("/api/generate-complaint")
def generate_complaint(body: ComplaintIn):
    if body.scenario == "fault" and not body.fault_code:
        raise HTTPException(422, "fault_code is required for fault scenario")
    if client_mode() == "meta":
        try:
            client = MetaClient()
        except ValueError as exc:
            raise HTTPException(500, str(exc))
        if body.scenario == "fault":
            desc = f"a charging session stopped with error {body.fault_code}"
        else:
            desc = "the driver paid but the charger never started"
        user = (
            f"Write a one-or-two-sentence driver complaint about {desc}. "
            f"Language: {LANG_NAMES[body.language]} ({body.language}). "
            f"The driver paid {body.paid_kes} KES "
            f"(they may mention it)."
        )
        text = client.complete(GEN_SYSTEM, user).strip()
        if text:
            return {"text": text[:500]}
    return {"text": CANNED_COMPLAINTS[(body.scenario, body.language)]}


@app.post("/api/cases/{case_id}/decision")
def decide(case_id: str, body: DecisionIn):
    try:
        audit.record_decision(AUDIT_DB, case_id, body.decision, body.note)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return audit.get_case(AUDIT_DB, case_id)


def _read_results(path: Path):
    if not path.exists():
        raise HTTPException(404, f"not found: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/results")
def results():
    return _read_results(RESULTS_PATH)


@app.get("/api/baseline")
def baseline():
    return _read_results(BASELINE_PATH)


@app.get("/api/audit")
def list_audit():
    return {"runs": audit.list_cases(AUDIT_DB)}
