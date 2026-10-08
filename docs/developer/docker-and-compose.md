# Docker and Compose

**Purpose:** Shared image pattern and Compose concepts for this monorepo.  
**Audience:** Humans and LLMs writing Dockerfiles or Compose config.  
**Status:** Settled for the Phase 1 scaffold (Python uv images + Vite Node images).

Day-to-day commands: [workflow.md](workflow.md). Service list: [phase1-layout.md](phase1-layout.md).

## Multi-stage Dockerfile (one file, two targets)

| Stage | Purpose |
| --- | --- |
| `base` | Shared OS + language runtime |
| `development` | Install all deps (including test/dev); hot-reload CMD |
| `production` | Prod-only deps; optimized start CMD |

Local Compose builds with `target: development`.  
CI/CD builds production with `docker build --target production` (see [cicd-and-images.md](../ci/cicd-and-images.md)).

### Python services (`backend-core`, `agent-service`)

Build context is the **repo root** (uv workspace + `shared-core`). Shape matches the checked-in Dockerfiles:

```dockerfile
FROM python:3.12-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /uvx /bin/
# UV_* env, WORKDIR /app …

FROM base AS development
COPY pyproject.toml uv.lock .python-version ./
COPY shared-core ./shared-core
COPY backend-core ./backend-core
COPY agent-service ./agent-service
RUN uv sync --frozen --package backend-core --group dev
CMD ["uv", "run", "--package", "backend-core", "uvicorn", "…", "--reload"]

FROM base AS production
# same COPY; uv sync --frozen --package backend-core --no-dev --no-editable
CMD ["uv", "run", "--package", "backend-core", "uvicorn", "…"]
```

Venv lives at `/opt/venv` inside the image so bind mounts of source trees do not wipe dependencies.

### Frontend packages (`frontend-dashboard`, `chat-widget`)

Build context is the package directory. Typical Node multi-stage:

```dockerfile
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./

FROM base AS development
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]

FROM base AS production
RUN npm ci --only=production
COPY . .
CMD ["npm", "run", "start"]
```

## Docker Compose role

Compose is infra-as-code for the laptop:

- One `docker-compose.yml` in the repo root (normative; edit that file, not copies in docs).
- Developers run `docker compose up` / `docker compose down`.
- Compose creates a private network with DNS: service name = hostname (e.g. `db`, `vector-db`).

CI/CD SHOULD NOT use Compose to run production. CI validates with Compose development targets; shipping uses production image targets.

## Concepts the team MUST use

### Bind mounts (source)

```yaml
volumes:
  - ./backend-core:/app/backend-core
  - ./shared-core:/app/shared-core
```

### Anonymous volume for host-incompatible Node deps

```yaml
volumes:
  - ./frontend-dashboard:/app
  - /app/node_modules
```

### Named volumes (data)

```yaml
volumes:
  - pg_data:/var/lib/postgresql/data
```

### `depends_on` + healthchecks

Orders start and can wait on health (e.g. Postgres). Apps SHOULD still tolerate brief unavailability.

### Port publishing

```yaml
ports:
  - "8080:8080"  # host:container
```

### Environment

Pass `DATABASE_URL`, `VECTOR_DB_URL`, `STORAGE_PROVIDER`, `TENANT_ID`, `LLM_API_KEY`, etc. Prefer Compose env (and later secrets) over hardcoding.

### Log attach filters

Each service can set `attach: ${COMPOSE_ATTACH_<SERVICE>:-true}`. When `false`, Compose still starts the container but does not stream its logs during `docker compose up`. Usage: [workflow.md](workflow.md#filter-which-service-logs-you-see).

## Why not raw `docker run`

Without Compose, each service needs long manual `docker run` flags, correct network linking, and ordered startup. Compose replaces that with checked-in YAML shared by the whole team.
