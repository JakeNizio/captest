# agent-service

**Audience:** Junior developers working on the chat / RAG runtime.  
**Stack:** FastAPI + LangGraph + Python 3.12 (uv workspace member).  
**Local URL:** http://localhost:8000

## What is this package?

`agent-service` is the **LangGraph chat runtime** — the AI “brain” that talks to end customers.

When someone on a tenant’s website asks a question in the chat widget, traffic should eventually hit this service. It:

- runs a LangGraph graph (today: a stub echo node)
- will retrieve tenant-scoped documents from the vector DB (RAG)
- will call an LLM to synthesize answers
- will stream replies back to the widget (planned)

It is **not** the control plane. Business admins upload docs and manage config via `backend-core` + `frontend-dashboard`. This service **reads** knowledge at chat time; it should not own ingestion.

| You own | You do not own |
| --- | --- |
| Chat API + LangGraph graph | Document upload / chunk / embed pipeline |
| Retrieval tools + session memory | Dashboard UI / admin APIs |
| Streaming replies to the widget | Postgres tenant admin schemas |

Architecture overview: [docs/architecture/product-and-architecture.md](../docs/architecture/product-and-architecture.md).  
Runtime RAG loop: [docs/architecture/rag-and-data-flow.md](../docs/architecture/rag-and-data-flow.md).

## Current features (scaffold)

What works today:

| Feature | Endpoint / behavior | Notes |
| --- | --- | --- |
| Health check | `GET /health` | Checks Qdrant; reports `tenant_id` and whether `LLM_API_KEY` is set |
| Stub chat | `POST /api/v1/chat` | Runs a LangGraph echo node — **no LLM call yet** |
| Tenant / thread config | Passed into every graph run | `configurable.tenant_id` + `configurable.thread_id` |
| Vector client wiring | Health uses `QdrantVectorStore` from `shared-core` | Retrieval tool not implemented yet |

Example chat call:

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "content-type: application/json" \
  -d "{\"message\":\"hello\",\"session_id\":\"demo\"}"
```

Expected shape: a reply that includes `tenant=default_tenant` and echoes your message.

## Planned features

Near-term Phase 1 work:

1. **Real LangGraph graph** — Intent → (optional) retrieve → synthesize with LLM instead of `echo_node`.
2. **Retrieval tool** — Call `VectorStoreService.similarity_search(..., tenant_id)` reading `tenant_id` from `RunnableConfig` (never hardcode another tenant).
3. **LLM integration** — Use `LLM_API_KEY` (provider choice still open — see [docs/architecture/open-decisions.md](../docs/architecture/open-decisions.md)).
4. **Streaming** — SSE or WebSocket so the widget can show tokens as they arrive.
5. **Session memory** — Checkpointer keyed by `thread_id` / session (SQLite vs Redis still open).

Phase 2 (later): one agent deployment/pod per tenant on EKS; ingress validates widget tokens and routes by tenant. Phase 1 keeps a **single** `agent-service` container with `TENANT_ID=default_tenant`.

## Integration dependencies

```text
chat-widget ──HTTP (later: stream)──► agent-service
                                         │
                                         ├──► Qdrant (vector-db)   tenant-filtered similarity search
                                         ├──► LLM API              synthesis (when wired)
                                         └──► shared-core          vector interface + contracts
```

| Depends on | Why |
| --- | --- |
| `shared-core` | `VectorStoreService` / `QdrantVectorStore`; shared contracts |
| Qdrant (`VECTOR_DB_URL`) | RAG retrieval at chat time |
| LLM provider (`LLM_API_KEY`) | Needed once the graph stops echoing |
| `TENANT_ID` env | Phase 1 static tenant for every graph run |

| Depends on this package | Why |
| --- | --- |
| `chat-widget` | End-user UI that will call `/api/v1/chat` (or a streaming successor) |

**Does not talk to Postgres today.** Ingestion writes vectors from `backend-core`; this service only needs the vector DB (+ LLM) for chat.

### Key env vars

| Variable | Default / example | Meaning |
| --- | --- | --- |
| `TENANT_ID` | `default_tenant` | Injected into every LangGraph `configurable` |
| `VECTOR_DB_URL` | `http://vector-db:6333` | Qdrant base URL |
| `LLM_API_KEY` | empty | Optional for stub; required for real LLM nodes |
| `PORT` | `8000` | HTTP port |

## How to develop

Day-to-day loop: [docs/developer/workflow.md](../docs/developer/workflow.md).

### 1. Start the stack

```bash
# from repo root
docker compose up
# rebuild only this service after dependency changes:
docker compose up -d --build agent-service
```

Edit under `agent-service/` on the host; uvicorn reloads inside the container.

### 2. Where to put code

```text
agent-service/
├── src/agent_service/
│   ├── main.py       # FastAPI routes (health, chat)
│   ├── config.py     # env → Settings
│   └── graph.py      # LangGraph state + nodes
└── tests/
```

Junior tip: keep HTTP concerns in `main.py` and agent logic in `graph.py` (or modules imported from it). When you add a retrieval tool, pass `config: RunnableConfig` and read `config["configurable"]["tenant_id"]` — see [docs/architecture/interfaces-and-shared-core.md](../docs/architecture/interfaces-and-shared-core.md).

### 3. Add a Python dependency

```bash
uv add --package agent-service <package>
docker compose up -d --build agent-service
```

Commit the updated `uv.lock`.

### 4. Verify your change

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "content-type: application/json" \
  -d "{\"message\":\"hello\",\"session_id\":\"demo\"}"

uv sync --all-packages --all-groups
uv run pytest agent-service
uv run black agent-service
uv run flake8 agent-service/src agent-service/tests --max-line-length=88
```

### 5. Rules that matter on every PR

1. Every `ainvoke` / `astream` MUST pass `tenant_id` and `thread_id` in `configurable`.
2. Similarity search MUST filter by `tenant_id` (enforced via `VectorStoreService`).
3. Do not put document upload / chunk / embed logic here — that belongs in `backend-core`.
4. Do not talk to the vector DB with ad-hoc clients that skip the shared interface.
