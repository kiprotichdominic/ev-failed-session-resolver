# Agent instructions

Human-written, from the brief, before Session 1. Paste brief Sections 1
and 2 below so they stop being pasted into every session prompt.

> Filename unverified: confirm the coding agent actually reads `AGENTS.md`
> automatically (vs `CLAUDE.md` or another name) by testing one session
> before relying on it.

## 1. TODO - brief Section 1 title

TODO - human pastes brief Section 1 here.

## 2. TODO - brief Section 2 title

TODO - human pastes brief Section 2 here.

## Standing rules (repo facts the agent must respect)

- All data in this demo is synthetic.
- The model explains; it never computes money. Arithmetic
  (`energy_kwh`, `owed_kes`, refund, `still_open`, `offline_minutes`) lives
  in `resolver/calc.py`; escalation rules in `resolver/rules.py`; neither
  calls the model.
- Never weaken test expectations, fixtures, or eval labels to make a
  session pass. If a test fails on new code, the code is wrong.
- Never paste outside text (specs, manuals, docs) into the repo. Corpus
  entries are the human's own short summaries; every chunk gets a row in
  `corpus/SOURCES.md`.
- New dependency in `requirements.txt` must be justified in `REVIEW.md`
  and listed in `THIRD_PARTY.md`.
- The agent does not write verdicts in `REVIEW.md` or results in
  `eval/EVAL.md`. Factual session output only; the human judges.
- Never commit `.env` or API keys. The demo must run without a key on the
  code-only path.
