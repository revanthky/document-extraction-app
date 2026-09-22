from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.applications import Starlette
from starlette.routing import Mount

from app.api import documents, extractions, health
from app.api import settings as settings_api
from app.config import get_app_config
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger

# When a built frontend is present (frontend/dist, a sibling of backend/), this process
# serves it directly alongside the API -- the single-process shape a DKubeX app tile
# needs. In the split local-dev workflow (`npm run dev` on its own port) this directory
# doesn't exist yet and none of this activates.
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

config = get_app_config()
configure_logging(config.log_level)
logger = get_logger(__name__)

app = FastAPI(title="Document Extraction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    started = time.monotonic()
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "unhandled_exception",
            extra={"request_id": request_id, "path": request.url.path},
        )
        raise
    duration_ms = int((time.monotonic() - started) * 1000)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "operation": f"{request.method} {request.url.path}",
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "app_error",
        extra={"request_id": request_id, "error": exc.message, "detail": exc.detail},
    )
    body = {"message": exc.message}
    if exc.detail:
        body["detail"] = exc.detail
    return JSONResponse(status_code=exc.status_code, content=body)


app.include_router(health.router)
app.include_router(settings_api.router)
app.include_router(documents.router)
app.include_router(extractions.router)

if FRONTEND_DIST.is_dir():
    _frontend_dist_resolved = FRONTEND_DIST.resolve()
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str) -> FileResponse:
        # Root-level build outputs (favicon.svg, etc.) are served as-is; any other path not
        # matched by an API route or /assets above (including client-side routes like
        # "extract") falls back to the built index.html, so React Router can take over.
        candidate = (FRONTEND_DIST / full_path).resolve()
        if full_path and candidate.is_relative_to(_frontend_dist_resolved) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")


# When running as a DKubeX app tile, the workspace's nginx forwards the *full* prefixed
# request path -- it does not strip DKUBEX_BASE_PATH -- so uvicorn's --root-path (which only
# affects URL generation, not incoming route matching) is not enough on its own. Wrapping
# the app in a Starlette Mount at that prefix does the actual stripping. Locally (no
# DKUBEX_BASE_PATH set) this is a no-op and `asgi_app` is just `app`.
_dkubex_base_path = os.environ.get("DKUBEX_BASE_PATH", "").rstrip("/")
asgi_app = Starlette(routes=[Mount(_dkubex_base_path, app=app)]) if _dkubex_base_path else app
