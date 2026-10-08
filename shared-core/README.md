# shared-core

**Audience:** Junior developers changing contracts used by more than one Python service.  
**Stack:** Python 3.12 package (uv workspace member).  
**Not a running server** — imported by `backend-core` and `agent-service`.

## What is this package?

`shared-core` is the **shared contracts library**. It exists so the control plane and the agent do not invent two different ways to talk about tenants, files, and vectors.

Put code here when **both** (or eventually many) services need the same:

- interface / ABC (what operations exist)
- schema (request-scoped tenant identity, shared models)
- Phase 1 provider implementation (local disk, Qdrant client wrapper)

| You own | You do not own |
| --- | --- |
| Storage / vector interfaces | FastAPI routes |
| Tenant schemas used across services | LangGraph graph nodes |
| Swappable providers (`local` today, `s3` later) | React / widget UI |

Why this exists: [docs/architecture/interfaces-and-shared-core.md](../docs/architecture/interfaces-and-shared-core.md).  
Multi-tenant rules: [docs/architecture/phased-delivery-strategy.md](../docs/architecture/phased-delivery-strategy.md).

## Current features (scaffold)

| Area | Module | What it does |
| --- | --- | --- |
| Tenant schema | `schemas/tenant.py` | `TenantContext` with `tenant_id` |
| Storage interface | `interfaces/storage.py` | `StorageService`: `upload_file`, `get_presigned_url` |
| Vector interface | `interfaces/vector_store.py` | `VectorStoreService`: `upsert_embeddings`, `similarity_search` (must take `tenant_id`) |
| Local storage provider | `providers/local_storage.py` | Phase 1 filesystem implementation |
| Qdrant provider | `providers/qdrant_vector.py` | Phase 1 vector store + healthcheck |
| Tests | `tests/test_local_storage.py` | Covers local storage behavior |

Package version: `0.1.0` (`shared_core.__version__`).

## Planned features

Near-term Phase 1 work:

1. **Harden Qdrant provider** — Full upsert/search with forced `payload["tenant_id"]` filters.
2. **Richer shared schemas** — Document metadata, chat message DTOs only when **both** services need them.
3. **Provider factory helpers** — Optional `get_storage(settings)` shared helper if duplication grows.
4. **More tests** — Vector tenant-filter invariants (upsert always stamps tenant; search always filters).

Phase 2:

- `S3StorageProvider` behind the same `StorageService` interface (`STORAGE_PROVIDER=s3`).
- Possible alternate vector backends — keep call sites on the interface.

**Do not** dump service-specific business logic here (e.g. FastAPI routers, LangGraph nodes, React components).

## Integration dependencies

```text
backend-core ──imports──► shared-core ◄──imports── agent-service
                              │
                              ├── LocalStorageProvider ──► local filesystem
                              └── QdrantVectorStore ────► Qdrant
```

| Consumed by | What they use |
| --- | --- |
| `backend-core` | `TenantContext`, `LocalStorageProvider`, `QdrantVectorStore` (upload + health) |
| `agent-service` | `QdrantVectorStore` (health today; retrieval tools next) |

| Downstream systems (via providers) | Notes |
| --- | --- |
| Local filesystem | Phase 1 object storage |
| Qdrant | Phase 1 vector DB |

Frontends (`frontend-dashboard`, `chat-widget`) do **not** import `shared-core`.

### Workspace wiring

Root `pyproject.toml` lists `shared-core` as a uv workspace member. Downstream packages declare:

```toml
dependencies = ["shared-core", ...]

[tool.uv.sources]
shared-core = { workspace = true }
```

After you change `shared-core`, rebuild/restart services that import it so containers pick up the editable install:

```bash
docker compose up -d --build backend-core agent-service
```

## How to develop

Day-to-day loop: [docs/developer/workflow.md](../docs/developer/workflow.md).

### 1. You usually do not “run” this package alone

There is no HTTP port. You change code, then run **tests** and exercise it through `backend-core` / `agent-service`.

### 2. Where to put code

```text
shared-core/
├── src/shared_core/
│   ├── interfaces/     # ABCs — stable contracts
│   ├── schemas/        # pydantic / shared models
│   └── providers/      # concrete Phase 1 (and later Phase 2) implementations
└── tests/
```

Junior tip:

- Changing an **interface** method signature is a **breaking change** for both services — update callers in the same PR.
- Prefer adding a method to the ABC + both providers + tests over sneaking a one-off Qdrant call into `agent-service`.

### 3. Add a dependency to shared-core

Only add deps that belong in the shared layer (e.g. a vector client used by the provider):

```bash
# from repo root
uv add --package shared-core <package>
docker compose up -d --build backend-core agent-service
```

Commit `uv.lock`.

### 4. Verify your change

```bash
uv sync --all-packages --all-groups
uv run pytest shared-core
uv run black shared-core
uv run flake8 shared-core/src shared-core/tests --max-line-length=88

# still exercise consumers
uv run pytest backend-core agent-service
curl -s http://localhost:8080/health
curl -s http://localhost:8000/health
```

### 5. Rules that matter on every PR

1. Vector APIs MUST take `tenant_id` and enforce it inside the provider (stamp on write, filter on read).
2. Feature code in other packages MUST call interfaces/providers — not raw SDKs — for storage/vector.
3. Keep this package small and boring: contracts + providers + schemas, not product features.
4. If only one service needs a type, it probably belongs in that service until a second consumer appears.
