# GitHub Actions PR Checks

**Purpose:** How to run build/test checks on PRs for this monorepo — locally and via GitHub Actions — including implementation prerequisites and GitHub free-tier resource limits.  
**Audience:** Humans and LLMs setting up CI for Phase 1.  
**Status:** Phase 1 plan (workflow shape). CI product remains open in [12-open-decisions.md](12-open-decisions.md); GitHub Actions is the provisional default.

Related: high-level CD / production images in [06-cicd-and-images.md](06-cicd-and-images.md). Compose topology in [05-phase1-monorepo-and-compose.md](05-phase1-monorepo-and-compose.md).

## Scope split

| Concern | Where |
| --- | --- |
| PR lint, Compose validate/build, in-container tests | This doc |
| Production image build (`--target production`), registry push, deploy | [06-cicd-and-images.md](06-cicd-and-images.md) |

PR CI MAY use Compose `development` targets to mirror local. CD MUST still build production targets separately when shipping.

## Local PR verification

Before or during review:

```bash
gh pr checkout <PR-NUMBER>
```

Without `gh`:

```bash
git fetch origin pull/<PR-NUMBER>/head:pr-<PR-NUMBER>
git checkout pr-<PR-NUMBER>
```

Then exercise the stack the same way CI will:

```bash
docker compose config -q
docker compose up -d --build
# wait for db / vector-db readiness (see workflow below)
docker compose exec -T agent-service pytest   # once tests exist
docker compose down -v
```

Language-specific host lint/test commands depend on stack choices — see [12-open-decisions.md](12-open-decisions.md).

## Target workflow layout

Create `.github/workflows/ci.yml` when ready to implement (not required until the monorepo and Dockerfiles exist).

### Job graph

```text
lint ─────────────────────────────► (independent)
docker-build ──► compose-test
```

- `lint` and `docker-build` MAY run in parallel.
- `compose-test` MUST wait on `docker-build` (needs images / validated Compose).

### Verified workflow sketch

Assumptions match provisional scaffolding defaults: Python for `agent-service` + `shared-core` (+ `backend-core` if FastAPI); Node for `frontend-dashboard` + `chat-widget`. Adjust lint/test steps if stack choices differ.

```yaml
name: CI Checks

on:
  pull_request:
    branches: [main, master]
  push:
    branches: [main, master]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Code Quality & Linting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm

      - name: Lint Python packages
        run: |
          python -m pip install --upgrade pip
          pip install black flake8
          # Include backend-core here if it is Python (provisional default: FastAPI)
          black --check agent-service shared-core
          flake8 agent-service shared-core --max-line-length=88
          if [ -f backend-core/pyproject.toml ] || [ -f backend-core/requirements.txt ]; then
            black --check backend-core
            flake8 backend-core --max-line-length=88
          fi

      - name: Lint Node packages
        run: |
          for dir in frontend-dashboard chat-widget; do
            if [ -f "$dir/package.json" ]; then
              (cd "$dir" && npm ci && npm run lint --if-present)
            fi
          done
          # If backend-core is Node instead of Python, lint it here instead.

  docker-build:
    name: Docker Build & Compose Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3

      - name: Validate Compose file
        run: docker compose config -q

      - name: Build all Compose services
        run: docker compose build
        env:
          LLM_API_KEY: dummy_ci_key_for_build

  compose-test:
    name: Integration Tests (Docker Compose)
    needs: [docker-build]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Boot Compose stack
        run: docker compose up -d --build
        env:
          LLM_API_KEY: mock_ci_key

      - name: Wait for Postgres and Qdrant
        run: |
          until docker compose exec -T db pg_isready -U platform_admin -d core_platform; do
            sleep 2
          done
          # Confirm health path against your Qdrant image tag (/readyz is common on recent Qdrant)
          until curl -sf http://localhost:6333/readyz || curl -sf http://localhost:6333/healthz; do
            sleep 2
          done

      - name: Run service tests inside containers
        run: |
          # Prefer explicit commands once stacks are fixed.
          # Python agent (expected):
          docker compose exec -T agent-service pytest
          # Control plane — pick ONE based on language:
          # docker compose exec -T backend-core pytest
          # docker compose exec -T backend-core npm test --if-present

      - name: Dump logs on failure
        if: failure()
        run: docker compose logs

      - name: Tear down
        if: always()
        run: docker compose down -v
```

### Corrections vs the research chat

| Claim in chat | Verification |
| --- | --- |
| Three jobs "in parallel" | Only `lint` ∥ `docker-build`; `compose-test` is sequential after build |
| `pytest --if-present` | Invalid; pytest has no `--if-present`. Use explicit commands or shell guards |
| Lint only `agent-service` + `shared-core` for Python | If `backend-core` is FastAPI (provisional default), lint it too |
| Qdrant `/healthz` only | Probe `/readyz` or `/healthz` depending on image version |
| PR CI builds = production CD | False. This workflow validates Compose/dev parity; prod images stay in [06](06-cicd-and-images.md) |

## Implementation checklist

Do these in order. Do **not** expect a green CI run until prerequisites exist.

1. **Repo layout** — Monorepo matches [05](05-phase1-monorepo-and-compose.md) (`docker-compose.yml`, service folders, `shared-core`).
2. **Dockerfiles** — Each Compose-built service has a `development` stage (`target: development`). Pattern: [04-docker-and-compose.md](04-docker-and-compose.md).
3. **Test entrypoints** — `agent-service` has pytest (or chosen runner) + tests; Node packages define `"test"` / `"lint"` scripts if used.
4. **`shared-core` packaging** — Install/copy into `backend-core` and `agent-service` images so imports resolve in CI builds. Still open how (editable pip install vs copy vs workspaces) — [12](12-open-decisions.md).
5. **Add workflow file** — `.github/workflows/ci.yml` from the sketch above, adjusted to final languages.
6. **Local dry-run** — `docker compose config -q`, `up --build`, exec tests, `down -v`.
7. **Open PR** — Push branch; watch Checks / Actions.
8. **Optional: required checks** — Repo Settings → Branch protection / Rulesets → require `lint`, `docker-build`, `compose-test` (exact job names) on `main`.

## Re-running failed checks

| Method | How |
| --- | --- |
| UI | PR → Checks (or Conversation footer) → Re-run jobs → Re-run failed jobs |
| CLI | `gh run rerun <run-id> --failed` |
| Push | New commit (empty commit works but is noisy; prefer fixing the failure) |

## GitHub resources (minutes and runners)

Limits change; confirm on GitHub billing docs for your plan.

### Typical Free-plan expectations

| Repo visibility | Actions minutes (GitHub-hosted) |
| --- | --- |
| Public | Generally unlimited for standard GitHub-hosted Linux runners |
| Private | Common Free allotment: **2,000 minutes/month** (verify in billing UI) |

Rough capacity if a full workflow averages ~3 minutes: on the order of hundreds of runs per month on a private Free plan — usually enough for a small team. Large Compose builds can exceed 3 minutes; measure with real runs.

### How to check usage

Profile → **Settings** → **Billing and plans** → **Plans and usage** → **GitHub Actions** minutes used vs allotment.

### Runner capacity vs this Compose stack

Standard `ubuntu-latest` GitHub-hosted runners are commonly documented around **2 vCPU / 7 GB RAM / ~14 GB SSD**. Phase 1 services (Postgres, Qdrant, four app containers) SHOULD fit for build + idle + light tests. If builds OOM or disk-fill:

- Build services sequentially or with fewer parallel BuildKit jobs.
- Add layer caching (`docker/build-push-action` cache or registry cache) later.
- Drop unused services from CI Compose overrides if needed.

### Spending limit

Free accounts typically default to a **$0** Actions spending limit: exceeding included minutes pauses workflows rather than billing, unless you raise the limit. Confirm in billing settings.

## What this does *not* cover yet

- Publishing production images to ECR / deploy to EKS ([06](06-cicd-and-images.md)).
- Path filters (only test changed packages) — useful later to save minutes.
- Matrix builds per language version.
- Required secrets beyond a dummy `LLM_API_KEY` for boot (real LLM calls SHOULD be mocked in CI).

## LLM context tip

When scaffolding CI, also load [05](05-phase1-monorepo-and-compose.md), [04](04-docker-and-compose.md), [06](06-cicd-and-images.md), and [12](12-open-decisions.md). Do not invent production deploy steps into `ci.yml` unless asked.
