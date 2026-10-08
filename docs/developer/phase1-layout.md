# Phase 1 Layout and Compose

**Purpose:** As-built Phase 1 directory layout and local Compose topology.  
**Audience:** Humans and LLMs working in this monorepo.  
**Status:** Matches the current scaffold. Normative Compose file is the repo-root [`docker-compose.yml`](../../docker-compose.yml) — do not treat embedded YAML elsewhere as source of truth.

## Directory tree

```text
Capstone/
├── .github/workflows/ci.yml   # PR lint / Compose build / in-container pytest
├── pyproject.toml             # uv workspace root
├── uv.lock
├── docker-compose.yml
├── shared-core/               # Shared schemas, storage/vector interfaces + Phase 1 providers
│   ├── src/shared_core/
│   └── tests/
├── backend-core/              # FastAPI control plane (SQLAlchemy + Alembic)
│   ├── src/backend_core/
│   ├── alembic/
│   ├── Dockerfile             # context: repo root
│   └── tests/
├── agent-service/             # FastAPI + LangGraph stub
│   ├── src/agent_service/
│   ├── Dockerfile             # context: repo root
│   └── tests/
├── frontend-dashboard/        # Vite + React
│   ├── Dockerfile
│   └── …
├── chat-widget/               # Vite library (`widget.js`)
│   ├── Dockerfile
│   └── …
└── docs/
```

`shared-core` is required so storage/vector/tenant contracts are not duplicated between `backend-core` and `agent-service`. Contracts: [interfaces-and-shared-core.md](../architecture/interfaces-and-shared-core.md).

Python packaging: uv workspace members `shared-core`, `backend-core`, `agent-service`. Frontends use npm in their own directories.

## Service map (local URLs)

| Service | Role | Host port |
| --- | --- | --- |
| `db` | Postgres (`pgvector`-enabled image; relational data) | `5432` |
| `vector-db` | Qdrant (embeddings live here, not in Postgres) | `6333` |
| `backend-core` | Control plane / ingestion | `8080` |
| `agent-service` | LangGraph runtime (stub chat) | `8000` |
| `dashboard-ui` | Business dashboard | `3000` |
| `chat-widget` | Widget dev server | `4000` |

Day-to-day bring-up: [workflow.md](workflow.md).

## Compose facts (as built)

- **Storage:** `STORAGE_PROVIDER=local` + named volume `backend_storage` (not LocalStack).
- **Python images:** build context is the **repo root** so `shared-core` and the uv workspace install correctly; Dockerfiles live under each service folder.
- **Frontends:** build context is the package directory; anonymous `/app/node_modules` volumes avoid host OS clashes.
- **Migrations:** `backend-core` applies Alembic on startup and seeds `default_tenant`.
- **Log filters:** `COMPOSE_ATTACH_*` env vars (see `.env.example`).

## Required Phase 1 env semantics

| Variable | Meaning |
| --- | --- |
| `TENANT_ID=default_tenant` | Static tenant for all local requests |
| `STORAGE_PROVIDER=local` | Local FS implementation of `StorageService` |
| `LOCAL_STORAGE_PATH` | Root path for tenant-prefixed files |
| `VECTOR_DB_URL` | Qdrant HTTP endpoint |
| `DATABASE_URL` | Postgres DSN (Compose DNS hostname `db`) |
| `LLM_API_KEY` | Only required cloud secret in Phase 1 (stub chat may omit) |

## Intentionally not in Phase 1 Compose

- LocalStack / S3 mock (local FS is canonical)
- Nginx/Traefik multi-tenant gateway mock
- Redis
- Dedicated `backend-worker` service (in-process tasks OK until forced otherwise)

Open Phase 2 / auth items: [open-decisions.md](../architecture/open-decisions.md).
