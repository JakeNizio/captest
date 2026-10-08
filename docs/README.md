# Docs library

**Purpose:** Architecture and developer guidance for the AI support-agent platform.  
**Audience:** Project owner and LLMs used as coding/architecture context.  
**Status:** Phase 1 scaffold is settled; Phase 2 and auth details remain open.

| Folder | What belongs here |
| --- | --- |
| [`developer/`](developer/workflow.md) | How to run and change the current repo (runbook, layout, Docker) |
| [`architecture/`](architecture/product-and-architecture.md) | Product shape, tenancy, RAG, contracts, Phase 2 scaling, open decisions |
| [`ci/`](ci/github-actions-pr-checks.md) | PR checks vs production image/deploy sketch |

**Source of truth for day-to-day work:** [`developer/workflow.md`](developer/workflow.md).  
Root [`README.md`](../README.md) is a short day-1 bring-up only. Package READMEs cover per-service detail.

**Provenance:** Extrapolated from [`../inititalArchitectureResearch.txt`](../inititalArchitectureResearch.txt) (Gemini research chat; filename keeps the original typo). Prefer these docs over the raw chat.

## Load by task

Load a small set for the task. Do not dump the entire library unless auditing architecture end-to-end.

| Task | Load |
| --- | --- |
| Learn one package | Package READMEs below |
| Day-to-day run / change / verify / push | [workflow](developer/workflow.md) |
| Local DX / Docker / as-built layout | [local-development](developer/local-development.md), [docker-and-compose](developer/docker-and-compose.md), [phase1-layout](developer/phase1-layout.md) |
| Product / system overview | [product-and-architecture](architecture/product-and-architecture.md) |
| Phase 1 vs Phase 2 strategy | [phased-delivery-strategy](architecture/phased-delivery-strategy.md) |
| RAG ingestion or chat runtime | [rag-and-data-flow](architecture/rag-and-data-flow.md), [interfaces-and-shared-core](architecture/interfaces-and-shared-core.md) |
| Multi-tenancy / isolation | [multi-tenancy](architecture/multi-tenancy-and-isolation.md) (contracts: [interfaces](architecture/interfaces-and-shared-core.md)) |
| PR checks / GitHub Actions | [github-actions-pr-checks](ci/github-actions-pr-checks.md) |
| Production images / deploy sketch | [cicd-and-images](ci/cicd-and-images.md) |
| Phase 2 / scaling | [scaling-platform](architecture/scaling-platform.md) (layer map), [scaling-backend](architecture/scaling-backend.md) (control-plane patterns) |
| Still-unresolved choices | [open-decisions](architecture/open-decisions.md) |

**LLM rules:** Treat `MUST` / `MUST NOT` as invariants. Phase 1 stack in the repo is **settled** — do not re-litigate from research chat. Treat [open-decisions.md](architecture/open-decisions.md) as undecided unless the user overrides. Prefer local FS + Qdrant + Postgres + `shared-core` over older LocalStack-only drafts.

## Package guides

| Package | Guide |
| --- | --- |
| `backend-core` | [../backend-core/README.md](../backend-core/README.md) |
| `agent-service` | [../agent-service/README.md](../agent-service/README.md) |
| `frontend-dashboard` | [../frontend-dashboard/README.md](../frontend-dashboard/README.md) |
| `chat-widget` | [../chat-widget/README.md](../chat-widget/README.md) |
| `shared-core` | [../shared-core/README.md](../shared-core/README.md) |

## Settled vs open

**Settled (Phase 1):** Compose local stack; FastAPI + LangGraph stub + Vite/React + uv workspace; Postgres + Qdrant + local FS; GitHub Actions PR CI; single-tenant runtime with multi-tenant abstractions (`tenant_id`, storage/vector interfaces). RAG: ingest on control plane, retrieve on agent, always tenant-filter. Phase 2 direction: siloed agent pods on EKS; pooled data; S3.

**Open:** Auth token model, widget public API, observability, Phase 2 managed services / ingress / workers — [open-decisions.md](architecture/open-decisions.md).
