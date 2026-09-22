#!/usr/bin/env bash
# Start the Document Extraction app in the workspace. Publish it first:
#
#   d3x app create --name document-extraction --display-name "Document Extraction" \
#                  --description "Extract fields from PDFs with a Vision Model" --icon icon.svg
#
# That writes .dkubex-app.env next to this script. Nothing supervises the app, so this is
# what actually makes the tile serve something -- leave it running (tmux/nohup).
#
# This app is a FastAPI backend + a Vite/React frontend. Rather than run two servers under
# one prefix, the frontend is built as static assets and served BY the backend, so the tile
# is one process on one port. `frontend/vite.config.ts` reads $DKUBEX_BASE_PATH at build
# time to prefix every emitted asset URL; `backend/app/main.py` serves that build and falls
# back to index.html for client-side routes.
set -euo pipefail
cd "$(dirname "$0")"

# PORT and DKUBEX_BASE_PATH come from the workspace, not from this file.
set -a
. ./.dkubex-app.env
set +a

echo "[run.sh] Building frontend for DKUBEX_BASE_PATH=$DKUBEX_BASE_PATH ..."
(cd frontend && npm install --no-audit --no-fund && npm run build)

echo "[run.sh] Starting backend on port $PORT ..."
cd backend
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --quiet -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

# Apply any pending migrations before serving.
alembic upgrade head

exec uvicorn app.main:asgi_app --host 0.0.0.0 --port "$PORT"
