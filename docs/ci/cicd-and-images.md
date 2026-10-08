# CI/CD and Images

**Purpose:** How code moves from laptop Compose to production images and deploy.  
**Audience:** Humans and LLMs designing pipelines or Docker build targets.  
**Status:** Settled high-level pipeline. PR CI product is GitHub Actions ([github-actions-pr-checks.md](github-actions-pr-checks.md)); production registry/deploy details remain Phase 2-open.

## Principle

| Environment | What runs |
| --- | --- |
| Local | `docker compose up` with `target: development` + bind mounts |
| CI/CD | Lint/test, then `docker build --target production`, push images |
| Production | Pull production images; no source bind mounts; no Compose for runtime |

Compose is a developer tool. Production runs hardened images from a registry.

## Pipeline stages

1. **CI (lint & test)** — GitHub Actions PR workflow (lint, Compose build, in-container pytest). See [github-actions-pr-checks.md](github-actions-pr-checks.md).
2. **Build** — Build production images for each deployable that ships as a container. Python images use **repo-root** context (uv workspace):

```bash
docker build --target production -f backend-core/Dockerfile -t <registry>/backend-core:<tag> .
docker build --target production -f agent-service/Dockerfile -t <registry>/agent-service:<tag> .
```

Frontends may be containerized or built as static assets for CDN hosting (Phase 2 hosting choice still open).

3. **Push** — Push tagged images to a container registry (AWS ECR is the Phase 2 example; Docker Hub also mentioned).
4. **Deploy**
   - Control plane + dashboard: standard Deployment in a shared namespace (e.g. `prod-core`).
   - Agents (Phase 2): control plane provisions tenant pods/namespaces from the same `agent-service` image with tenant-specific config.

## Images that MUST be separate

| Image | Source package |
| --- | --- |
| Control plane | `backend-core` |
| Agent runtime | `agent-service` |

Shared contracts live in `shared-core` and are installed via the uv workspace into both Python images.

## Tenant provisioning (Phase 2 sketch only)

When a business signs up / is ready for an agent:

1. Control plane completes ingestion into shared vector store (with `tenant_id` metadata).
2. Control plane calls the Kubernetes API (SDK).
3. Provision isolated namespace/pod via Helm chart or CRD.
4. Pod boots from the generic `agent-service` production image with tenant identity injected (env or equivalent).

Exact Helm vs CRD design, IAM, and failure modes are open — see [open-decisions.md](../architecture/open-decisions.md).

## Workflow summary

| Phase | Actor | Action |
| --- | --- | --- |
| Local | Developer | `docker compose up`; edit via mounts |
| CI/CD | Pipeline | Test; build `--target production`; push registry |
| Prod | Cloud / orchestrator | Pull image; run; scale |

Multi-stage Dockerfile pattern: [docker-and-compose.md](../developer/docker-and-compose.md).  
PR lint / Compose integration checks: [github-actions-pr-checks.md](github-actions-pr-checks.md).  
Scaling after deploy: [scaling-platform.md](../architecture/scaling-platform.md), [scaling-backend.md](../architecture/scaling-backend.md).
