# Interfaces and Shared Core

**Purpose:** Normative contracts that keep Phase 1 → Phase 2 swaps infrastructure-only.  
**Audience:** Humans and LLMs implementing `shared-core`, middleware, storage, vector, or LangGraph tools.  
**Status:** Settled contracts. Python ABCs below are **shape reference**, not a language decision.

## Why `shared-core`

`backend-core` and `agent-service` both need tenant-aware storage and vector operations. Put abstractions and shared schemas in `shared-core/` to avoid divergent copies.

```text
shared-core/
├── interfaces/
│   ├── storage.*
│   └── vector_store.*
└── schemas/
    └── tenant.*
```

## Tenant middleware behavior

| Phase | Source of `tenant_id` |
| --- | --- |
| Phase 1 | `TENANT_ID` env (`default_tenant`) |
| Phase 2 | JWT claims and/or validated headers / API keys |

Middleware MUST attach tenant to request context. Business handlers and tools MUST read from that context (or LangGraph `configurable`), not from scattered globals.

## A. `StorageService`

MUST NOT call S3/local FS SDKs from feature code. Call this interface.

Shape reference (Python ABC — illustrative):

```python
from abc import ABC, abstractmethod
from typing import BinaryIO

class StorageService(ABC):
    @abstractmethod
    async def upload_file(self, file_obj: BinaryIO, path: str, tenant_id: str) -> str:
        """Upload file; return absolute URI / identifier."""
        pass

    @abstractmethod
    async def get_presigned_url(self, path: str, tenant_id: str, expires_in: int = 3600) -> str:
        """Direct client read/write URL (local URL or S3 presign)."""
        pass
```

| Driver | When | Behavior |
| --- | --- | --- |
| `LocalStorageProvider` | Phase 1 (`STORAGE_PROVIDER=local`) | Write `/app/storage/{tenant_id}/{path}`; local download URLs |
| `S3StorageProvider` | Phase 2 (`STORAGE_PROVIDER=s3`) | `s3://bucket/{tenant_id}/{path}`; boto3 presigns |

## B. `VectorStoreService`

MUST enforce tenant metadata inside the interface so LangGraph tools cannot omit filters.

```python
class VectorStoreService(ABC):
    @abstractmethod
    async def upsert_embeddings(self, vectors: list[dict], tenant_id: str) -> bool:
        """Force payload['tenant_id'] = tenant_id before write."""
        pass

    @abstractmethod
    async def similarity_search(
        self, query_vector: list[float], tenant_id: str, top_k: int = 5
    ) -> list[dict]:
        """Always apply tenant metadata filter."""
        pass
```

| Phase | `tenant_id` passed as |
| --- | --- |
| Phase 1 | Static `default_tenant` (from env/context) |
| Phase 2 | Dynamic per request / per agent pod |

Implementation may target Qdrant, pgvector, or another store — see [12-open-decisions.md](12-open-decisions.md).

## C. LangGraph config signature

Every `invoke` / `stream` MUST pass:

```python
config = {
    "configurable": {
        "thread_id": session_id,
        "tenant_id": request_tenant_id,
    }
}
```

Retrieval tool pattern:

```python
def retrieve_documents(query: str, config: RunnableConfig):
    tenant_id = config["configurable"].get("tenant_id")
    return vector_store.similarity_search(
        query_vector=embed(query),
        tenant_id=tenant_id,
    )
```

MUST NOT hardcode tenant inside tools except by reading `configurable`.

## Phase 1 vs Phase 2 change matrix

| Component | Change today (Phase 1) | Change in Phase 2 |
| --- | --- | --- |
| DB schemas | Add `tenant_id`; plan for RLS | Point DSN at managed Postgres; enable RLS |
| API middleware | Set context from `TENANT_ID` env | Parse JWT/headers; same context field |
| Storage | `LocalStorageProvider` | Flip `STORAGE_PROVIDER=s3` |
| Vector tools | Always pass tenant into interface | Same code; dynamic tenant values |
| LangGraph tools | Read `configurable.tenant_id` | No tool signature change |

Related: [02-phased-delivery-strategy.md](02-phased-delivery-strategy.md), [07-rag-and-data-flow.md](07-rag-and-data-flow.md), [08-multi-tenancy-and-isolation.md](08-multi-tenancy-and-isolation.md).
