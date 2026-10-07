# Scaling the Backend (`backend-core`)

**Purpose:** Make the control plane horizontally scalable from one Compose container to many pods.  
**Audience:** Humans and LLMs implementing API handlers, health checks, or workers.  
**Status:** Phase 2 target with Phase 1 coding rules. Queue product and worker framework are open.

## Three rules for horizontal scale

### Rule 1: Zero local state

- MUST NOT store sessions/auth only in process memory.
- Phase 2: shared Redis / ElastiCache for session-like state.
- MUST NOT persist uploads on container disk as the source of truth — use `StorageService` (stream/temp then upload).

### Rule 2: Decouple HTTP from heavy ingestion

- MUST NOT run long PDF chunk/embed work inline in the request path under load.
- Phase 1: background tasks (framework-specific: Celery, BullMQ, FastAPI `BackgroundTasks`, etc.).
- Phase 2: enqueue to SQS/RabbitMQ/Redis; API returns **202 Accepted**; workers process jobs.
- Workers MAY scale independently (e.g. KEDA on queue depth).

### Rule 3: Connection pooling

Many API replicas can overwhelm Postgres. Put PgBouncer or AWS RDS Proxy between pods and the DB.

## Phase 1 vs Phase 2 topology

```text
[Requests]
    v
[ALB]
    |-- backend-core pod 1
    |-- backend-core pod 2
    |-- ...
         |--> Redis (sessions/cache)
         |--> Postgres / Aurora (via pooler)
         |--> Queue --> backend-worker pods
```

| Dimension | Phase 1 | Phase 2 |
| --- | --- | --- |
| Compute | One Compose container | EKS Deployment or ECS Fargate |
| Routing | Published port `:8080` | ALB + HTTPS |
| Scaling | Manual | HPA on CPU/RAM/RPS |
| Session state | Single instance OK; prefer externalizable | Redis / ElastiCache |
| Jobs | Sync or local background | SQS (or similar) + worker pool |

## Illustrative HPA (Phase 2)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-core-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-core
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Illustrative async ingest endpoint

Language/framework illustrative (FastAPI-shaped):

```python
@router.post("/api/v1/documents/ingest")
async def ingest_document(
    file: UploadFile,
    tenant_id: str = Depends(get_current_tenant_id),
    queue: QueueService = Depends(get_queue_service),
):
    file_path = await storage_service.upload_file(file.file, file.filename, tenant_id)
    job_id = await queue.enqueue_job(
        task_name="process_rag_document",
        payload={"file_path": file_path, "tenant_id": tenant_id},
    )
    return {"status": "processing", "job_id": job_id}  # 202 Accepted
```

| Process | Responsibility |
| --- | --- |
| `backend-core` API pods | Auth, dashboard APIs, enqueue jobs, fast responses |
| `backend-worker` pods | Chunk, embed, vector upsert; scale on queue depth |

## Phase 1 checklist (do now)

1. Keep `backend-core` logically stateless (Postgres/Redis for shared state).
2. Implement `GET /healthz` and `GET /readyz` for future load balancers/K8s probes.
3. Structure ingestion so a queue/worker split can replace in-process tasks without rewriting upload/auth.

Platform-wide Phase 2 map: [10-scaling-platform.md](10-scaling-platform.md).  
Contracts: [09-interfaces-and-shared-core.md](09-interfaces-and-shared-core.md).
