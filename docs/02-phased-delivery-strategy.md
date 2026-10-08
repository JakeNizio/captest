# Phased Delivery Strategy

**Purpose:** Deliver Phase 1 without rewriting for Phase 2 multi-tenancy and AWS.  
**Audience:** Humans and LLMs scaffolding code, schemas, and env wiring.  
**Status:** Settled strategy. Implementation languages remain open.

## Strategy name

**Single-Tenant Architecture with Multi-Tenant Abstraction**

Build a single-tenant app now. Design schemas, APIs, and interfaces as if multi-tenancy already exists. Phase 2 becomes mostly infrastructure and middleware changes, not a ground-up rewrite.

## Phase constraints

| | Phase 1 | Phase 2 |
| --- | --- | --- |
| Tenancy | One logical tenant (`default_tenant`) | Many tenants |
| Cloud | LLM inference only | AWS (EKS, S3, managed DB/vector, etc.) |
| Runtime | Docker Compose on laptop | EKS + managed services |
| Storage | Local FS via `StorageService` | S3 provider |
| Agent compute | Single `agent-service` container | Per-tenant pods |

## Three future-proof rules (MUST)

### Rule 1: `tenant_id` on all data

- Add `tenant_id` to Postgres tables and vector metadata **in Phase 1**.
- Phase 1: hardcode via env `TENANT_ID=default_tenant`.
- Queries MUST already filter: `WHERE tenant_id = <current_tenant>`.

### Rule 2: Pass `tenant_id` into LangGraph

- Every `invoke` / `stream` MUST pass:

```python
config = {"configurable": {"tenant_id": <current_tenant_id>, "thread_id": <session_id>}}
```

- Retrieval tools MUST read `tenant_id` from `RunnableConfig` and apply it to vector search.

### Rule 3: Decouple storage behind an interface

- MUST NOT call S3 (or local FS) SDKs directly from business logic.
- Use `StorageService` with a Phase 1 local provider and a Phase 2 S3 provider toggled by `STORAGE_PROVIDER`.

Full contracts: [09-interfaces-and-shared-core.md](09-interfaces-and-shared-core.md).

## Phase 1 → Phase 2 transition checklist

When Phase 2 is approved:

1. **Tenant resolution** — Remove static `TENANT_ID=default_tenant` from prod env. Middleware reads `tenant_id` from JWT / headers. Downstream signatures stay the same.
2. **Storage swap** — Set `STORAGE_PROVIDER=s3` + AWS credentials. No business-logic rewrite if Rule 3 was followed.
3. **Agent siloing** — Deploy `agent-service` image via Helm/CRD; inject per-tenant `TENANT_ID` (or equivalent) at pod launch.
4. **Data plane** — Point Postgres/vector URLs at managed services; enable RLS; keep `tenant_id` filters.
5. **Control plane scale** — Stateless API behind ALB + HPA; async workers for ingestion — see [10-scaling-platform.md](10-scaling-platform.md) and [11-scaling-backend.md](11-scaling-backend.md).

## What Phase 1 Compose includes

Canonical services and env vars: [05-phase1-monorepo-and-compose.md](05-phase1-monorepo-and-compose.md).

Phase 1 intentionally omits: LocalStack (use local FS), multi-tenant gateway mock, Redis (unless chosen for sessions early), dedicated worker service (may use in-process background tasks initially — see [12-open-decisions.md](12-open-decisions.md)).
