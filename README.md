# AI Support Agent Platform

Phase 1 monorepo scaffold: Docker Compose local stack, shared tenant/storage/vector contracts, and stub services so developers can start Phase 1 feature work.

Architecture docs live in [`docs/`](docs/README.md).  
Day-to-day loop (run → change → verify → commit/push): [`docs/14-developer-workflow.md`](docs/14-developer-workflow.md).

## Stack (scaffolding defaults)

| Package | Stack |
| --- | --- |
| `shared-core` | Python package (uv workspace) |
| `backend-core` | FastAPI + uv |
| `agent-service` | FastAPI + LangGraph stub + uv |
| `frontend-dashboard` | Vite + React |
| `chat-widget` | Vite library (`widget.js`) |
| Data | Postgres (pgvector image) + Qdrant |
| Storage | Local filesystem via `StorageService` |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose)
- Git
- Optional on host: [uv](https://docs.astral.sh/uv/) for running Python tests outside containers; Node 20+ for frontend work outside containers

## Day-1 local bring-up

```bash
cp .env.example .env
# optional: set LLM_API_KEY (stub chat does not call an LLM yet)
# optional: set COMPOSE_ATTACH_*=false to hide noisy service logs

docker compose up --build
```

| Service | URL |
| --- | --- |
| Dashboard | http://localhost:3000 |
| Chat widget host | http://localhost:4000 |
| Control plane health | http://localhost:8080/health |
| Agent health | http://localhost:8000/health |
| Agent stub chat | `POST http://localhost:8000/api/v1/chat` |
| Postgres | `localhost:5432` |
| Qdrant | http://localhost:6333 |

Edit code on the host; Python/Node services hot-reload via bind mounts.

## uv virtualenvs (Python DX)

This repo is a **uv workspace**. Root [`pyproject.toml`](pyproject.toml) members: `shared-core`, `backend-core`, `agent-service`.

**Preferred day-to-day path:** run services in Compose (Linux venvs inside images at `/opt/venv`, so bind mounts do not wipe dependencies).

**Host-side Python (tests/lint/IDE):**

```bash
# from repo root
uv sync --all-packages --all-groups
uv run pytest
uv run black shared-core backend-core agent-service
uv run flake8 shared-core/src backend-core/src agent-service/src \
  shared-core/tests backend-core/tests agent-service/tests --max-line-length=88
```

`uv sync` creates a root `.venv` and installs workspace packages (editable). Use `uv run …` rather than activating manually unless you prefer `source .venv/bin/activate` / `.venv\Scripts\activate`.

Install a new dependency into a member:

```bash
uv add --package backend-core <package>
# or from that directory:
cd backend-core && uv add <package>
```

Inside a running container (matches prod Linux):

```bash
docker compose exec backend-core uv add --package backend-core <package>
docker compose exec agent-service uv add --package agent-service <package>
```

Commit the updated `uv.lock` after dependency changes.

## Smoke checks

```bash
curl -s http://localhost:8080/health
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "content-type: application/json" \
  -d "{\"message\":\"hello\",\"session_id\":\"demo\"}"
```

## CI

PR checks are defined in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) (lint, Compose build, in-container pytest). See [`docs/13-github-actions-pr-checks.md`](docs/13-github-actions-pr-checks.md).

## What this scaffold intentionally omits

- Real RAG chunk/embed pipeline
- Real LLM-backed LangGraph graph (echo stub only)
- Auth beyond Phase 1 `TENANT_ID` middleware
- Redis, LocalStack, workers, multi-tenant gateway
- Production registry/deploy (see [`docs/06-cicd-and-images.md`](docs/06-cicd-and-images.md))
