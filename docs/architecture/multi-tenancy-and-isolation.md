# Multi-Tenancy and Isolation

**Purpose:** Define how tenants are isolated in compute vs data, and how tenant context propagates.  
**Audience:** Humans and LLMs implementing auth middleware, schemas, or agent routing.  
**Status:** Settled model. Auth token format and gateway product are open.

Normative storage/vector/LangGraph contracts: [interfaces-and-shared-core.md](interfaces-and-shared-core.md). Strategy rules: [phased-delivery-strategy.md](phased-delivery-strategy.md).

## Isolation model

| Layer | Model | Mechanism |
| --- | --- | --- |
| Agent compute (Phase 2) | Siloed | Per-tenant EKS pod/namespace running `agent-service` |
| Postgres | Pooled | Shared DB; `tenant_id` column; Phase 2 RLS |
| Vector store | Pooled | Shared cluster; metadata filter on `tenant_id` |
| Object storage | Pooled bucket, partitioned paths | `{tenant_id}/...` prefixes via `StorageService` |

Siloed agent compute removes noisy-neighbor CPU/memory issues and keeps agent process memory separate. Data stays pooled for cost efficiency.

## Phase 1 vs Phase 2 tenant resolution

```text
[Chat Widget / Dashboard]
       |  Authorization: Bearer <JWT>  (or X-Tenant-ID in controlled environments)
       v
[Middleware / Control Plane]
       |-- Phase 1: tenant_id = env TENANT_ID (default_tenant)
       |-- Phase 2: tenant_id from JWT / validated API key
       |
       |-- SET LOCAL app.current_tenant_id = '...'   (Postgres RLS session)
       |-- Forward X-Tenant-ID (or equivalent) to agent when calling it
       v
[Agent] configurable.tenant_id -> vector filter
```

### Middleware contract

- **Phase 1:** Middleware reads `TENANT_ID` from environment and sets request context (`req.tenantId` / `request.state.tenant_id`).
- **Phase 2:** Same middleware API; implementation switches to JWT/header extraction.
- Downstream business code MUST read tenant from request context, never hardcode except via that context/env bridge.

## Database multi-tenancy (RLS)

Every tenant-owned table MUST have `tenant_id`; application queries MUST filter by current tenant (see [interfaces](interfaces-and-shared-core.md)). Phase 2 additionally enables Postgres RLS, e.g.:

```sql
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_policy ON documents
  USING (tenant_id = current_setting('app.current_tenant_id'));
```

Wrap work in a transaction that sets:

```sql
BEGIN;
SET LOCAL app.current_tenant_id = 'tenant_123';
-- queries
COMMIT;
```

Use a shared pool (PgBouncer / RDS Proxy in Phase 2), not per-tenant connection pools.

## Local multi-tenant simulation

Simulating full EKS multi-pod tenancy on a laptop is out of scope for Phase 1 Compose.

- Phase 1: one `agent-service`, static `TENANT_ID=default_tenant`.
- Optional later local mock: gateway (Nginx/Traefik) + header-based tenant switching against one agent process. **Not** in the canonical Phase 1 Compose file — see [phase1-layout.md](../developer/phase1-layout.md).

## Widget → agent routing (Phase 2)

1. Widget sends query + public API key.
2. Ingress validates key → resolves tenant.
3. Traffic routes to that tenant's LangGraph pod.
4. Pod uses its tenant identity for retrieval filters.

API key scopes, rotation, and ingress product (Traefik / Nginx / Kong) are open — [open-decisions.md](open-decisions.md).
