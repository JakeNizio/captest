from fastapi import FastAPI
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from shared_core.providers.qdrant_vector import QdrantVectorStore

from agent_service.config import Settings, get_settings
from agent_service.graph import build_graph


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str = Field(default="local-session")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="agent-service", version="0.1.0")
    app.state.settings = settings
    app.state.graph = build_graph()

    @app.get("/health")
    async def health() -> dict:
        settings = app.state.settings
        vector_ok = False
        try:
            vector_ok = await QdrantVectorStore(settings.vector_db_url).healthcheck()
        except Exception:
            vector_ok = False

        status = "ok" if vector_ok else "degraded"
        body = {
            "status": status,
            "service": "agent-service",
            "tenant_id": settings.tenant_id,
            "llm_configured": bool(settings.llm_api_key),
            "dependencies": {"qdrant": vector_ok},
        }
        code = 200 if status == "ok" else 503
        return JSONResponse(content=body, status_code=code)

    @app.post("/api/v1/chat")
    async def chat(request: ChatRequest) -> dict:
        settings = app.state.settings
        config = {
            "configurable": {
                "tenant_id": settings.tenant_id,
                "thread_id": request.session_id,
            }
        }
        result = await app.state.graph.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
        )
        assistant = result["messages"][-1]
        return {
            "tenant_id": settings.tenant_id,
            "session_id": request.session_id,
            "reply": getattr(assistant, "content", str(assistant)),
        }

    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "agent_service.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    run()
