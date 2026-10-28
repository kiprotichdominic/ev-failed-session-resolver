# Session review log

Human-written. One row per session, filled in by the human after every
session, starting with Session 0. This log is the evidence of what was built
during the event: dates plus commit hashes, and a record that a human
reviewed every agent session. The agent must not fill in its own verdicts.

Columns:

- Date — calendar date the session work was reviewed.
- Tests passed — exact command and result (e.g. `pytest tests/ -q`: 12 passed).
- Expected values unchanged — confirm pre-existing test expectations and
  fixtures were not weakened to make the session pass (yes/no + note).
- Labels untouched — confirm `eval/` labels/expected outputs were not edited
  to fit the code (yes/n/a + note; n/a before labels exist).
- Dependencies added — new entries in `requirements.txt`, if any (name +
  why, and THIRD_PARTY.md updated).
- Verdict — accepted or rejected, decided by the human only.
- Commit — full hash of the commit that records the accepted work
  (empty if rejected).

| Session | Date       | Tests passed                     | Expected values unchanged | Labels untouched | Dependencies added | Verdict | Commit                                   |
| ------- | ---------- | -------------------------------- | ------------------------- | ---------------- | ------------------ | ------- | ---------------------------------------- |
| 0       | 2026-10-28 | `pytest tests/ -q`: 1 passed     | n/a (no expectations yet) | n/a (no labels)  | none               | TODO    | cb8037c3743a63eafbbde951ac099591c9118820 |

## Session notes

### Session 0 — scaffold

- Factual (agent may fill): scaffold commit only — `resolver/` module stubs,
  `app.py` docstring stub, empty `corpus/*.json`, empty `eval/cases/`,
  `tests/test_smoke.py` import check, `requirements.txt`
  (pydantic, pytest, streamlit), `.env.example`, `.gitignore`.
- Human review notes: TODO — human writes this.
- Verdict: TODO — human decides: accepted / rejected.
