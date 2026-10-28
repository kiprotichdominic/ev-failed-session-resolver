"""Session 4 tests: section 6.6, written before model.py."""

import json

import pytest

from resolver.model import (
    SYSTEM_PROMPT,
    FakeModelClient,
    MetaClient,
    build_user_message,
    parse_and_validate,
    run_model,
)
from resolver.models import Case
from resolver.retrieve import Chunk


def _case():
    return Case.model_validate({
        "case_id": "C-014",
        "complaint": {"text": "nimelipa 1000 lakini hakuna power",
                      "received_at": "2026-10-21T18:42:00+03:00"},
        "session_log": [
            {"ts": "2026-10-21T18:31:02+03:00", "type": "StartTransaction",
             "connector_id": 1, "meter_wh": 0},
            {"ts": "2026-10-21T18:33:10+03:00", "type": "StatusNotification",
             "connector_id": 1, "status": "Faulted", "error_code": "GroundFailure"},
            {"ts": "2026-10-21T18:33:41+03:00", "type": "StopTransaction",
             "connector_id": 1, "meter_wh": 1200, "reason": "EmergencyStop"},
        ],
        "payment": {"method": "mobile_money", "currency": "KES",
                    "held": 1000, "captured": 1000, "status": "captured"},
        "tariff_kes_per_kwh": 25,
    })


def _facts():
    return {"still_open": True, "estimated": False, "underpaid": False,
            "hazard_codes": ["GroundFailure"], "payment_status": "captured",
            "payment_method": "mobile_money"}


def _chunks():
    return [Chunk(clause_id="OCPP16-ERR-GroundFailure", title="t",
                  text="ground failure", source="s")]


def _reply_dict(**overrides):
    data = {
        "side": "charger",
        "cause": "A ground failure faulted the connector.",
        "evidence": [{"source": "log", "ref": "session_log[1]",
                      "note": "Faulted status"}],
        "clause_ids": ["OCPP16-ERR-GroundFailure"],
        "confidence": 0.86,
        "driver_message": {"language": "en",
                           "text": "Stopped. Energy {{energy_kwh}} kWh, "
                                   "owed {{owed_kes}} KES, "
                                   "refund {{refund_kes}} KES."},
        "technician_note": "Isolate connector 1.",
    }
    data.update(overrides)
    return data


def _reply_json(**overrides):
    return json.dumps(_reply_dict(**overrides))


def test_valid_reply_returns_output_after_one_attempt():
    client = FakeModelClient([_reply_json()])
    out, attempts = run_model(client, _case(), _facts(), _chunks())
    assert out is not None
    assert out.side == "charger"
    assert len(attempts) == 1
    assert attempts[0]["error"] is None
    assert len(client.calls) == 1
    assert client.calls[0]["system"] == SYSTEM_PROMPT


def test_invalid_then_valid_retries_once():
    client = FakeModelClient(["not json {{{", _reply_json()])
    out, attempts = run_model(client, _case(), _facts(), _chunks())
    assert out is not None
    assert len(attempts) == 2
    assert attempts[0]["error"] is not None
    assert "Your previous reply was invalid" in attempts[1]["user_message"]


def test_two_invalid_replies_return_none():
    client = FakeModelClient(["bad {", "worse ["])
    out, attempts = run_model(client, _case(), _facts(), _chunks())
    assert out is None
    assert len(attempts) == 2


@pytest.mark.parametrize("text", ["Pay KES 970 now", "got 1.2 kWh", "kWh 3 today"])
def test_literal_figure_next_to_unit_rejected(text):
    reply = _reply_json(driver_message={"language": "en", "text": text})
    with pytest.raises(ValueError):
        parse_and_validate(reply)


def test_unknown_placeholder_rejected():
    reply = _reply_json(driver_message={"language": "en",
                                        "text": "refund {{amount}} KES"})
    with pytest.raises(ValueError):
        parse_and_validate(reply)


def test_fenced_block_accepted():
    for fence in ("```json", "```"):
        reply = f"{fence}\n{_reply_json()}\n```"
        out = parse_and_validate(reply)
        assert out.side == "charger"


def test_confidence_out_of_range_rejected():
    with pytest.raises(ValueError):
        parse_and_validate(_reply_json(confidence=1.5))


def test_meta_client_missing_key(monkeypatch):
    monkeypatch.delenv("META_API_KEY", raising=False)
    with pytest.raises(ValueError):
        MetaClient()


def test_meta_client_reads_env(monkeypatch):
    monkeypatch.setenv("META_API_KEY", "env-key")
    monkeypatch.setenv("META_MODEL", "env-model")
    monkeypatch.setenv("META_BASE_URL", "https://example.test/v9/")
    client = MetaClient()
    assert (client.api_key, client.model, client.base_url) == (
        "env-key", "env-model", "https://example.test/v9")


def test_meta_client_defaults():
    client = MetaClient(api_key="k")
    assert client.model == "muse-spark-1.3"
    assert client.base_url == "https://api.meta.ai/v1"


def test_meta_client_complete():
    from unittest.mock import MagicMock, patch

    reply = _reply_json()
    resp = MagicMock()
    resp.json.return_value = {"choices": [{"message": {"content": reply}}]}
    client = MetaClient(api_key="test-key")
    with patch("httpx.post", return_value=resp) as post:
        assert client.complete("sys", "user") == reply
    url, kwargs = post.call_args.args[0], post.call_args.kwargs
    assert url == "https://api.meta.ai/v1/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert kwargs["json"]["model"] == "muse-spark-1.3"
    assert kwargs["json"]["messages"] == [{"role": "system", "content": "sys"},
                                          {"role": "user", "content": "user"}]
    assert kwargs["json"]["temperature"] == 0.2
    assert kwargs["json"]["response_format"] == {"type": "json_object"}


def test_meta_client_malformed_response():
    from unittest.mock import MagicMock, patch

    resp = MagicMock()
    resp.json.return_value = {"oops": 1}
    client = MetaClient(api_key="test-key")
    with patch("httpx.post", return_value=resp):
        with pytest.raises(ValueError):
            client.complete("sys", "user")


def test_build_user_message_shape_and_no_numbers():
    payload = json.loads(build_user_message(_case(), _facts(), _chunks()))
    assert set(payload) == {"complaint", "session_log", "facts", "chunks"}
    assert payload["facts"] == _facts()
    assert payload["chunks"] == [{"clause_id": "OCPP16-ERR-GroundFailure",
                                  "text": "ground failure"}]
    for entry in payload["session_log"]:
        assert set(entry) == {"index", "ts", "type", "connector_id"}
    raw = build_user_message(_case(), _facts(), _chunks())
    assert "meter_wh" not in raw
    assert "tariff" not in raw


def test_system_prompt_markers():
    assert "{{energy_kwh}}" in SYSTEM_PROMPT
    assert "{{owed_kes}}" in SYSTEM_PROMPT
    assert "{{refund_kes}}" in SYSTEM_PROMPT
    assert "Return JSON only, matching the schema. No markdown and no commentary." in SYSTEM_PROMPT
