# Document Extraction App

Extract user-defined fields from PDF documents using a configurable Vision/Multimodal LLM
(any OpenAI-compatible API, including DKubeX SecureLLM).

## What it does

1. Configure a Vision Model (OpenAI-compatible endpoint) in **Settings**.
2. Upload a PDF on the **Document Extraction** page.
3. Define arbitrary fields to extract (name, description, type, required).
4. Run extraction — the backend renders each PDF page as an image, sends all pages plus
   your field definitions to the Vision Model in a single request, and validates the
   response.
5. View results (value, confidence, page, evidence), download as JSON/CSV, or run
   **Extract Again** to create a new extraction run without losing the previous one.

Only PDF is supported today; the architecture keeps PDF handling behind a small service
interface so other file types could be added later without touching extraction logic.

## Architecture

```
frontend/   React + TypeScript + Vite + Tailwind CSS
backend/    FastAPI + SQLAlchemy 2.x (async) + Alembic
            ├── pdf/       PyMuPDF-based rendering, isolated from the vision provider
            ├── vision/    VisionModelProvider abstraction + OpenAICompatibleProvider
            ├── storage/   ObjectStorage abstraction + MinIOObjectStorage
            ├── services/  document + extraction orchestration
            ├── api/       FastAPI routers (Pydantic request/response models)
            └── db/        SQLAlchemy models (Document, Extraction, ExtractionField,
                            ExtractionResult, DocumentSection)
```

- **PostgreSQL** is the system of record for all structured data: document metadata,
  extraction runs, field definitions, results, confidence, evidence, and verification
  state. No PDF bytes are ever stored in Postgres.
- **MinIO** is the system of record for the original PDF binary. The original file is
  kept after extraction so it can be reopened/reprocessed later.
- A document can have multiple extraction runs; **Extract Again** always creates a new
  `Extraction` row rather than overwriting the previous one.
- The Vision Model is abstracted behind `VisionModelProvider`; `OpenAICompatibleProvider`
  works against vLLM, OpenAI, or DKubeX SecureLLM (which is just an OpenAI-compatible
  endpoint at `https://<host>/securellm/v1`) — there is no provider-specific branching in
  the extraction logic itself.

## Tech stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS, react-router-dom
- **Backend**: Python, FastAPI, Pydantic, Uvicorn
- **PDF processing**: PyMuPDF (`pymupdf`)
- **Object storage**: MinIO
- **Database**: PostgreSQL, SQLAlchemy 2.x, Alembic

## Installation

Requires Python 3.12+ (tested on 3.14), Node 20+, and access to a PostgreSQL instance and
a MinIO instance (see below for a quick way to run both locally with Docker — the app
itself has no Docker/Compose/Kubernetes dependency; those are just one way to stand up the
two external services in development).

### 1. Start PostgreSQL and MinIO (development only)

The app expects both as externally available services — how you run them is up to you.
For local development, plain Docker containers are enough (no docker-compose file is used
or required):

```bash
docker run -d --name doc-extract-postgres \
  -e POSTGRES_USER=document_extractor -e POSTGRES_PASSWORD=document_extractor \
  -e POSTGRES_DB=document_extractor -p 5432:5432 postgres:16

docker run -d --name doc-extract-minio \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  -p 9000:9000 -p 9001:9001 quay.io/minio/minio:latest server /data --console-address ":9001"
```

(`quay.io/minio/minio` is used above because some environments block anonymous pulls from
`minio/minio` on Docker Hub; substitute whichever registry mirror you have access to.)

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL / MINIO_* / MODEL_* as needed
alembic upgrade head
```

### 3. Frontend

```bash
cd frontend
npm install
```

## Running

```bash
# Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```

The frontend dev server proxies `/api/*` to `http://localhost:8000` (configured in
`vite.config.ts`). Ports are configurable via the usual `--port` flags / Vite config.

## Model configuration

Open **Settings** first (it's the default page). Two provider presets are offered, both of
which use the exact same OpenAI-compatible backend:

- **OpenAI Compatible** — point `API Base URL` at any OpenAI-compatible chat completions
  endpoint (vLLM, OpenAI itself, etc.), e.g. `http://localhost:8000/v1`.
- **DKubeX (SecureLLM)** — selecting this with an empty Base URL auto-fills
  `https://<host>/securellm/v1` once you provide the host.

Set the API key, model name (or use **Fetch Models** to list what the endpoint reports),
temperature, max tokens, timeout, and PDF rendering DPI, then **Test Connection** before
uploading documents. Settings persist to a JSON file (`SETTINGS_FILE`, default
`./.data/model_settings.json`, created with `0600` permissions) so they survive backend
restarts; API keys are always masked in the UI and never logged.

## API overview

```
GET    /api/health

GET    /api/settings/model
PUT    /api/settings/model
POST   /api/settings/model/test
POST   /api/settings/model/models

POST   /api/documents/upload
GET    /api/documents/{document_id}
GET    /api/documents/{document_id}/pages/{page_num}
GET    /api/documents/{document_id}/download
DELETE /api/documents/{document_id}

POST   /api/extractions
GET    /api/extractions/{extraction_id}
GET    /api/extractions/{extraction_id}/result
GET    /api/extractions/{extraction_id}/download/json
GET    /api/extractions/{extraction_id}/download/csv
```

All request/response bodies are validated with Pydantic models (see `backend/app/schemas`).

## Testing

Backend (no real Vision Model API key required — synthetic PDFs are generated with
`reportlab`, and the Vision Model is mocked; the persistence tests run against the real
PostgreSQL/MinIO dev instances):

```bash
cd backend && source .venv/bin/activate
pytest
ruff check app tests
mypy app
```

Frontend:

```bash
cd frontend
npm run test    # vitest
npm run lint    # oxlint
npx tsc --noEmit
```

## Running as a DKubeX app

This app can run inside DKubeX two ways; both use the same `$DKUBEX_BASE_PATH` contract, so
the app code is identical either way (`backend/app/main.py` wraps itself in a Starlette
`Mount` at that path when the env var is set — see the comment there for why plain
`--root-path` isn't sufficient).

- **Workspace app tile** (`run.sh`, `.dkubex-app.env`, `icon.svg` at the repo root) — a live
  tile in your own DKubeX workspace, published with `d3x app create`. Builds the frontend and
  starts the backend directly on the workspace-allocated port; see `run.sh`.
- **Platform app** (`charts/document-extraction/`, `Dockerfile`) — an installable Helm chart
  for the DKubeX catalog, with `postgres` and `minio` auto-provisioned as dependencies and an
  app-owned PVC for the Settings JSON file. Build the image from the repo root
  (`docker build -t <registry>/document-extraction:<tag> .`) — the frontend's base path is
  baked in at image-build time via the `DKUBEX_BASE_PATH` build arg (default
  `/document-extraction`, matching the chart's release name; if you rename the chart, rebuild
  the image with a matching build arg). Validate the chart with
  `python3 <package-app-skill>/scripts/validate_chart.py charts/document-extraction`.
  Publishing the image to a real registry and the chart to `dkubeio/helm-charts` (or your own
  chart repo) is a deployment step outside this repo's scope — `image.repository`/`tag` in
  `charts/document-extraction/values.yaml` are placeholders to update once you have one.

## Troubleshooting

- **"Only PDF documents are supported."** — the upload endpoint rejects any file whose
  content type isn't `application/pdf`.
- **Extraction fails immediately with a 400** — the Vision Model isn't configured yet;
  set an API base URL and model name in Settings.
- **401 from the Vision Model** — check the API key in Settings; it's never echoed back
  by the API, only a masked placeholder and an `api_key_configured` flag are returned.
- **"The Vision Model did not return valid structured data."** — the model's response
  couldn't be parsed as the expected JSON shape even after stripping markdown fencing; the
  error includes a truncated snippet of the raw response for diagnosis (never full
  document content or extracted values are logged).
- **MinIO/Postgres connection errors on startup** — confirm both containers/services are
  running and that `DATABASE_URL` / `MINIO_ENDPOINT` in `.env` match them.
