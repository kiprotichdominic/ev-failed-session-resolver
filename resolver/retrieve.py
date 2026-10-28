"""Corpus lookup: chunks for error codes and complaint keywords."""

import json
import re
from pathlib import Path

from resolver import codes
from resolver.models import StrictModel

INDEX_PATH = Path(__file__).resolve().parent.parent / "corpus" / "index.json"

_WORD = re.compile(r"[a-z0-9]+")


class Chunk(StrictModel):
    clause_id: str
    title: str
    text: str
    source: str


def _load_index() -> dict[str, Chunk]:
    with open(INDEX_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return {clause_id: Chunk(clause_id=clause_id, **entry)
            for clause_id, entry in raw.items() if not clause_id.startswith("_")}


def _words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def chunks_for(error_codes: list[str], complaint_text: str, k: int = 5) -> list[Chunk]:
    """Error-code chunks first, then keyword matches, deduped, at most k."""
    index = _load_index()
    out: list[Chunk] = []
    seen: set[str] = set()

    def add(chunk: Chunk | None) -> None:
        if chunk is not None and chunk.clause_id not in seen:
            seen.add(chunk.clause_id)
            out.append(chunk)

    for code in error_codes:
        info = codes.lookup(code)
        if info is not None:
            add(index.get(info.clause_id))
    keywords = [w for w in dict.fromkeys(_words(complaint_text)) if len(w) >= 4]
    ranked: list[tuple[int, str, Chunk]] = []
    for chunk in index.values():
        words = set(_words(chunk.title + " " + chunk.text))
        count = sum(1 for w in keywords if w in words)
        if count > 0:
            ranked.append((count, chunk.clause_id, chunk))
    for _, _, chunk in sorted(ranked, key=lambda r: (-r[0], r[1])):
        add(chunk)
    return out[:k]
