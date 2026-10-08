from contextlib import asynccontextmanager
from io import BytesIO

from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from shared_core.schemas.tenant import TenantContext

from backend_core.config import Settings, get_settings
from backend_core.db import database_ready, get_db, reset_engine
from backend_core.deps import get_storage, get_tenant, get_vector_store
from backend_core.migrate import run_migrations
from backend_core.middleware import TenantMiddleware
from backend_core.models import Document


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    reset_engine()
    if settings.run_migrations_on_startup:
        run_migrations(settings.database_url)
    storage = get_storage(settings)
    storage.root_path.mkdir(parents=True, exist_ok=True)
    yield
    reset_engine()


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
        db_ok = database_ready(settings)
        vector_ok = False

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
    async def upload_document(
        file: UploadFile = File(...),
        tenant: TenantContext = Depends(get_tenant),
        db: Session = Depends(get_db),
    ) -> dict:
        """Store raw file via StorageService and record metadata in Postgres."""
        settings = app.state.settings
        storage = get_storage(settings)
        content = await file.read()
        filename = file.filename or "unnamed.bin"
        uri = await storage.upload_file(
            BytesIO(content),
            path=f"uploads/{filename}",
            tenant_id=tenant.tenant_id,
        )
        document = Document(
            tenant_id=tenant.tenant_id,
            filename=filename,
            storage_uri=uri,
            status="uploaded",
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return {
            "id": str(document.id),
            "tenant_id": document.tenant_id,
            "filename": document.filename,
            "uri": document.storage_uri,
            "status": document.status,
            "note": "Phase 1: chunk/embed/upsert not implemented yet",
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
