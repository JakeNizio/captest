# Local Development Principles

**Purpose:** Why and how the team writes code against the Docker-based local stack.  
**Audience:** Developers and LLMs needing DX principles (not step-by-step commands).  
**Status:** Settled. Day-to-day commands live only in [workflow.md](workflow.md).

## Canonical runbook

For bring-up, rebuilds, deps, migrations, verify, and git/PR steps, use **[workflow.md](workflow.md)**.  
This page is principles only so those commands are not duplicated.

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

In Compose, bind-mount the service directory into the container (e.g. `./backend-core:/app/backend-core`).

- Host edit + save → immediately visible in the container.
- App MUST run with hot-reload so containers are not rebuilt on every change.
- Rebuild images when Dockerfile, lockfiles, or system dependencies change — not for ordinary source edits.

Ports and service map: [phase1-layout.md](phase1-layout.md).

## Installing dependencies

Install server runtime deps so binaries match the container OS (Linux):

- Prefer host `uv add --package <member> …` then rebuild the affected Compose service.
- Or `docker compose exec <service> …` for Linux-matched installs.

Do not install server runtime deps only on the host and expect containers to pick them up correctly. Details: [workflow.md](workflow.md).

## IDE options

| Approach | Where you type | Where SDKs/extensions run |
| --- | --- | --- |
| Traditional volumes (default) | Any local IDE | On host; terminal via `docker compose exec` |
| VS Code Dev Containers | VS Code attached to container | Inside container |

Default for this repo: bind mounts + Compose. Dev Containers remain optional. See [open-decisions.md](../architecture/open-decisions.md).

Compose mechanics: [docker-and-compose.md](docker-and-compose.md).
