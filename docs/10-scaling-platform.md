# Scaling the Platform (Non-Agent Layers)

**Purpose:** How everything except agent pod siloing scales from Phase 1 to Phase 2.  
**Audience:** Humans and LLMs planning Phase 2 infra or writing scale-ready Phase 1 code.  
**Status:** Phase 2 target. Managed product picks (Aurora vs Cloud SQL, Qdrant Cloud vs Pinecone, etc.) are open.

## Goal

Agent pods scale by tenant isolation on EKS. The rest of the system MUST scale as shared, horizontally expandable services without rewriting application contracts from [09-interfaces-and-shared-core.md](09-interfaces-and-shared-core.md).

## 1. Database and vector storage

### Postgres

| | Phase 1 | Phase 2 |
| --- | --- | --- |
| Deployment | Compose `pgvector` container | Aurora PostgreSQL Serverless v2 (or managed Cloud SQL) |
| Scaling | Single container | ACU autoscaling, storage growth, read replicas |
| Tenancy | `tenant_id` column | Same + RLS |

### Vector DB

| | Phase 1 | Phase 2 |
| --- | --- | --- |
| Deployment | Compose Qdrant (canonical example) | Managed Qdrant Cloud / Pinecone / OpenSearch |
| Scaling | Single node | Sharding / managed node autoscaling |
| Tenancy | Payload `tenant_id` filter | Same; index `tenant_id` for filter-before-ANN |

## 2. Control plane (`backend-core`)

- MUST be stateless (no in-memory sessions; no durable local disk for uploads).
- Deploy as EKS Deployment (or ECS Fargate) behind ALB.
- Scale with HPA on CPU/memory or request count.
- Offload heavy ingestion to async workers (detail: [11-scaling-backend.md](11-scaling-backend.md)).

## 3. Storage layer

- Flip `STORAGE_PROVIDER=s3`.
- Path isolation: `s3://platform-bucket/{tenant_id}/uploads/{file_id}`.
- Prefer presigned URLs so clients upload large files directly to S3 instead of through API pods.

## 4. Frontends and edge

| Asset | Phase 2 hosting | Scale mechanism |
| --- | --- | --- |
| Dashboard | Static build on S3/CloudFront or Vercel | CDN |
| Chat widget | Bundled `widget.js` on CloudFront | Global edge |
| Streaming | API Gateway or ingress (NGINX/Envoy) in front of agents | Connection fan-out at edge/proxy |

## Phase 1 → Phase 2 blueprint table

| Layer | Phase 1 (Compose) | Phase 2 (Cloud) | Autoscaling |
| --- | --- | --- | --- |
| Control API | Single `backend-core` | EKS Deployment + ALB | HPA (CPU / RPS) |
| Agent brain | Single `agent-service` | Per-tenant EKS pods / KEDA | HPA or queue depth |
| Database | `pgvector` container | Aurora Serverless | ACU + replicas |
| Vector DB | Qdrant container | Managed vector service | Cloud sharding |
| File storage | Local volume | S3 | Managed |
| Widget CDN | `chat-widget` container | CloudFront / S3 | CDN anycast |

## Code implications for Phase 1

- Keep using interfaces (`StorageService`, `VectorStoreService`).
- Avoid assuming localhost paths outside the storage provider.
- Design control plane handlers to tolerate multiple replicas later (stateless).

Backend-specific patterns and HPA samples: [11-scaling-backend.md](11-scaling-backend.md).
