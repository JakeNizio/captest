# Phased Delivery Strategy

**Purpose:** Deliver Phase 1 without rewriting for Phase 2 multi-tenancy and AWS.  
**Audience:** Humans and LLMs scaffolding code, schemas, and env wiring.  
**Status:** Settled strategy. Phase 1 stack is implemented; Phase 2 infra choices remain in [open-decisions.md](open-decisions.md).

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

Normative API shapes and enforcement details: [interfaces-and-shared-core.md](interfaces-and-shared-core.md).

1. **`tenant_id` on all data** — Postgres tables and vector metadata include `tenant_id` in Phase 1. Env `TENANT_ID=default_tenant` supplies the value locally. Queries MUST filter by current tenant.
2. **Pass `tenant_id` into LangGraph** — Every `invoke` / `stream` MUST put `tenant_id` and `thread_id` in `configurable`. Retrieval tools read tenant from `RunnableConfig` and apply it to vector search.
3. **Decouple storage behind an interface** — MUST NOT call S3 or local FS SDKs from business logic. Use `StorageService`; toggle `STORAGE_PROVIDER` (`local` → `s3`) in Phase 2.

## Phase 1 → Phase 2 transition checklist

When Phase 2 is approved:

1. **Tenant resolution** — Remove static `TENANT_ID=default_tenant` from prod env. Middleware reads `tenant_id` from JWT / headers. Downstream signatures stay the same.
2. **Storage swap** — Set `STORAGE_PROVIDER=s3` + AWS credentials. No business-logic rewrite if Rule 3 was followed.
3. **Agent siloing** — Deploy `agent-service` image via Helm/CRD; inject per-tenant `TENANT_ID` (or equivalent) at pod launch.
4. **Data plane** — Point Postgres/vector URLs at managed services; enable RLS; keep `tenant_id` filters.
5. **Control plane scale** — Stateless API behind ALB + HPA; async workers for ingestion — see [scaling-platform.md](scaling-platform.md) and [scaling-backend.md](scaling-backend.md).

## Phase 1 Compose

Canonical services, env vars, and the intentional omit list: [phase1-layout.md](../developer/phase1-layout.md).
