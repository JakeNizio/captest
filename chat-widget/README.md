# chat-widget

**Audience:** Junior developers working on the embeddable end-user chat UI.  
**Stack:** Vite (library build) + plain JavaScript.  
**Local URL:** [http://localhost:4000](http://localhost:4000)  
**Compose service name:** `chat-widget`

## What is this package?

`chat-widget` is the **embeddable chat widget** — a small script a business can put on their public website so customers can talk to the AI support agent.

In production it will ship as a single browser bundle (today: IIFE `widget.js`) that:

- mounts a chat UI into a host page
- sends messages to `agent-service`
- eventually streams tokens back (SSE/WebSocket)

It is **not** the admin dashboard. Admins use `frontend-dashboard`. This package is for **end customers**.


| You own                            | You do not own            |
| ---------------------------------- | ------------------------- |
| Widget UI + mount API              | LangGraph / RAG logic     |
| Client calls to the agent chat API | Document ingestion        |
| Bundle size / embed story          | Business auth and billing |


Product surfaces: [docs/architecture/product-and-architecture.md](../docs/architecture/product-and-architecture.md).  
Chat runtime flow: [docs/architecture/rag-and-data-flow.md](../docs/architecture/rag-and-data-flow.md).

## Current features (scaffold)

What works today:


| Feature          | Behavior                                                               | Notes                                                   |
| ---------------- | ---------------------------------------------------------------------- | ------------------------------------------------------- |
| Dev host page    | Vite serves a local page at `:4000`                                    | Useful for manual testing                               |
| Mount helpers    | Auto-mounts `#ai-chat-widget-root`; exports `createChatWidget(target)` | Stub UI only                                            |
| Agent URL wiring | `VITE_AGENT_URL` (default `http://localhost:8000`)                     | Displayed on the stub; not yet used for real chat posts |
| Library build    | `npm run build` → IIFE `widget.js`                                     | Embeddable bundle shape                                 |
| Lint script      | `npm run lint`                                                         | ESLint for `.js`                                        |
| Unit tests       | Placeholder                                                            | `npm test` currently prints that tests are not set up   |


There is **no** message composer, history, or streaming client yet.

## Planned features

Near-term Phase 1 work:

1. **Chat UI** — Input box, message list, loading state.
2. **Send message** — `POST {VITE_AGENT_URL}/api/v1/chat` with `{ message, session_id }`.
3. **Session id** — Persist a per-browser/session id so `thread_id` is stable.
4. **Streaming client** — Consume SSE/WebSocket once `agent-service` supports it.
5. **Embed docs** — Minimal snippet for tenant sites (`<script src="…/widget.js">` + mount target).
6. **Public token** — Phase 2 widget auth / abuse controls (still open — [docs/architecture/open-decisions.md](../docs/architecture/open-decisions.md)).

Keep the bundle small and framework-light unless the team chooses otherwise (scaffold default is plain JS + Vite lib mode).

## Integration dependencies

```text
Customer website
   └── loads widget.js
          └── chat-widget UI ──HTTP/stream──► agent-service :8000
                                                  ├── Qdrant
                                                  └── LLM API
```


| Depends on               | Why                             |
| ------------------------ | ------------------------------- |
| `agent-service`          | Chat / streaming runtime        |
| Node 20+ (host optional) | Local `npm` work outside Docker |



| Does **not** depend on     | Why                                                       |
| -------------------------- | --------------------------------------------------------- |
| `backend-core`             | Widget users are not admins; no document upload from here |
| `frontend-dashboard`       | Separate surface                                          |
| `shared-core`              | Python package; not imported in the browser bundle        |
| Postgres / Qdrant directly | Never expose data-plane credentials to the widget         |




### Key env vars


| Variable         | Default                 | Meaning                       |
| ---------------- | ----------------------- | ----------------------------- |
| `VITE_AGENT_URL` | `http://localhost:8000` | Agent base URL for chat calls |


Restart Vite after changing `VITE_*` variables.

## How to develop

Day-to-day loop: [docs/developer/workflow.md](../docs/developer/workflow.md).

### 1. Preferred: run via Compose

```bash
# from repo root
docker compose up chat-widget
# full stack (recommended when testing chat against the agent):
docker compose up
```

Open [http://localhost:4000](http://localhost:4000). Edit `chat-widget/src/widget.js` on the host; Vite hot-reloads (polling enabled for Docker Desktop on Windows).

### 2. Optional: run on the host

```bash
cd chat-widget
npm install
npm run dev
```

Start `agent-service` (via Compose) before testing real chat calls.

### 3. Where to put code

```text
chat-widget/
├── index.html          # local test host page
├── vite.config.js      # lib build → widget.js (IIFE)
├── package.json
└── src/
    └── widget.js       # mount API + stub UI — grow chat UI here
```

Junior tip: keep network calls in a small helper (e.g. `sendChatMessage`) so UI rendering stays readable. Prefer the public export `createChatWidget` as the stable embed API.

### 4. Build the embeddable bundle

```bash
cd chat-widget
npm run build
# output: dist/widget.js (IIFE named AiChatWidget)
```



### 5. Add a Node dependency

```bash
docker compose exec chat-widget npm install <package>
# or on host:
cd chat-widget && npm install <package>
docker compose up -d --build chat-widget
```

Commit `package.json` (and lockfile once present).

### 6. Verify your change

```bash
cd chat-widget
npm run lint
npm run build
```

Manual check: open [http://localhost:4000](http://localhost:4000), send a message (once implemented), confirm the network tab hits port `8000` (`agent-service`), not `8080` (`backend-core`).

### 7. Rules that matter on every PR

1. Widget → `agent-service` for chat. Do not call control-plane admin APIs from the widget.
2. Never embed private API keys or DB URLs in the bundle — only public widget tokens when those exist.
3. Protect bundle size; this script loads on customer sites.
4. Always send a `session_id` / thread id so conversation memory can work later.

