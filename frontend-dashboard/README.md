# frontend-dashboard

**Audience:** Junior developers working on the business admin UI.  
**Stack:** Vite + React 18.  
**Local URL:** http://localhost:3000  
**Compose service name:** `dashboard-ui`

## What is this package?

`frontend-dashboard` is the **business dashboard** — the web app a small-business admin uses to manage their AI support agent.

Typical jobs (mostly still planned):

- sign in and see their tenant’s agents
- upload documents that become RAG knowledge
- tweak agent settings / branding
- copy the embed snippet for the chat widget

It talks to **`backend-core`** (control plane). It does **not** talk to the LangGraph agent or Qdrant directly.

| You own | You do not own |
| --- | --- |
| Admin UI pages and forms | FastAPI routes / DB schemas |
| Calling control-plane HTTP APIs | Chat streaming for end customers |
| Dashboard UX / routing | Embeddable widget script |

Product surfaces: [docs/architecture/product-and-architecture.md](../docs/architecture/product-and-architecture.md).

## Current features (scaffold)

What works today:

| Feature | Behavior | Notes |
| --- | --- | --- |
| Vite + React app shell | Renders a stub landing page | Hot-reload in Compose |
| Backend URL wiring | `VITE_BACKEND_URL` (default `http://localhost:8080`) | Shown on the stub page as a health link target |
| Lint script | `npm run lint` | ESLint for `.js` / `.jsx` |
| Unit tests | Placeholder | `npm test` currently prints that tests are not set up |

There is **no** real login, document upload UI, or agent management yet — only a Phase 1 placeholder page in `src/App.jsx`.

## Planned features

Near-term Phase 1 work:

1. **Health / status view** — Call `GET {VITE_BACKEND_URL}/health` and show connection status.
2. **Document upload UI** — `POST /api/v1/documents` (multipart) against `backend-core`.
3. **Agent list / config screens** — Once control-plane APIs exist.
4. **Auth UI** — Login/session once backend auth exists (do not invent a parallel auth scheme in the UI).
5. **Embed instructions** — Show how to install `chat-widget` on the customer’s site.

Phase 2: multi-tenant admin experience, production hosting (S3/CloudFront vs Vercel still open — [docs/architecture/open-decisions.md](../docs/architecture/open-decisions.md)).

## Integration dependencies

```text
Browser ──► frontend-dashboard (Vite/React)
                 │
                 └──HTTP──► backend-core :8080
                               ├── Postgres
                               ├── Qdrant
                               └── Local storage
```

| Depends on | Why |
| --- | --- |
| `backend-core` | All business data and uploads go through the control plane |
| Node 20+ (host optional) | Local `npm` work outside Docker |

| Does **not** depend on | Why |
| --- | --- |
| `agent-service` | Admins do not chat through the dashboard runtime path |
| `shared-core` | Python package; not imported by the React app |
| Qdrant / Postgres directly | Never expose DB credentials to the browser |

### Key env vars

| Variable | Default | Meaning |
| --- | --- | --- |
| `VITE_BACKEND_URL` | `http://localhost:8080` | Control plane base URL baked in at Vite build/dev time |

Vite only exposes env vars prefixed with `VITE_`. Restart the Vite dev server after changing them.

## How to develop

Day-to-day loop: [docs/developer/workflow.md](../docs/developer/workflow.md).

### 1. Preferred: run via Compose

```bash
# from repo root
docker compose up dashboard-ui
# or the full stack:
docker compose up
```

Open http://localhost:3000. Edit `frontend-dashboard/src/` on the host; Vite hot-reloads (polling is enabled for Docker Desktop on Windows).

### 2. Optional: run on the host

```bash
cd frontend-dashboard
npm install
npm run dev
```

You still need `backend-core` (and usually the full Compose stack) for real API calls.

### 3. Where to put code

```text
frontend-dashboard/
├── index.html
├── vite.config.js
├── package.json
└── src/
    ├── main.jsx    # React entry
    └── App.jsx     # stub page — grow this into routes/components
```

Junior tip: keep API base URL in one place (`VITE_BACKEND_URL` / a small `api.js` helper). Prefer `fetch` against `backend-core` paths; do not hardcode `localhost` in many components.

### 4. Add a Node dependency

```bash
docker compose exec dashboard-ui npm install <package>
# or on host:
cd frontend-dashboard && npm install <package>
```

Then rebuild if the image layer needs the new lockfile:

```bash
docker compose up -d --build dashboard-ui
```

Commit `package.json` (and `package-lock.json` once present).

### 5. Verify your change

```bash
cd frontend-dashboard
npm run lint
npm run build
```

Manually click through http://localhost:3000 and confirm network calls hit `backend-core`, not the agent port (`8000`).

### 6. Rules that matter on every PR

1. Browser → `backend-core` only for admin/data operations.
2. Never put LLM keys, DB passwords, or Qdrant URLs in frontend code.
3. Match existing Vite/React patterns; avoid adding a second framework without a team decision.
