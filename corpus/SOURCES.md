# Corpus sources

Human-written, while building the corpus. One entry per chunk: the human's
own short summary (never pasted outside text), the source link, and license
notes.

> Status: corpus is empty (Session 0: `corpus/error_codes.json` and
> `corpus/index.json` are `{}`).

| Chunk id | Summary (own words) | Source link | License notes |
| -------- | ------------------- | ----------- | ------------- |
| OCPP16-ERR-GroundFailure | A ground failure means current is leaking somewhere it should not go, so the charger stops the session as a safety precaution. The connector should stay out of service until a technician inspects the grounding and cabling. | Agent-drafted; human to verify against OCPP 1.6 spec | Original text, no outside text used |

Rules:

- No text from the OCPP specification, vendor manuals, or any outside
  document is pasted into this repo. Summaries only.
- Every chunk needs a row here before it counts as sourced.
