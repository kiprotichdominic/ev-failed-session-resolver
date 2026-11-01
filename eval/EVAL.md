# Evaluation

Human-written. How the eval was built, how to rerun it, and what happened -
including every failure.

> Status: no cases or labels yet (Session 0). This file fills in as the eval
> lands; results table due Nov 1–2.

## How the cases and labels were written

TODO - human writes: what each case contains, how labels/expected outputs
were derived, and confirmation that labels were fixed before the resolver
was tuned against them.

## Dev / held-out split

TODO - human writes: which cases are dev (may be inspected while building)
vs held-out (never inspected until the final run), file lists, and the
rule for keeping held-out cases unseen.

- Dev: `eval/cases/` TODO
- Held-out: TODO
- Labels: `eval/labels.json` (TODO: not created yet)

## How to rerun

```sh
pytest tests/ -q
python eval/run_eval.py          # writes eval/results.json (TODO: not yet)
python eval/baseline.py          # writes eval/baseline_results.json (TODO: not yet)
```

With an API key: copy `.env.example` to `.env` and set `META_API_KEY`,
`META_MODEL`, `META_BASE_URL` first (TODO: confirm when the model path lands).

## Results

TODO.

| System   | Dev pass | Held-out pass | Notes |
| -------- | -------- | ------------- | ----- |
| Baseline | TODO     | TODO          |       |
| Resolver | TODO     | TODO          |       |

## Failed cases

TODO - every failed case, dev and held-out: case id, expected vs actual,
and a one-line diagnosis. No failures hidden.
