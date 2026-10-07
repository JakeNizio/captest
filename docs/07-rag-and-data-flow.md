# RAG and Data Flow

**Purpose:** Define ingestion and runtime RAG paths across control plane and agent.  
**Audience:** Humans and LLMs implementing document upload, embedding, or chat retrieval.  
**Status:** Settled flow and security invariants. Embedding provider and vector product details are open.

## Split responsibility

| Phase | Owner | Job |
| --- | --- | --- |
| Ingestion | `backend-core` (control plane) | Upload → store → chunk → embed → upsert with `tenant_id` |
| Runtime query | `agent-service` (LangGraph) | Intent → retrieve (tenant-filtered) → memory → synthesize → stream |

MUST NOT let the browser talk directly to vector DB credentials. MUST NOT run similarity search without a tenant filter.

## Ingestion pipeline

```text
[Dashboard UI] --upload--> [backend-core]
                              |-- StorageService.upload_file(..., tenant_id)
                              |-- chunk text
                              |-- embed chunks (LLM/embedding API)
                              |-- VectorStoreService.upsert_embeddings(..., tenant_id)
```

### Steps

1. **Auth + tenant** — Resolve `tenant_id` (Phase 1: env `TENANT_ID`; Phase 2: JWT/session).
2. **Store raw file** — Via `StorageService` under a tenant-prefixed path.
3. **Chunk & embed** — Control plane owns chunking/embedding for uploads.
4. **Upsert** — Every vector payload MUST include `tenant_id` (and useful metadata such as `source_file`, `text_content`).

Example payload shape:

```json
{
  "vector": [0.134, -0.432],
  "payload": {
    "tenant_id": "tenant-123",
    "text_content": "Our return policy lasts exactly 30 days...",
    "source_file": "policy.pdf"
  }
}
```

Heavy ingestion SHOULD eventually be async (202 + worker). Phase 1 may use in-process background tasks; Phase 2 uses a queue — see [11-scaling-backend.md](11-scaling-backend.md).

## Runtime query loop

```text
[Customer page]
  -> [Chat Widget] (query + public API token)
  -> [Ingress / agent entry]
  -> [LangGraph agent for tenant]
       1. Intent node (skip retrieval for pure chitchat if desired)
       2. Retrieval tool: VectorStoreService.similarity_search(..., tenant_id)
       3. Memory checkpointer (thread/session)
       4. Synthesis LLM node
       5. Stream tokens (SSE or WebSocket) back to widget
```

### Step details

1. **Ingress (Phase 2)** — Validate widget API key, map to tenant, route to that tenant's pod.
2. **LangGraph** — Pass `configurable.tenant_id` and `thread_id` on every run.
3. **Retrieval guardrail** — Agent injects its tenant into the vector filter (`tenant_id == <self>`). Cross-tenant nearest neighbors MUST be dropped by metadata filter before results return.
4. **Memory** — Checkpointer scoped to the agent/session (SQLite vs Redis open).
5. **Stream** — Tokens leave via SSE or WebSocket to the widget.

Phase 1 local mock: single `agent-service` with static `TENANT_ID=default_tenant`; no per-tenant pods.

## Security invariants

- MUST attach `tenant_id` on every upsert.
- MUST filter by `tenant_id` on every similarity search.
- Agent pods SHOULD only know their own tenant identity in Phase 2 (no master cross-tenant credentials in the agent).
- Shared vector cluster is allowed; isolation is logical via metadata (and later Postgres RLS for relational data).

Interfaces: [09-interfaces-and-shared-core.md](09-interfaces-and-shared-core.md).  
Tenancy model: [08-multi-tenancy-and-isolation.md](08-multi-tenancy-and-isolation.md).
