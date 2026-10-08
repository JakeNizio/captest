# Open Decisions

**Purpose:** Capture choices that are still unresolved so normative docs do not freeze research brainstorming as decisions.  
**Audience:** Humans deciding next product/infra steps; LLMs MUST treat items here as undecided unless the user overrides.  
**Status:** Phase 1 stack is settled (see decision log). This file tracks remaining gaps.

## How to use this file

- Settled Phase 1 architecture and layout live under `docs/architecture/` and `docs/developer/`.
- Items under **Still open** and **Documented gaps** are **not decided**.
- Do **not** re-open settled Phase 1 stack choices from the research chat.

## Settled for Phase 1 (do not re-litigate)

| Topic | Choice |
| --- | --- |
| Control plane | FastAPI + SQLAlchemy + Alembic (`backend-core`) |
| Agent runtime | Python + LangGraph stub + FastAPI (`agent-service`) |
| Packaging | uv workspace (`shared-core`, `backend-core`, `agent-service`) |
| Vector / DB | Postgres + Qdrant; local FS storage (vectors in Qdrant, not Postgres) |
| Frontends | Vite + React (`frontend-dashboard`, `chat-widget` → `widget.js`) |
| CI product | GitHub Actions (`.github/workflows/ci.yml`) |
| Local DX default | Bind mounts + Compose (Dev Containers optional) |
| Storage mock | Local FS — not LocalStack |
| Redis / worker / gateway in Phase 1 | Omitted |
| App health path | `GET /health` on control plane and agent |

Layout detail: [phase1-layout.md](../developer/phase1-layout.md). PR CI: [github-actions-pr-checks.md](../ci/github-actions-pr-checks.md).

## Still open — product / auth

Research sketches:

- Dashboard: JWT sessions.
- Widget: public API key → tenant routing at ingress.

Still unspecified: token claims shape, key rotation, scopes, secret storage, widget auth abuse controls.

**MUST NOT** invent a full auth system beyond Phase 1 stub middleware that sets `tenant_id` from env (`TENANT_ID`).

## Still open — Phase 2 infra

| Topic | Options mentioned |
| --- | --- |
| Managed vector | Qdrant Cloud, Pinecone, AWS OpenSearch |
| Ingress / gateway | Traefik, Nginx, Kong, Envoy, API Gateway |
| Agent checkpointer | SQLite vs Redis per pod |
| Tenant provisioning | Helm chart vs K8s CRD; control-plane K8s IAM design |
| Hosting for dashboard | S3/CloudFront vs Vercel |
| Queue | SQS, RabbitMQ, Redis queues |
| Worker scaling | HPA vs KEDA on queue depth |
| LLM provider | OpenAI / Anthropic / other behind `LLM_API_KEY` |
| K8s probe paths | Whether to add `/healthz` / `/readyz` beside `/health` |

No provisional defaults required until Phase 2 planning starts — prefer deciding with load/cost constraints.

## Documented gaps

| Gap | Impact |
| --- | --- |
| Observability | No logging/metrics/tracing/LLM cost controls defined |
| Testing strategy | PR Compose CI exists; still no RAG isolation / e2e matrix |
| Widget public API contract | Ports/CDN noted; no events/embed snippet contract |
| Richer readiness probes | `/health` is settled; probe split for load balancers not specified |

Migrations / seeding and `shared-core` packaging via uv workspace are **settled** for the scaffold (not gaps).

## Decision log

| Date | Decision | Chosen option | Notes |
| --- | --- | --- | --- |
| 2026-10-07 | Phase 1 scaffolding defaults | FastAPI + LangGraph + Vite/React + Qdrant + GHA | Confirmed; Python packaging via uv workspace |
| 2026-10-08 | Docs reorg | Foldered `architecture` / `developer` / `ci` | Dropped flat `01`–`14` numbering; [workflow.md](../developer/workflow.md) is the single runbook |
| 2026-10-08 | Docs clarity pass | Single CI source of truth; thinned duplicates | Normative contracts in interfaces; omit list only in phase1-layout |

## Appendix — resolved research-chat conflicts

Historical only. Do not treat as open options.

| Conflict | Resolution |
| --- | --- |
| LocalStack Compose vs local FS | Local FS + `STORAGE_PROVIDER=local` |
| pgvector-only vs Postgres+Qdrant | Postgres + Qdrant for Phase 1 (vectors in Qdrant) |
| Monorepo without vs with `shared-core` | **With** `shared-core` |
| Node-centric examples vs Python agent | Python for backend/agent; Node for frontends only |
