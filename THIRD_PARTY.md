# Third-party libraries and text

## Libraries

- pydantic - data contracts (resolver/models.py)
- pytest - test runner (tests/)
- fastapi - HTTP API for the Next.js UI (api.py; human-approved Oct 28)
- uvicorn - API server (human-approved Oct 28)
- httpx - API tests via FastAPI TestClient, and Meta API calls in MetaClient (human-approved Oct 28; no new dependency for Session 7)
- httpx doubles as the Meta API HTTP client (chosen in Session 7; no extra dependency).
- Node dependencies for web/ are pinned in web/package.json.
- react-icons - sun/moon icons for the theme toggle (web/app/theme-toggle.tsx).
- streamlit - removed Oct 28 when the UI moved to Next.js + API (human decision).

## Outside text

None. No text from the OCPP specification, vendor manuals, or any outside document has been pasted into this repo. Corpus summaries will be the human's own short summaries.
