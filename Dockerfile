# Single image serving both the API and the built frontend as one process, matching the
# architecture used for the DKubeX workspace app tile (see backend/app/main.py: `asgi_app`
# Mounts the whole app at $DKUBEX_BASE_PATH when that env var is set).

FROM node:20-alpine AS frontend-build
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# The platform serves this app at a fixed path (its Helm release name), not a per-user one,
# so the base path is known at image-build time and can be baked into the Vite bundle here.
ARG DKUBEX_BASE_PATH=/document-extraction
ENV DKUBEX_BASE_PATH=${DKUBEX_BASE_PATH}
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY --from=frontend-build /src/frontend/dist frontend/dist

WORKDIR /app/backend
EXPOSE 8080
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:asgi_app --host 0.0.0.0 --port 8080"]
