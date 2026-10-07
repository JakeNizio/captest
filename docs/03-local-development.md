# Local Development

**Purpose:** How the team writes and runs code against the Docker-based local stack.  
**Audience:** Developers and LLMs generating onboarding or DX instructions.  
**Status:** Settled workflow principles. IDE approach (Dev Containers vs volumes) is open — see [12-open-decisions.md](12-open-decisions.md).

## Core rule

Write code on the **host**. Run the app inside **containers**. Sync via bind mounts. Do not treat the container as the primary editor environment unless using Dev Containers.

## Why Docker locally

| Without local Docker | With local Docker |
| --- | --- |
| Host OS differs from prod Linux | Same Linux base as prod images |
| Manual DB / tool installs | `docker compose up` brings the stack |
| Version conflicts across projects | Isolated per-project containers |

Accept trade-offs: file-sync overhead on macOS/Windows; team must learn Compose basics.

## How file sync works

In Compose, bind-mount the service directory into the container (e.g. `./backend-core:/app`).

- Host edit + save → immediately visible at `/app` in the container.
- App MUST run with hot-reload (e.g. nodemon, `uvicorn --reload`) so containers are not rebuilt on every change.
- Rebuild images when Dockerfile or system dependencies change — not for ordinary source edits.

## Ports

Map container listen ports to localhost so browsers and GUI tools work on the host.

Canonical Phase 1 ports: [05-phase1-monorepo-and-compose.md](05-phase1-monorepo-and-compose.md).

## Installing dependencies

Install packages **inside** the running container so binaries match Linux:

```bash
docker compose exec backend-core <pkg-manager> install <package>
docker compose exec agent-service <pkg-manager> install <package>
```

Do not install server runtime deps only on the host and expect containers to pick them up correctly.

## Day-1 onboarding

1. Install Git and Docker Desktop.
2. Clone the repo.
3. Copy/configure secrets as required (at minimum `LLM_API_KEY` for agent).
4. Run `docker compose up`.
5. Open dashboard / APIs on published localhost ports.

Daily loop: edit on host → hot-reload in container → test via localhost → commit.

## IDE options (open)

| Approach | Where you type | Where SDKs/extensions run |
| --- | --- | --- |
| VS Code Dev Containers | VS Code attached to container | Inside container |
| Traditional volumes | Any local IDE | On host; terminal via `docker compose exec` |

Team SHOULD pick one primary path; until then both are valid. See [12-open-decisions.md](12-open-decisions.md).

Compose mechanics: [04-docker-and-compose.md](04-docker-and-compose.md).
