FROM python:3.12-slim-bookworm AS base

COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

FROM base AS development

COPY pyproject.toml uv.lock .python-version ./
COPY shared-core/pyproject.toml ./shared-core/pyproject.toml
COPY backend-core/pyproject.toml ./backend-core/pyproject.toml
COPY agent-service/pyproject.toml ./agent-service/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package backend-core --group dev --no-install-workspace

COPY shared-core ./shared-core
COPY backend-core ./backend-core

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package backend-core --group dev

WORKDIR /app/backend-core
EXPOSE 8080
CMD ["uv", "run", "--package", "backend-core", "uvicorn", "backend_core.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload", "--reload-dir", "/app/backend-core", "--reload-dir", "/app/shared-core"]

FROM base AS production

COPY pyproject.toml uv.lock .python-version ./
COPY shared-core/pyproject.toml ./shared-core/pyproject.toml
COPY backend-core/pyproject.toml ./backend-core/pyproject.toml
COPY agent-service/pyproject.toml ./agent-service/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package backend-core --no-dev --no-editable --no-install-workspace

COPY shared-core ./shared-core
COPY backend-core ./backend-core

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package backend-core --no-dev --no-editable

WORKDIR /app/backend-core
EXPOSE 8080
CMD ["uv", "run", "--package", "backend-core", "uvicorn", "backend_core.main:app", "--host", "0.0.0.0", "--port", "8080"]
