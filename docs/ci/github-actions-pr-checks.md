# GitHub Actions PR Checks

**Purpose:** How PR lint/build/test works for this monorepo — locally and via GitHub Actions.  
**Audience:** Humans and LLMs extending Phase 1 CI.  
**Status:** Settled for Phase 1. **Normative workflow:** [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — edit that file; do not copy YAML from docs.

Related: production images / deploy sketch in [cicd-and-images.md](cicd-and-images.md). Compose topology in [phase1-layout.md](../developer/phase1-layout.md). Day-to-day verify: [workflow.md](../developer/workflow.md).

## Scope split

| Concern | Where |
| --- | --- |
| PR lint, Compose validate/build, in-container tests | This doc + `ci.yml` |
| Production image build (`--target production`), registry push, deploy | [cicd-and-images.md](cicd-and-images.md) |

PR CI uses Compose `development` targets to mirror local. CD MUST build production targets separately when shipping.

## What the workflow does

```text
lint ─────────────────────────────► (independent)
docker-build ──► compose-test
```

| Job | Role |
| --- | --- |
| `lint` | `uv sync`; black + flake8 on `shared-core`, `backend-core`, `agent-service` (Python 3.12); npm lint for both frontends |
| `docker-build` | `docker compose config -q` then `docker compose build` |
| `compose-test` | Needs `docker-build`; `up --build`; wait for Postgres, Qdrant, `/health` on `:8080` and `:8000`; verify migrated schema; `uv run --package … pytest` in both Python services; always `down -v` |

- `lint` and `docker-build` MAY run in parallel.
- `compose-test` MUST wait on `docker-build`.

Triggers: PRs and pushes to `main` / `master`, with concurrency cancel-in-progress.

## Local PR verification

```bash
gh pr checkout <PR-NUMBER>
# or: git fetch origin pull/<PR-NUMBER>/head:pr-<PR-NUMBER>
#     git checkout pr-<PR-NUMBER>
```

Mirror CI (same commands as `compose-test`, plus host lint from [workflow.md](../developer/workflow.md)):

```bash
docker compose config -q
docker compose up -d --build
# wait for db / vector-db / service /health
docker compose exec -T agent-service uv run --package agent-service pytest
docker compose exec -T backend-core uv run --package backend-core pytest
docker compose down -v
```

## Implementation checklist

Already in place for Phase 1. Use when extending CI:

1. **Repo layout** — [phase1-layout](../developer/phase1-layout.md).
2. **Dockerfiles** — `development` / `production`; Python images use repo-root context — [docker-and-compose.md](../developer/docker-and-compose.md).
3. **Test entrypoints** — pytest via uv packages; Node `"lint"` scripts.
4. **`shared-core`** — uv workspace install inside Python images.
5. **Workflow file** — edit `.github/workflows/ci.yml` only; keep PR CI separate from production CD.
6. **Optional:** require the workflow jobs on `main` via branch protection / rulesets.

## Re-running failed checks

| Method | How |
| --- | --- |
| UI | PR → Checks → Re-run jobs → Re-run failed jobs |
| CLI | `gh run rerun <run-id> --failed` |
| Push | New commit that fixes the failure |

## Runner notes (short)

Private GitHub Free plans commonly include a monthly Actions minutes allotment (confirm in billing). Standard `ubuntu-latest` runners are typically ~2 vCPU / 7 GB RAM — enough for this Compose stack for light tests. If builds OOM: fewer parallel BuildKit jobs, layer caching later, or a CI Compose override that drops unused services.

## Out of scope for `ci.yml`

- Publishing production images / EKS deploy — [cicd-and-images](cicd-and-images.md)
- Path filters, language-version matrices
- Real LLM calls (use dummy `LLM_API_KEY`; mock inference in tests)

## Corrections vs old research chat

| Claim in chat | Reality |
| --- | --- |
| Three jobs fully in parallel | Only `lint` parallel with `docker-build`; `compose-test` after build |
| `pytest --if-present` | Invalid; use explicit `uv run --package … pytest` |
| Lint only two Python packages | Lint all three workspace members |
| PR CI = production CD | False — prod images stay in [cicd-and-images](cicd-and-images.md) |
