"""Model clients, prompt, and output validation. No arithmetic here."""

import json
import os
import re
from typing import Protocol

import httpx

from resolver.models import Case, ModelOutput
from resolver.retrieve import Chunk

SYSTEM_PROMPT = """You analyze failed EV charging sessions for a charging operator. You receive a driver complaint, an indexed session log, a few facts and reference chunks.

Rules:
1. Use only the supplied log and reference chunks. For every claim, cite a log entry as session_log[i] or a reference by its clause ID.
2. If evidence is missing or conflicting, set side to "unknown" and confidence below 0.5.
3. Never write a money or energy figure. Use the placeholders {{energy_kwh}}, {{owed_kes}} and {{refund_kes}} instead.
4. Write driver_message in the language of the complaint: en, sw, sheng, fr, de, it, zh or pt.
5. If a hazard code is listed in the facts, tell the driver to use another charger and write a technician_note. Never suggest a remote reset.
6. Return JSON only, matching the schema. No markdown and no commentary.

Schema: side (charger, network, vehicle, driver, payment or unknown), cause (one sentence), evidence (list of source, ref, note), clause_ids (list), confidence (0 to 1), driver_message (language, text), technician_note (string or null)."""

ALLOWED_PLACEHOLDERS = {"energy_kwh", "owed_kes", "refund_kes"}

_PLACEHOLDER = re.compile(r"\{\{([^{}]*)\}\}")
_FIGURE = re.compile(
    r"(?:\d[\d,]*\.?\d*\s*(?:KES|kWh)|(?:KES|kWh)\s*\d[\d,]*\.?\d*)",
    re.IGNORECASE,
)

_FACT_KEYS = ("still_open", "estimated", "underpaid", "hazard_codes",
              "payment_status", "payment_method")


class ModelClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class FakeModelClient(ModelClient):
    """Test double: replays canned replies in order and records calls."""

    def __init__(self, replies: list[str]):
        self._replies = list(replies)
        self.calls: list[dict] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append({"system": system, "user": user})
        if not self._replies:
            raise IndexError("FakeModelClient is out of canned replies")
        return self._replies.pop(0)


class MetaClient(ModelClient):
    """Live client for the Meta Model API.

    Session 7, from the docs at dev.meta.ai: POST {base}/chat/completions
    with a Bearer key, OpenAI-style {model, messages} body, low temperature
    and json_object response_format. No docs text is copied into the repo.
    """

    DEFAULT_MODEL = "muse-spark-1.3"
    DEFAULT_BASE_URL = "https://api.meta.ai/v1"

    def __init__(self, *, api_key: str | None = None,
                 model: str | None = None, base_url: str | None = None,
                 timeout: float = 120.0) -> None:
        key = api_key or os.environ.get("META_API_KEY")
        if not key:
            raise ValueError("META_API_KEY is not set")
        self.api_key = key
        self.model = model or os.environ.get("META_MODEL") or self.DEFAULT_MODEL
        self.base_url = (base_url or os.environ.get("META_BASE_URL")
                         or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    def complete(self, system: str, user: str) -> str:
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}],
                  "temperature": 0.2,
                  "response_format": {"type": "json_object"}},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        try:
            content = resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"unexpected Meta API response shape: {exc}")
        if not isinstance(content, str):
            raise ValueError("unexpected Meta API response shape: no text content")
        return content


def build_user_message(case: Case, facts: dict, chunks: list[Chunk]) -> str:
    """Build the section 5 user message. Carries no amounts or tariffs."""
    payload = {
        "complaint": {"text": case.complaint.text,
                      "received_at": case.complaint.received_at.isoformat()},
        "session_log": [{"index": i, "ts": e.ts.isoformat(), "type": e.type,
                         "connector_id": e.connector_id}
                        for i, e in enumerate(case.session_log)],
        "facts": {key: facts[key] for key in _FACT_KEYS},
        "chunks": [{"clause_id": c.clause_id, "text": c.text} for c in chunks],
    }
    return json.dumps(payload, indent=2)


def _strip_fence(text: str) -> str:
    if text.startswith("```") and text.rstrip().endswith("```"):
        lines = text.rstrip().splitlines()
        return "\n".join(lines[1:-1])
    return text


def parse_and_validate(text: str) -> ModelOutput:
    """Parse a reply and validate it. Raises ValueError when invalid."""
    body = _strip_fence(text.strip())
    data = json.loads(body)
    out = ModelOutput.model_validate(data)
    for name in _PLACEHOLDER.findall(body):
        if name not in ALLOWED_PLACEHOLDERS:
            raise ValueError(f"placeholder {{{{{name}}}}} is not allowed")
    found = _FIGURE.search(_PLACEHOLDER.sub("", body))
    if found:
        raise ValueError(
            f"literal figure next to KES or kWh: {found.group(0)!r}")
    return out


def run_model(client: ModelClient, case: Case, facts: dict,
              chunks: list[Chunk]) -> tuple[ModelOutput | None, list[dict]]:
    """One call, one retry with the section 5 retry message, else None.

    Returns the output (or None) plus the list of attempts, each with
    user_message, raw_output and error keys.
    """
    attempts: list[dict] = []
    first = build_user_message(case, facts, chunks)
    user_message = first
    for _ in range(2):
        raw = None
        try:
            raw = client.complete(SYSTEM_PROMPT, user_message)
            out = parse_and_validate(raw)
        except Exception as exc:
            attempts.append({"user_message": user_message,
                             "raw_output": raw, "error": str(exc)})
            user_message = (
                first + "\n\nYour previous reply was invalid: "
                f"{exc}. Return corrected JSON only."
            )
            continue
        attempts.append({"user_message": user_message,
                         "raw_output": raw, "error": None})
        return out, attempts
    return None, attempts
