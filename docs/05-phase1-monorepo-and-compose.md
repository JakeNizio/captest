# Phase 1 Monorepo and Compose

**Purpose:** Canonical Phase 1 directory layout and local Compose topology.  
**Audience:** Humans and LLMs scaffolding the repo.  
**Status:** Phase 1 plan (settled structure). Language manifests (`package.json` vs `requirements.txt`) remain open.

## Canonical directory tree

```text
my-ai-agent-platform/
├── .github/workflows/         # Future CI/CD pipelines
├── shared-core/               # Shared schemas, abstractions, interfaces
│   ├── interfaces/
│   │   ├── storage.py         # StorageService shape (language illustrative)
│   │   └── vector_store.py    # VectorStoreService shape
│   └── schemas/
│       └── tenant.py          # Tenant context schemas
├── backend-core/              # Control plane API
│   ├── src/
│   ├── Dockerfile
│   └── package.json / requirements.txt
├── agent-service/             # LangGraph chat runtime
│   ├── src/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend-dashboard/        # Business UI
│   ├── Dockerfile
│   └── package.json
├── chat-widget/               # Embeddable widget
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

`shared-core` is required so storage/vector/tenant contracts are not duplicated between `backend-core` and `agent-service`. Contracts: [09-interfaces-and-shared-core.md](09-interfaces-and-shared-core.md).

## Service map (local URLs)

| Service | Role | Host port |
| --- | --- | --- |
| `db` | Postgres + pgvector image | `5432` |
| `vector-db` | Qdrant | `6333` |
| `backend-core` | Control plane / ingestion | `8080` |
| `agent-service` | LangGraph runtime | `8000` |
| `dashboard-ui` | Business dashboard | `3000` |
| `chat-widget` | Widget dev server | `4000` |

## Canonical Phase 1 `docker-compose.yml`

This is the normative Phase 1 stack: **local filesystem storage** + **Postgres** + **Qdrant**. Do not treat the older LocalStack-heavy draft in the research chat as current.

```yaml
version: '3.8'
services:
  db:
    image: ankane/pgvector:v0.5.1
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: platform_admin
      POSTGRES_PASSWORD: local_secure_password
      POSTGRES_DB: core_platform
    volumes:
      - pg_data:/var/lib/postgresql/data

  vector-db:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  backend-core:
    build:
      context: ./backend-core
      target: development
    ports:
      - "8080:8080"
    volumes:
      - ./backend-core:/app
      - /app/node_modules  # Node example; omit or adapt for non-Node
    environment:
      - DATABASE_URL=postgresql://platform_admin:local_secure_password@db:5432/core_platform
      - VECTOR_DB_URL=http://vector-db:6333
      - STORAGE_PROVIDER=local
      - LOCAL_STORAGE_PATH=/app/storage
      - TENANT_ID=default_tenant
    depends_on:
      - db
      - vector-db

  agent-service:
    build:
      context: ./agent-service
      target: development
    ports:
      - "8000:8000"
    volumes:
      - ./agent-service:/app
    environment:
      - VECTOR_DB_URL=http://vector-db:6333
      - LLM_API_KEY=your_actual_openai_or_anthropic_key_here
      - TENANT_ID=default_tenant
    depends_on:
      - vector-db

  dashboard-ui:
    build:
      context: ./frontend-dashboard
      target: development
    ports:
      - "3000:3000"
    volumes:
      - ./frontend-dashboard:/app

  chat-widget:
    build:
      context: ./chat-widget
      target: development
    ports:
      - "4000:4000"
    volumes:
      - ./chat-widget:/app

volumes:
  pg_data:
  qdrant_data:
```

## Required Phase 1 env semantics

| Variable | Meaning |
| --- | --- |
| `TENANT_ID=default_tenant` | Static tenant for all local requests |
| `STORAGE_PROVIDER=local` | Use local FS implementation of `StorageService` |
| `LOCAL_STORAGE_PATH` | Root path for tenant-prefixed files |
| `VECTOR_DB_URL` | Qdrant HTTP endpoint |
| `DATABASE_URL` | Postgres DSN (Compose DNS hostname `db`) |
| `LLM_API_KEY` | Only required cloud secret in Phase 1 |

## Intentionally not in Phase 1 Compose

- LocalStack / S3 mock (local FS is canonical)
- Nginx/Traefik multi-tenant gateway mock
- Redis (unless later added for sessions)
- Dedicated `backend-worker` service (optional; see open decisions)

## Notes for scaffolders

- `package.json` vs `requirements.txt` in the tree are placeholders — choose stacks via [12-open-decisions.md](12-open-decisions.md).
- pgvector-only (no Qdrant) remains a valid alternative; if chosen, remove `vector-db` and point vector ops at Postgres.
- Mount or package `shared-core` into `backend-core` and `agent-service` builds once language packaging is decided.
