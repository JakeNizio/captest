from contextlib import asynccontextmanager
from io import BytesIO

import psycopg
from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from shared_core.schemas.tenant import TenantContext

from backend_core.config import Settings, get_settings
from backend_core.deps import get_storage, get_tenant, get_vector_store
from backend_core.middleware import TenantMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    storage = get_storage(settings)
    storage.root_path.mkdir(parents=True, exist_ok=True)
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="backend-core", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(TenantMiddleware, tenant_id=settings.tenant_id)

    @app.get("/health")
    async def health(
        tenant: TenantContext = Depends(get_tenant),
    ) -> dict:
        settings = app.state.settings
        db_ok = False
        vector_ok = False

        try:
            with psycopg.connect(settings.database_url, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    db_ok = cur.fetchone() is not None
        except Exception:
            db_ok = False

        try:
            vector_ok = await get_vector_store(settings).healthcheck()
        except Exception:
            vector_ok = False

        status = "ok" if db_ok and vector_ok else "degraded"
        body = {
            "status": status,
            "service": "backend-core",
            "tenant_id": tenant.tenant_id,
            "dependencies": {
                "postgres": db_ok,
                "qdrant": vector_ok,
                "storage_provider": settings.storage_provider,
            },
        }
        code = 200 if status == "ok" else 503
        return JSONResponse(content=body, status_code=code)

    @app.post("/api/v1/documents")
    async def upload_document_stub(
        file: UploadFile = File(...),
        tenant: TenantContext = Depends(get_tenant),
    ) -> dict:
        """Minimal ingestion stub: store raw file via StorageService only."""
        settings = app.state.settings
        storage = get_storage(settings)
        content = await file.read()
        uri = await storage.upload_file(
            BytesIO(content),
            path=f"uploads/{file.filename or 'unnamed.bin'}",
            tenant_id=tenant.tenant_id,
        )
        return {
            "tenant_id": tenant.tenant_id,
            "filename": file.filename,
            "uri": uri,
            "note": "Phase 1 stub: chunk/embed/upsert not implemented yet",
        }

    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend_core.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    run()
