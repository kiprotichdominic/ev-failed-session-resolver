#!/bin/sh
# Start API (:8000) + web UI (:3000) together. Ctrl-C stops both.
set -u
cd "$(dirname "$0")"
.venv/bin/python -m uvicorn api:app --port 8000 &
API_PID=$!
(cd web && npm run dev) &
WEB_PID=$!
trap 'kill $API_PID $WEB_PID 2>/dev/null' INT TERM
echo "API: http://localhost:8000  UI: http://localhost:3000"
wait
