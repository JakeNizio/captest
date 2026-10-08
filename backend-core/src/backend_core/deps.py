from fastapi import Request

from shared_core.providers.local_storage import LocalStorageProvider
from shared_core.providers.qdrant_vector import QdrantVectorStore
from shared_core.schemas.tenant import TenantContext

from backend_core.config import Settings, get_settings


def get_tenant(request: Request) -> TenantContext:
    return request.state.tenant


def get_storage(settings: Settings | None = None) -> LocalStorageProvider:
    settings = settings or get_settings()
    if settings.storage_provider != "local":
        raise RuntimeError(
            f"Unsupported STORAGE_PROVIDER={settings.storage_provider!r} in Phase 1"
        )
    return LocalStorageProvider(
        root_path=settings.local_storage_path,
        public_base_url=f"http://localhost:{settings.port}",
    )


def get_vector_store(settings: Settings | None = None) -> QdrantVectorStore:
    settings = settings or get_settings()
    return QdrantVectorStore(base_url=settings.vector_db_url)
