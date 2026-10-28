# Failed-Session Resolver

All data in this demo is synthetic.

30-second pitch: when an EV charging session fails, drivers and support agents get
conflicting numbers — what the car drew, what the charger delivered, what was
refunded. This tool reconstructs the failed session from the raw inputs, resolves
exactly what is owed or refunded using auditable code-only arithmetic, and
escalates only the cases a human must see. The model explains; it never computes
money.

> Status: Session 0 scaffold (Oct 28). Modules are stubs; the resolver,
> corpus, and eval cases land in later sessions. Sections below marked
> TODO fill in as the event progresses.

## How to run

Without an API key (code-only path; always works):

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -q
python eval/run_eval.py            # TODO: works once eval cases land
streamlit run app.py               # TODO: works once the UI lands
```

With an API key (model-backed explanations):

```sh
cp .env.example .env               # then set META_API_KEY, META_MODEL, META_BASE_URL
streamlit run app.py               # TODO: works once the UI lands
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

- TODO (Session 10): fill in honestly — e.g. synthetic data only, single
  failure domain, no production hardening, model explanations unverified
  beyond the eval set.

## Docs

- [REVIEW.md](REVIEW.md) — per-session human review log (what was built when).
- [eval/EVAL.md](eval/EVAL.md) — eval method and results.
- [corpus/SOURCES.md](corpus/SOURCES.md) — corpus provenance and licenses.
- [THIRD_PARTY.md](THIRD_PARTY.md) — libraries and outside text.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — architecture and worked example.
- [docs/DEMO.md](docs/DEMO.md) — demo video script and case order.
