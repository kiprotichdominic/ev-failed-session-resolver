## Goal

Deliver a 5-minute hackathon pitch (slides + live demo) for EV-Failed-Session
Resolver that leaves judges trusting the human-in-the-loop refund flow.

## Success Criteria

- Pitch fits 5 minutes: 2 minutes slides, 2 minutes live demo, 1 minute close.
- Live demo resolves one case end to end with the model banner visible.
- Every judge question about "who computes the money" is answerable from the
  architecture slide and the UI's calc/model split.
- Backup screenshots or the VIDEO.md recording cover a total live failure.

## Approach

Six slides plus a live demo in the middle. Slides sell the problem and the
trust design; the demo proves it. Reuse the README architecture diagram and
the docs/VIDEO.md storyline so no new narrative is invented.

## Steps

1. Slide 1 - Problem: failed EV sessions strand drivers and force operators
   to guess refunds from messy logs and complaints in several languages.
2. Slide 2 - Rule: the model explains, code computes money. Show the
   placeholder contract (code substitutes {{energy_kwh}}, {{owed_kes}},
   {{refund_kes}}) and the escalate-unless-all-checks-pass policy.
3. Slide 3 - Architecture: complaint + log + payment into FastAPI pipeline
   (calc, codes, retrieve, rules), Muse Spark for narrative only, Next.js UI,
   SQLite audit. Reuse the README mermaid diagram.
4. Live demo (2 min): resolve sample case C-014, narrate the progress steps,
   show verified clause, calc card, Swahili driver message, then approve the
   refund draft and show the recorded decision on the Audit page.
5. Slide 4 - Trust: escalation reasons, approval gate, audit row with raw
   model output, Evaluation page (model vs code-only baseline).
6. Slide 5 - Stack and honesty: FastAPI + Next.js + Muse Spark, 107 pytest,
   synthetic data only, MIT licensed, independent project not made or
   endorsed by Meta.
7. Slide 6 - Close: repo link, one-line ask, "all data in this demo is
   synthetic" on screen.

## Validation Plan

- Dry run with a timer: slides 2:00, demo 2:00, close 1:00; cut Slide 5
  detail first if over.
- Demo rehearsal checklist: `./start-dev.sh` running, `RESOLVER_CLIENT=meta`,
  live banner visible, C-014 resolves without error, approve button records.
- Backup check: screenshots of each demo state plus the finished video from
  docs/VIDEO.md ready to play if the network or API fails.

## Risks / Open Questions

- Live model latency may stretch the 2-minute demo slot; mitigation is the
  narrated progress steps plus screenshots as fallback, never faked output.
- Pitch length cap assumed at 5 minutes; if the rules state otherwise, cut
  Slide 5 first, then Slide 1.
