# Architecture Docs Library

**Purpose:** Canonical architecture and developer-workflow guidance for the AI support-agent platform.  
**Audience:** Project owner and LLMs used as coding/architecture context.  
**Status:** Settled direction with explicit open decisions.

## Provenance

Extrapolated from [`../inititalArchitectureResearch.txt`](../inititalArchitectureResearch.txt) (Gemini research chat). Prefer these docs over the raw chat. The chat is provenance only.

## How to use with LLMs

Load a small set of docs for the task. Do not dump the entire library unless auditing architecture end-to-end.

| Task | Load |
| --- | --- |
| Scaffold Phase 1 monorepo / Compose | [02](02-phased-delivery-strategy.md), [05](05-phase1-monorepo-and-compose.md), [09](09-interfaces-and-shared-core.md), [12](12-open-decisions.md) |
| Local DX / Docker questions | [03](03-local-development.md), [04](04-docker-and-compose.md), [05](05-phase1-monorepo-and-compose.md) |
| RAG ingestion or chat runtime | [07](07-rag-and-data-flow.md), [09](09-interfaces-and-shared-core.md), [08](08-multi-tenancy-and-isolation.md) |
| Multi-tenancy / isolation | [08](08-multi-tenancy-and-isolation.md), [02](02-phased-delivery-strategy.md), [09](09-interfaces-and-shared-core.md) |
| CI/CD / images | [06](06-cicd-and-images.md), [04](04-docker-and-compose.md) |
| PR checks / GitHub Actions | [13](13-github-actions-pr-checks.md), [05](05-phase1-monorepo-and-compose.md), [06](06-cicd-and-images.md) |
| Phase 2 / scaling | [10](10-scaling-platform.md), [11](11-scaling-backend.md), [02](02-phased-delivery-strategy.md) |
| Product / system overview | [01](01-product-and-architecture.md) |
| Unresolved stack choices | [12](12-open-decisions.md) |

**LLM rules when using these docs:**

- Treat `MUST` / `MUST NOT` as invariants.
- Treat items in [12-open-decisions.md](12-open-decisions.md) as undecided unless the user overrides.
- Python ABC snippets in [09](09-interfaces-and-shared-core.md) define **interface shape**, not a language choice.
- Prefer later Phase 1 plan (local FS + Qdrant + Postgres + `shared-core`) over older LocalStack-only drafts mentioned in the raw chat.

## Library map

| Doc | One-line summary |
| --- | --- |
| [01-product-and-architecture.md](01-product-and-architecture.md) | Product shape and production topology |
| [02-phased-delivery-strategy.md](02-phased-delivery-strategy.md) | Phase 1 vs Phase 2; multi-tenant abstraction |
| [03-local-development.md](03-local-development.md) | How developers write and run code with Docker |
| [04-docker-and-compose.md](04-docker-and-compose.md) | Multi-stage images and Compose concepts |
| [05-phase1-monorepo-and-compose.md](05-phase1-monorepo-and-compose.md) | Canonical Phase 1 tree and Compose services |
| [06-cicd-and-images.md](06-cicd-and-images.md) | Build, registry, deploy sketch |
| [07-rag-and-data-flow.md](07-rag-and-data-flow.md) | Ingestion + runtime RAG flows |
| [08-multi-tenancy-and-isolation.md](08-multi-tenancy-and-isolation.md) | Siloed compute, pooled data, tenant context |
| [09-interfaces-and-shared-core.md](09-interfaces-and-shared-core.md) | Storage, vector, LangGraph, middleware contracts |
| [10-scaling-platform.md](10-scaling-platform.md) | How non-agent layers scale in Phase 2 |
| [11-scaling-backend.md](11-scaling-backend.md) | Stateless control plane, HPA, async workers |
| [12-open-decisions.md](12-open-decisions.md) | Unresolved choices, gaps, provisional scaffolding notes |
| [13-github-actions-pr-checks.md](13-github-actions-pr-checks.md) | PR lint/build/test via Actions + local dry-run + minute limits |

## Settled vs open (summary)

**Settled**

- Docker for local + production parity on a multi-service stack.
- Monorepo split: `backend-core`, `agent-service`, `frontend-dashboard`, `chat-widget`, `shared-core`.
- Phase 1: local Compose; only cloud dependency is LLM inference.
- Strategy: single-tenant runtime with multi-tenant abstractions (`tenant_id`, storage/vector interfaces).
- Phase 2: siloed LangGraph pods on EKS; pooled Postgres + vector with `tenant_id` filters; S3 for files.
- RAG: ingestion on control plane; retrieval on agent; never search without tenant filter.

**Open**

- Languages/frameworks, vector DB final choice, frontend framework, CI product, IDE workflow, auth token model, and several Phase 2 implementation details — see [12-open-decisions.md](12-open-decisions.md).
