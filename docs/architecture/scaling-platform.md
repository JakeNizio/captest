# Scaling the Platform (Non-Agent Layers)

**Purpose:** Phase 1 → Phase 2 layer map for everything except per-tenant agent siloing detail.  
**Audience:** Humans and LLMs planning Phase 2 infra or writing scale-ready Phase 1 code.  
**Status:** Phase 2 target. Managed product picks (Aurora vs Cloud SQL, Qdrant Cloud vs Pinecone, etc.) are open.

Control-plane coding rules, HPA, and async ingest: [scaling-backend.md](scaling-backend.md). Contracts stay stable: [interfaces-and-shared-core.md](interfaces-and-shared-core.md).

## Goal

Agent pods scale by tenant isolation on EKS. The rest of the system MUST scale as shared, horizontally expandable services without rewriting application contracts.

## Phase 1 → Phase 2 blueprint

| Layer | Phase 1 (Compose) | Phase 2 (Cloud) | Autoscaling |
| --- | --- | --- | --- |
| Control API | Single `backend-core` | EKS Deployment + ALB | HPA (CPU / RPS) — see [scaling-backend](scaling-backend.md) |
| Agent brain | Single `agent-service` | Per-tenant EKS pods / KEDA | HPA or queue depth |
| Database | Postgres (`pgvector`-enabled image; relational data only) | Aurora Serverless (or managed Cloud SQL) | ACU + replicas |
| Vector DB | Qdrant container (vectors live here, not in Postgres) | Managed Qdrant Cloud / Pinecone / OpenSearch | Cloud sharding |
| File storage | Local volume via `StorageService` | S3 (`STORAGE_PROVIDER=s3`) | Managed |
| Widget / dashboard | Compose frontend containers | CDN (CloudFront / S3 or Vercel) | CDN anycast |
| Streaming edge | Direct to agent port | Ingress / API Gateway in front of agents | Connection fan-out |

Notes:

- **Postgres vs vectors:** The Compose `db` service uses a Postgres image that *includes* the pgvector extension. Phase 1 still stores embeddings in **Qdrant**. Do not treat “pgvector image” as “vectors in Postgres.”
- **Tenancy:** Same `tenant_id` column / payload filters in both phases; Phase 2 adds Postgres RLS.
- **Storage:** Prefer presigned URLs in Phase 2 so clients upload large files to S3 instead of through API pods.

## Code implications for Phase 1

- Keep using interfaces (`StorageService`, `VectorStoreService`).
- Avoid assuming localhost paths outside the storage provider.
- Design control plane handlers to tolerate multiple replicas later (stateless) — patterns in [scaling-backend.md](scaling-backend.md).
