# Video Documentation Plan - EV-Failed-Session Resolver

Target: one demo video, max 3 minutes, for the Meta Global AI Developer
Hackathon 2026 submission. Audience is judges who have never seen the app.

## Storyline (timestamped)

| Time | Beat | On screen |
|------|------|-----------|
| 0:00 - 0:20 | Hook: one failed charging session, one angry driver, one refund decision. State the rule: the model explains, code computes money. | Title card + app home |
| 0:20 - 0:50 | Pick sample case C-014. Show complaint (Swahili), session log, payment. | Cases page, Sample cases tab |
| 0:50 - 1:40 | Press Resolve. Narrate the live progress steps, then walk the result: side/cause, verified clause, calc numbers (1.2 kWh, owed 30, refund 970), driver message in Swahili. | Result drawer, calc card |
| 1:40 - 2:10 | Human-in-the-loop: refund draft needs approval. Approve it, show recorded decision. Mention escalate path briefly. | Approve/Reject buttons |
| 2:10 - 2:40 | Trust: open Audit page, show the run row, preview verdict, raw JSON behind it. Flash Evaluation page (model vs baseline). | Audit + Evaluation pages |
| 2:40 - 3:00 | Close: synthetic data note, stack (FastAPI + Next.js + Muse Spark), repo link. | Title card |

## Script notes

- Say out loud: "All data in this demo is synthetic."
- When numbers appear, say "computed by code, not the model."
- Show the "Live model output (muse-spark-1.3)" banner at least once.
- Keep narration in English even when the driver message is Swahili; translate it in one sentence.

## Recording checklist

- [ ] Backend + frontend running via `./start-dev.sh`
- [ ] `.env` set with `RESOLVER_CLIENT=meta` and a valid key (never show the key on screen)
- [ ] Fresh audit DB or a known case list, so the Audit page is tidy
- [ ] Browser zoom 125%, dark mode on, notifications off
- [ ] Sample C-014 JSON ready to paste (in case live resolve is slow, paste pre-run output is not allowed - resolve live)
- [ ] Mic check, one full dry run before recording

## Do / do not

- Do show one real end-to-end resolve with the live model.
- Do not show API keys, tokens, or `.env` contents.
- Do not promise production features (auth, payments, real chargers).
- Do not exceed 3 minutes; cut the Evaluation beat first if over time.
