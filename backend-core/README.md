# backend-core

**Audience:** Junior developers working on the control plane.  
**Stack:** FastAPI + SQLAlchemy + Alembic + Python 3.12 (uv workspace member).  
**Local URL:** http://localhost:8080

## What is this package?

`backend-core` is the **control plane API** — the brain of the business side of the product.

Think of it as the service the **dashboard** talks to when a business owner:

- signs in / manages their account (planned)
- uploads knowledge-base documents for RAG
- configures their AI agent (planned)

It is **not** the chat runtime. End-customer chat goes to `agent-service`. This service prepares data and config that the agent later uses.

| You own | You do not own |
| --- | --- |
| Auth, tenants, subscriptions (planned) | Streaming chat with end users |
| Document upload + ingestion pipeline | LangGraph graph / LLM reply logic |
| Postgres schemas, migrations, admin APIs | Embeddable widget UI |

Architecture overview: [docs/architecture/product-and-architecture.md](../docs/architecture/product-and-architecture.md).  
RAG split of duties: [docs/architecture/rag-and-data-flow.md](../docs/architecture/rag-and-data-flow.md).

## Current features (scaffold)

What works today:

| Feature | Endpoint / behavior | Notes |
| --- | --- | --- |
| Health check | `GET /health` | Checks Postgres schema readiness + Qdrant |
| Tenant middleware | Attaches `TenantContext` on every request | Phase 1: `TENANT_ID` env (`default_tenant`) |
| Alembic migrations | Applied on startup (default) | Creates `tenants`, `agents`, `documents`; seeds `default_tenant` |
| Document upload | `POST /api/v1/documents` | Saves file via `StorageService` **and** inserts a `documents` row |
| DI helpers | `deps.py` / `db.py` | Storage, vector store, SQLAlchemy sessions |

Example upload (stack must be running):

```bash
curl -s -X POST http://localhost:8080/api/v1/documents \
  -F "file=@./some-doc.txt"
```

## Database schema

Postgres is owned by this package. Models live under `src/backend_core/models/`; migrations under `alembic/versions/`.

| Table | Purpose | Tenant rule |
| --- | --- | --- |
| `tenants` | Tenant registry | PK is the `tenant_id` string |
| `agents` | Per-tenant agent config rows | `tenant_id` FK + index |
| `documents` | Uploaded file metadata | `tenant_id` FK + index; bytes in object storage |

Phase 1 seed (migration `0001_initial`):

- tenant `default_tenant` / "Default Tenant"
- one "Default Agent" row for that tenant

Raw file bytes are **not** stored in Postgres — only `storage_uri` pointing at `StorageService`.

### How migrations run

1. **Automatic (Compose):** on `backend-core` startup when `RUN_MIGRATIONS_ON_STARTUP=true` (default).
2. **CLI:**

```bash
# inside Compose
docker compose exec backend-core uv run --package backend-core backend-core-migrate

# on host (Postgres on localhost:5432)
cd backend-core
uv run backend-core-migrate
```

3. **After changing models:**

```bash
cd backend-core
uv run alembic revision --autogenerate -m "add widget_tokens table"
# review alembic/versions/*.py, then:
uv run backend-core-migrate
```

Never edit an already-applied migration on a shared DB — add a new revision instead. To wipe local data: `docker compose down -v` then bring the stack back up.

## Planned features

Near-term Phase 1 work (in rough product order):

1. **Real ingestion** — After upload: chunk → embed → `VectorStoreService.upsert_embeddings(..., tenant_id)`; update `documents.status`.
2. **Dashboard APIs** — CRUD for agents/docs that `frontend-dashboard` will call.
3. **Auth stub → real auth** — Keep Phase 1 middleware simple (see [docs/architecture/open-decisions.md](../docs/architecture/open-decisions.md)).
4. **Async ingestion** — Heavy uploads may move to background tasks (later: workers).

Phase 2 (later): JWT/header tenant resolution, Postgres RLS, S3 storage provider, managed DBs. Strategy: [docs/architecture/phased-delivery-strategy.md](../docs/architecture/phased-delivery-strategy.md).

## Integration dependencies

```text
frontend-dashboard ──HTTP──► backend-core
                                │
                                ├──► Postgres (db)          tenants / agents / documents
                                ├──► Qdrant (vector-db)     embeddings (after ingestion exists)
                                ├──► Local FS via StorageService   raw uploaded files
                                └──► shared-core            interfaces + tenant schemas
```

| Depends on | Why |
| --- | --- |
| `shared-core` | `StorageService`, `VectorStoreService`, `TenantContext`, Phase 1 providers |
| Postgres (`DATABASE_URL`) | Relational metadata + Alembic migrations |
| Qdrant (`VECTOR_DB_URL`) | Vector upserts once ingestion is implemented |
| Local storage (`STORAGE_PROVIDER=local`, `LOCAL_STORAGE_PATH`) | Raw file storage in Phase 1 |

| Depends on this package | Why |
| --- | --- |
| `frontend-dashboard` | Will call control-plane APIs for config and uploads |
| (indirectly) `agent-service` | Agent retrieves vectors that **this** service will write during ingestion |

**Important:** Feature code must call `shared-core` interfaces — do **not** open S3/FS SDKs or raw Qdrant clients from random handlers. See [docs/architecture/interfaces-and-shared-core.md](../docs/architecture/interfaces-and-shared-core.md).

### Key env vars

| Variable | Default / example | Meaning |
| --- | --- | --- |
| `TENANT_ID` | `default_tenant` | Phase 1 single-tenant identity (must exist in `tenants`) |
| `DATABASE_URL` | Compose Postgres URL | Postgres connection string (`postgresql://...`) |
| `RUN_MIGRATIONS_ON_STARTUP` | `true` | Set `false` only for special cases / some unit tests |
| `VECTOR_DB_URL` | `http://vector-db:6333` | Qdrant base URL (in Compose network) |
| `STORAGE_PROVIDER` | `local` | Only `local` supported in Phase 1 |
| `LOCAL_STORAGE_PATH` | `/app/storage` | Where uploads are written inside the container |
| `PORT` | `8080` | HTTP port |

## How to develop

Day-to-day loop for the whole repo: [docs/developer/workflow.md](../docs/developer/workflow.md).

### 1. Start the stack

From the **repo root**:

```bash
docker compose up
# first time or after Dockerfile/deps change:
docker compose up --build backend-core
```

Edit files under `backend-core/` on your machine. The container bind-mounts the source and uvicorn reloads on change. Schema changes: add an Alembic revision (reload alone does **not** invent SQL).

### 2. Where to put code

```text
backend-core/
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/           # migration scripts (committed)
├── src/backend_core/
│   ├── main.py             # routes / app factory (runs migrations in lifespan)
│   ├── config.py           # env → Settings
│   ├── db.py               # engine, sessions, readiness check
│   ├── migrate.py          # alembic upgrade head helper + CLI
│   ├── middleware.py       # tenant attachment
│   ├── deps.py             # storage / vector / tenant deps
│   └── models/             # SQLAlchemy tables
└── tests/
```

Junior tip: add routes in `main.py` (or a router module), resolve tenant with `Depends(get_tenant)`, use `Depends(get_db)` for SQLAlchemy, and `get_storage` / `get_vector_store` instead of constructing clients inline. Always filter queries by `tenant_id`.

### 3. Add a Python dependency

```bash
# from repo root
uv add --package backend-core <package>
docker compose up -d --build backend-core
```

Commit the updated `uv.lock`.

### 4. Verify your change

```bash
# smoke
curl -s http://localhost:8080/health

# confirm tables (Compose)
docker compose exec db psql -U platform_admin -d core_platform -c '\dt'

# tests + lint (host; needs uv sync once)
uv sync --all-packages --all-groups
uv run pytest backend-core
uv run black backend-core
uv run flake8 backend-core/src backend-core/tests --max-line-length=88
```

### 5. Rules that matter on every PR

1. Put `tenant_id` on every new tenant-owned table/query filter — even in Phase 1.
2. Ship schema changes as Alembic revisions (not manual one-off SQL on shared DBs).
3. Use `StorageService` / `VectorStoreService` from `shared-core`, not direct SDKs.
4. Keep chat/LLM logic out of this package — that belongs in `agent-service`.
