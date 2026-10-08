# AI Support Agent Platform

Phase 1 monorepo: Docker Compose local stack, shared tenant/storage/vector contracts, and stub services.

| Doc | Use it for |
| --- | --- |
| [`docs/developer/workflow.md`](docs/developer/workflow.md) | **Canonical runbook** — run → change → verify → commit/push |
| [`docs/README.md`](docs/README.md) | Architecture + docs index |
| Package `README.md` files | Per-service role, APIs, and DX |

## Stack

| Package | Stack | Guide |
| --- | --- | --- |
| `shared-core` | Python (uv workspace) | [`shared-core/README.md`](shared-core/README.md) |
| `backend-core` | FastAPI + SQLAlchemy + Alembic | [`backend-core/README.md`](backend-core/README.md) |
| `agent-service` | FastAPI + LangGraph stub | [`agent-service/README.md`](agent-service/README.md) |
| `frontend-dashboard` | Vite + React | [`frontend-dashboard/README.md`](frontend-dashboard/README.md) |
| `chat-widget` | Vite library (`widget.js`) | [`chat-widget/README.md`](chat-widget/README.md) |
| Data | Postgres (pgvector-enabled image) + **Qdrant** for vectors | — |
| Storage | Local filesystem via `StorageService` | — |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose)
- Git
- Optional on host: [uv](https://docs.astral.sh/uv/) for Python tests/lint; Node 20+ for frontend work outside containers

## Day-1 bring-up

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
| Control plane | http://localhost:8080/health |
| Agent | http://localhost:8000/health |
| Postgres | `localhost:5432` |
| Qdrant | http://localhost:6333 |

Edit code on the host; Python/Node services hot-reload via bind mounts.

Smoke checks, rebuilds, deps, migrations, lint/test, git/PR: [`docs/developer/workflow.md`](docs/developer/workflow.md).

## CI

PR checks: [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Notes: [`docs/ci/github-actions-pr-checks.md`](docs/ci/github-actions-pr-checks.md).

## What this scaffold intentionally omits

- Real RAG chunk/embed pipeline
- Real LLM-backed LangGraph graph (echo stub only)
- Auth beyond Phase 1 `TENANT_ID` middleware
- Redis, LocalStack, workers, multi-tenant gateway
- Production registry/deploy (see [`docs/ci/cicd-and-images.md`](docs/ci/cicd-and-images.md))
