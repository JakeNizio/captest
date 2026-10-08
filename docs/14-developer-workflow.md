# Developer Workflow

**Purpose:** End-to-end day-to-day loop — run the stack, make changes, verify, commit, and push to GitHub.  
**Audience:** Developers starting Phase 1 work on this monorepo.  
**Status:** Matches the current scaffold (Compose + uv workspace + GitHub Actions).

Related: principles in [03-local-development.md](03-local-development.md), ports/services in [05-phase1-monorepo-and-compose.md](05-phase1-monorepo-and-compose.md), CI detail in [13-github-actions-pr-checks.md](13-github-actions-pr-checks.md). Quick start also in the root [README.md](../README.md).

## Prerequisites

| Tool | Required? | Notes |
| --- | --- | --- |
| Git | Yes | Clone, branch, commit, push |
| Docker Desktop (or Engine + Compose) | Yes | Run the full local stack |
| [uv](https://docs.astral.sh/uv/) | Recommended | Host-side Python tests/lint |
| Node 20+ | Optional | Frontend work outside containers |

PRs are created and merged in the **GitHub web UI** (not via a CLI helper).

## 1. Run the stack

From the repo root:

```bash
cp .env.example .env
# optional: set LLM_API_KEY (stub chat does not call an LLM yet)

docker compose up --build
```

The **first** `docker compose up --build` (or a full rebuild after wiping images) can take several minutes — especially on Windows Docker Desktop. That is expected: Compose builds four app images and installs Python/Node dependencies.

You do **not** need a full `--build` every time you start the stack. After images exist:

```bash
docker compose up
```

Use `--build` again only when dependencies or Docker/Compose config changed (see [When to rebuild](#when-to-rebuild)). Prefer rebuilding a single service over rebuilding everything:

```bash
docker compose up -d --build backend-core
```

Leave the compose terminal running so it can keep streaming service logs. Open a **second** terminal in the repo root for everything else while the stack is up — for example adding packages, running tests/lint, and git commit/push (see sections below).

### Filter which service logs you see

All services still start; these flags only control what streams in the `docker compose up` terminal. Defaults are **all on**. Set them in `.env` (see [`.env.example`](../.env.example)):

| Variable | Service |
| --- | --- |
| `COMPOSE_ATTACH_DB` | `db` |
| `COMPOSE_ATTACH_VECTOR_DB` | `vector-db` |
| `COMPOSE_ATTACH_BACKEND_CORE` | `backend-core` |
| `COMPOSE_ATTACH_AGENT_SERVICE` | `agent-service` |
| `COMPOSE_ATTACH_DASHBOARD_UI` | `dashboard-ui` |
| `COMPOSE_ATTACH_CHAT_WIDGET` | `chat-widget` |

Example — backend work, hide everything else:

```bash
# in .env
COMPOSE_ATTACH_DB=false
COMPOSE_ATTACH_VECTOR_DB=false
COMPOSE_ATTACH_AGENT_SERVICE=false
COMPOSE_ATTACH_DASHBOARD_UI=false
COMPOSE_ATTACH_CHAT_WIDGET=false
# COMPOSE_ATTACH_BACKEND_CORE stays true (or omit it)
```

One-off without editing `.env`:

```bash
docker compose up --attach backend-core
# or hide noisy ones:
docker compose up --no-attach db --no-attach vector-db
```

Peek at a hidden service anytime from another terminal: `docker compose logs -f agent-service`.

| Surface | URL |
| --- | --- |
| Dashboard | http://localhost:3000 |
| Chat widget host | http://localhost:4000 |
| Control plane health | http://localhost:8080/health |
| Agent health | http://localhost:8000/health |
| Postgres | `localhost:5432` |
| Qdrant | http://localhost:6333 |

Stop the stack:

```bash
# Ctrl+C in the compose terminal, or:
docker compose down
# wipe DB/vector volumes only when you intend to reset local data:
docker compose down -v
```

## 2. Make changes

### Core rule

Edit on the **host**. Services run in **containers** with bind mounts and hot-reload. Ordinary source edits do **not** need an image rebuild.

### When to rebuild

A full `docker compose up --build` is the slow path. Most day-to-day work does not need it.

**Common cases — no rebuild**

| Situation | What to do |
| --- | --- |
| Edit app source (`.py`, `.jsx`, frontend assets, etc.) | Save → wait for hot-reload |
| Restart the stack after a previous successful build | `docker compose up` (no `--build`) |
| Pull/commit that only touched app code or docs | `docker compose up`; restart a service if reload missed the change |

**Common cases — rebuild (prefer one service)**

| Situation | What to do |
| --- | --- |
| Python deps changed (`pyproject.toml` / `uv.lock`) | `docker compose up -d --build <service>` for the affected service(s) |
| Node deps changed (`package.json` / lockfile) | Rebuild that frontend service, or `npm install` inside the running container |
| `Dockerfile`, system packages, or Compose service definition changed | Rebuild the affected service(s); full `--build` only if several services are involved |
| First clone / images deleted / BuildKit cache wiped | Full `docker compose up --build` (expect several minutes) |

### After `git pull`

Rebuild only when the pull changed something that lives **inside the image**, not bind-mounted source. Skim the diff, then use the tables above — if only `.py` / `.jsx` / docs changed, skip `--build`.

### Where to edit

| Package | Role |
| --- | --- |
| `shared-core/` | Shared schemas, storage/vector interfaces and Phase 1 providers |
| `backend-core/` | Control plane API |
| `agent-service/` | LangGraph chat runtime |
| `frontend-dashboard/` | Business dashboard UI |
| `chat-widget/` | Embeddable widget |

### Branch before coding

```bash
git checkout main
git pull origin main
git checkout -b feature/short-description
```

Use a clear prefix (`feature/`, `fix/`, `docs/`) if the team agrees on one.

### Add a Python dependency

Preferred on host (updates lockfile in the repo):

```bash
uv add --package backend-core <package>
# or:
uv add --package agent-service <package>
uv add --package shared-core <package>
```

Then rebuild/restart the affected Compose service so the container venv matches:

```bash
docker compose up -d --build backend-core
```

Inside a running container (Linux-matched install):

```bash
docker compose exec backend-core uv add --package backend-core <package>
```

Always commit the updated `uv.lock`.

### Add a Node dependency

```bash
docker compose exec dashboard-ui npm install <package>
# or
docker compose exec chat-widget npm install <package>
```

Commit `package.json` (and `package-lock.json` once it exists).

## 3. Verify

Run these before you commit. Prefer the same checks CI will run ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)).

### Smoke the running stack

```bash
curl -s http://localhost:8080/health
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "content-type: application/json" \
  -d "{\"message\":\"hello\",\"session_id\":\"demo\"}"
```

Expect healthy JSON from `/health` when Postgres + Qdrant are up. The chat stub should echo `tenant=default_tenant`.

### Host-side Python tests and lint

```bash
uv sync --all-packages --all-groups

uv run pytest

uv run black --check shared-core backend-core agent-service
# auto-format if needed:
uv run black shared-core backend-core agent-service

uv run flake8 \
  shared-core/src backend-core/src agent-service/src \
  shared-core/tests backend-core/tests agent-service/tests \
  --max-line-length=88
```

### Frontend lint (optional on host; CI runs this)

```bash
cd frontend-dashboard && npm install && npm run lint
cd ../chat-widget && npm install && npm run lint
```

### Compose validation (no full rebuild)

```bash
docker compose config -q
```

### Closer to CI (heavier)

With the stack already built:

```bash
docker compose exec -T agent-service uv run --package agent-service pytest
docker compose exec -T backend-core uv run --package backend-core pytest
```

Full local dry-run of the CI pattern: [13-github-actions-pr-checks.md](13-github-actions-pr-checks.md).

## 4. Commit and push to GitHub

### Never commit

- `.env` (secrets) — use `.env.example` for non-secret templates only
- `.venv/`, `node_modules/`, local storage dumps

### Commit

```bash
git status
git diff

git add <paths-you-intend-to-commit>
# example for a typical feature:
# git add backend-core agent-service shared-core uv.lock

git commit -m "$(cat <<'EOF'
Short why-focused summary.

EOF
)"
```

On Windows PowerShell without bash HEREDOC:

```powershell
git commit -m "Short why-focused summary."
```

Write a short message that explains **why** the change exists (not a file list).

### Push and open a PR

```bash
git push -u origin HEAD
```

Then open a pull request in the GitHub UI:

1. Open the repo on GitHub.
2. Use the banner/compare link that appears after a new branch push, or choose **Pull requests → New pull request**.
3. Set base `main` and compare your branch.
4. Fill in a short summary and test plan, then create the PR.
5. Wait for CI checks to finish before merging.

### After review

```bash
# address feedback, then:
git add <paths>
git commit -m "Address review: <short why>"
git push
```

Merge in the GitHub UI (squash or merge commit per team preference). Pull `main` before starting the next branch — then rebuild only if needed (see [When to rebuild](#when-to-rebuild)).

## Quick reference

```text
run      →  first time: docker compose up --build (slow); later: docker compose up
change   →  edit on host; branch first; uv add / npm install for deps
rebuild  →  only for lockfiles / Dockerfile / Compose — prefer one service, not full --build
pull     →  same rule: app/docs → no rebuild; deps/Docker → rebuild affected service
verify   →  curl health + uv run pytest + black/flake8 (+ frontend lint)
commit   →  git add … && git commit -m "…"
push/PR  →  git push -u origin HEAD, then open PR in GitHub UI
```

## Troubleshooting

| Symptom | Likely fix |
| --- | --- |
| Port already in use | Stop the other process or change the host port in `docker-compose.yml` |
| Stale Python deps in container after `uv add` | `docker compose up -d --build <service>` |
| `/health` returns 503 | Wait for `db` / `vector-db`; check `docker compose logs backend-core` |
| Hot-reload not picking up edits | Confirm bind mounts; restart the service |
| `git` / `docker` not found in a terminal | Install tools and ensure they are on `PATH`; restart the terminal |
| CI fails but local host tests pass | Re-run checks inside Compose (`docker compose exec … pytest`) — container env is source of truth |
