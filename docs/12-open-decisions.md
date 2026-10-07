# Open Decisions

**Purpose:** Capture unresolved stack and design choices so normative docs do not freeze Gemini examples as decisions.  
**Audience:** Humans deciding the stack; LLMs scaffolding MUST treat these as undecided unless a **Provisional scaffolding default** is used and labeled.  
**Status:** Open.

## How to use this file

- Settled architecture lives in docs `01`–`11`.
- Items here are **not decided**.
- **Provisional scaffolding default** = temporary pick so an LLM/human can generate boilerplate. Replace when the team decides. Never treat as final without explicit confirmation.

## Stack choices

### Control plane language / framework

| Options from research | Notes |
| --- | --- |
| FastAPI (Python) | Same language as LangGraph-friendly agent |
| Express / NestJS (Node) | Node examples appear often in Docker snippets |

**Provisional scaffolding default:** FastAPI for `backend-core` if generating a full-stack stub (keeps one language with agent). Confirm before committing.

### Agent language / framework

LangGraph strongly implies **Python** for `agent-service`.

**Provisional scaffolding default:** Python + LangGraph + FastAPI (or equivalent ASGI) HTTP wrapper.

### Vector store (Phase 1)

| Option | Notes |
| --- | --- |
| Postgres + Qdrant | Canonical in [05-phase1-monorepo-and-compose.md](05-phase1-monorepo-and-compose.md) |
| pgvector only | Earlier research draft used pgvector image alone; simpler ops |

**Provisional scaffolding default:** Postgres + Qdrant (matches canonical Compose). pgvector-only remains a valid simplification.

### Frontend dashboard

Options mentioned: Next.js, Vite/React.

**Provisional scaffolding default:** Vite + React for a lightweight dashboard unless SSR/auth needs push toward Next.

### Chat widget bundling

Embed via script tag or iframe; exact public API/events not specified.

**Provisional scaffolding default:** Vite library build producing a single `widget.js`.

### CI product

GitHub Actions (`.github/workflows/` in tree) vs GitLab CI.

**Provisional scaffolding default:** GitHub Actions (matches directory placeholder). Workflow shape, implementation checklist, and free-tier minute notes: [13-github-actions-pr-checks.md](13-github-actions-pr-checks.md).

### IDE / DX path

VS Code Dev Containers vs traditional bind mounts + any IDE.

**Provisional scaffolding default:** Bind mounts + Compose (works for any editor); add Dev Container config later if the team is VS Code-centric.

## Phase 1 infra forks

### LocalStack vs local filesystem

| Draft | Storage approach |
| --- | --- |
| Older research Compose | LocalStack S3 mock |
| Later Phase 1 plan (canonical) | `STORAGE_PROVIDER=local` + FS path |

**Decision for docs:** Canonical = local FS. LocalStack is optional later if S3 API parity is needed before AWS.

### Redis in Phase 1

Not in canonical Compose. Phase 2 wants Redis/ElastiCache for sessions.

**Provisional scaffolding default:** Omit Redis in Phase 1; keep session design swappable. Add Compose Redis when auth sessions need it.

### Dedicated worker service in Phase 1

Phase 2: SQS + `backend-worker`. Phase 1: in-process background tasks acceptable.

**Provisional scaffolding default:** No separate worker service until ingestion latency/timeouts force it.

### Local multi-tenant gateway mock

Nginx/Traefik header router proposed in research; **not** in Phase 1 Compose.

**Provisional scaffolding default:** Skip until multi-tenant local testing is required.

## Phase 2 choices still open

| Topic | Options mentioned |
| --- | --- |
| Managed vector | Qdrant Cloud, Pinecone, AWS OpenSearch |
| Ingress / gateway | Traefik, Nginx, Kong, Envoy, API Gateway |
| Agent checkpointer | SQLite vs Redis per pod |
| Tenant provisioning | Helm chart vs K8s CRD; control-plane K8s IAM design |
| Hosting for dashboard | S3/CloudFront vs Vercel |
| Queue | SQS, RabbitMQ, Redis queues |
| Worker scaling | HPA vs KEDA on queue depth |

No provisional defaults required until Phase 2 planning starts — prefer deciding with load/cost constraints.

## Auth and API keys (gap)

Research sketches:

- Dashboard: JWT sessions.
- Widget: public API key → tenant routing at ingress.

Still unspecified: token claims shape, key rotation, scopes, secret storage, widget auth abuse controls.

**MUST NOT** invent a full auth system in scaffolding beyond a stub middleware that sets `tenant_id` from env (Phase 1).

## Documented gaps (discussed lightly or not at all)

| Gap | Impact |
| --- | --- |
| Observability | No logging/metrics/tracing/LLM cost controls defined |
| Migrations / seeding | Named DB volumes only; no migration tool chosen |
| Testing strategy | PR Compose CI sketched in [13](13-github-actions-pr-checks.md); still no RAG isolation / e2e matrix |
| Widget public API contract | Ports/CDN noted; no events/embed snippet contract |
| Health/readiness | Recommended in scaling doc; not in Compose yet |
| Packaging `shared-core` | Need language-specific install path into both services |

## Chat contradictions (resolved for normative docs)

| Conflict | Resolution used in docs `01`–`11` |
| --- | --- |
| LocalStack Compose vs local FS | Local FS + `STORAGE_PROVIDER=local` |
| pgvector-only vs Postgres+Qdrant | Document Qdrant+Postgres as Phase 1 example; list pgvector-only here |
| Monorepo without vs with `shared-core` | **With** `shared-core` |
| Node-centric Dockerfile examples vs Python agent | Examples are illustrative; stacks open |

## Decision log (fill in as the team decides)

| Date | Decision | Chosen option | Notes |
| --- | --- | --- | --- |
| | | | |
