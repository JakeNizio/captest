# Docker and Compose

**Purpose:** Shared image pattern and Compose concepts for local multi-service development.  
**Audience:** Humans and LLMs writing Dockerfiles or Compose config.  
**Status:** Settled patterns. Exact base images depend on open language choices.

## Multi-stage Dockerfile (one file, two targets)

Use one Dockerfile per deployable with shared base and separate stages:

| Stage | Purpose |
| --- | --- |
| `base` | Shared OS + language runtime |
| `development` | Install all deps (including test/dev); hot-reload CMD |
| `production` | Prod-only deps; optimized build/start CMD |

Local Compose builds with `target: development`.  
CI builds with `docker build --target production`.

Illustrative Node shape (language open — adapt to chosen stack):

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

Each of `backend-core`, `agent-service`, `frontend-dashboard`, and `chat-widget` gets its own Dockerfile.

## Docker Compose role

Compose is infra-as-code for the laptop:

- One `docker-compose.yml` in the repo root.
- Developers run `docker compose up` / `docker compose down`.
- Compose creates a private network with DNS: service name = hostname (e.g. `db`, `vector-db`).

CI/CD SHOULD NOT use Compose to run production. CI builds production image targets and deploys those images. See [06-cicd-and-images.md](06-cicd-and-images.md).

## Concepts the team MUST use

### Bind mounts (source)

```yaml
volumes:
  - ./backend-core:/app
```

Keeps host source in sync with the container workdir.

### Anonymous volume for host-incompatible deps (Node example)

```yaml
volumes:
  - ./backend-core:/app
  - /app/node_modules
```

Prevents host `node_modules` from overwriting Linux modules in the container. Apply the equivalent pattern for other ecosystems if needed.

### Named volumes (data)

```yaml
volumes:
  - pg_data:/var/lib/postgresql/data
```

Persists DB/vector data across `compose down` (unless volumes are explicitly removed).

### `depends_on`

Orders container **start**, not full readiness. Apps SHOULD still retry DB connections or use healthchecks when needed.

### Port publishing

```yaml
ports:
  - "8080:8080"  # host:container
```

### Environment

Pass `DATABASE_URL`, `VECTOR_DB_URL`, `STORAGE_PROVIDER`, `TENANT_ID`, `LLM_API_KEY`, etc. Prefer Compose env (and later secrets) over hardcoding.

## Why not raw `docker run`

Without Compose, each service needs long manual `docker run` flags, correct network linking, and ordered startup. Compose replaces that with checked-in YAML shared by the whole team.

Canonical Phase 1 service list: [05-phase1-monorepo-and-compose.md](05-phase1-monorepo-and-compose.md).
