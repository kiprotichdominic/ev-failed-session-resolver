# Failed-Session Resolver

All data in this demo is synthetic.

30-second pitch: when an EV charging session fails, drivers and support agents get
conflicting numbers — what the car drew, what the charger delivered, what was
refunded. This tool reconstructs the failed session from the raw inputs, resolves
exactly what is owed or refunded using auditable code-only arithmetic, and
escalates only the cases a human must see. The model explains; it never computes
money.

> Status (Oct 28, Session 10): Sessions 0–6, 8, 9 implemented, 75 tests
> passing. Session 7 (Meta client) implemented Oct 28 from the docs at
> dev.meta.ai (muse-spark-1.3, POST /chat/completions, Bearer key,
> temperature 0.2, json_object mode); one live call from the human's
> machine still needed to confirm. UI direction changed Oct 28 (human decision): Streamlit
> removed, replaced by FastAPI (api.py) + Next.js (web/), Cases page first.
> Still human-owned: eval cases/labels, corpus summaries, browser check,
> and all commits.

## How to run

Without an API key (code-only path; always works):

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -q
python eval/run_eval.py --split dev --runs 3 --client fake  # TODO: needs eval cases + labels
.venv/bin/python -m uvicorn api:app --port 8000   # terminal 1: API
cd web && npm run dev                             # terminal 2: UI on :3000
```

With an API key (model-backed explanations):

```sh
cp .env.example .env               # then set META_API_KEY, META_MODEL, META_BASE_URL
# TODO: model-backed path lands with Session 7; UI runs on canned replies
```

`.env` is gitignored. Never commit keys.

## Built during the event vs third-party

Everything under `resolver/`, `app.py`, `eval/` (runner, baseline, cases,
labels), and `corpus/` was built during the event, starting from the Session 0
scaffold. Per-session evidence with dates and commit hashes lives in
[REVIEW.md](REVIEW.md).

Third-party: libraries and any outside text are listed in
[THIRD_PARTY.md](THIRD_PARTY.md). No outside text has been pasted into this
repo; corpus entries are the human's own short summaries
(see [corpus/SOURCES.md](corpus/SOURCES.md)).

## Eval

Full method, rerun instructions, and every failed case:
[eval/EVAL.md](eval/EVAL.md).

| System   | Cases (dev / held-out) | Pass rate | TODO |
| -------- | ---------------------- | --------- | ---- |
| Baseline | TODO                   | TODO      |      |
| Resolver | TODO                   | TODO      |      |

## Limitations

- Synthetic data only; no real charger, payment, or driver data.
- Single failure domain (one session log + one payment per case).
- No production hardening: no auth, no rate limits, file-backed SQLite audit.
- Model explanations are unverified beyond the eval set; every refund draft
  requires human approval and hazard cases always need a technician.
- Meta client unimplemented (Session 7 blocked on API docs); only the fake
  client and code-only baseline run today.

## Docs

- [REVIEW.md](REVIEW.md) — per-session human review log (what was built when).
- [eval/EVAL.md](eval/EVAL.md) — eval method and results.
- [corpus/SOURCES.md](corpus/SOURCES.md) — corpus provenance and licenses.
- [THIRD_PARTY.md](THIRD_PARTY.md) — libraries and outside text.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — architecture and worked example.
- [docs/DEMO.md](docs/DEMO.md) — demo video script and case order.
