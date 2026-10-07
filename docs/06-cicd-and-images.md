# CI/CD and Images

**Purpose:** How code moves from laptop Compose to production images and deploy.  
**Audience:** Humans and LLMs designing pipelines or Docker build targets.  
**Status:** Settled high-level pipeline. CI product (GitHub Actions vs GitLab CI) is open.

## Principle

| Environment | What runs |
| --- | --- |
| Local | `docker compose up` with `target: development` + bind mounts |
| CI/CD | Lint/test, then `docker build --target production`, push images |
| Production | Pull production images; no source bind mounts; no Compose for runtime |

Compose is a developer tool. Production runs hardened images from a registry.

## Pipeline stages

1. **CI (lint & test)** — Run linters and tests on the PR/push. May use the development image stage or the CI runner's language toolchain. Exact test matrix is open.
2. **Build** — Build production images for each deployable that ships as a container:

```bash
docker build --target production -t <registry>/backend-core:<tag> ./backend-core
docker build --target production -t <registry>/agent-service:<tag> ./agent-service
```

Frontends may be containerized or built as static assets for CDN hosting (Phase 2); decide with stack choices.

3. **Push** — Push tagged images to a container registry (AWS ECR is the Phase 2 example; Docker Hub also mentioned).
4. **Deploy**
   - Control plane + dashboard: standard Deployment in a shared namespace (e.g. `prod-core`).
   - Agents (Phase 2): control plane provisions tenant pods/namespaces from the same `agent-service` image with tenant-specific config.

## Images that MUST be separate

| Image | Source package |
| --- | --- |
| Control plane | `backend-core` |
| Agent runtime | `agent-service` |

Shared contracts live in `shared-core` and MUST be copied or packaged into both images as needed.

## Tenant provisioning (Phase 2 sketch only)

When a business signs up / is ready for an agent:

1. Control plane completes ingestion into shared vector store (with `tenant_id` metadata).
2. Control plane calls the Kubernetes API (SDK).
3. Provision isolated namespace/pod via Helm chart or CRD.
4. Pod boots from the generic `agent-service` production image with tenant identity injected (env or equivalent).

Exact Helm vs CRD design, IAM, and failure modes are open — see [12-open-decisions.md](12-open-decisions.md).

## Workflow summary

| Phase | Actor | Action |
| --- | --- | --- |
| Local | Developer | `docker compose up`; edit via mounts |
| CI/CD | Pipeline | Test; build `--target production`; push registry |
| Prod | Cloud / orchestrator | Pull image; run; scale |

Multi-stage Dockerfile pattern: [04-docker-and-compose.md](04-docker-and-compose.md).  
PR lint / Compose integration checks: [13-github-actions-pr-checks.md](13-github-actions-pr-checks.md).  
Scaling after deploy: [10-scaling-platform.md](10-scaling-platform.md), [11-scaling-backend.md](11-scaling-backend.md).
