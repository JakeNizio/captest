import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    tenant_id: str
    database_url: str
    vector_db_url: str
    storage_provider: str
    local_storage_path: str
    host: str
    port: int


def get_settings() -> Settings:
    return Settings(
        tenant_id=os.getenv("TENANT_ID", "default_tenant"),
        database_url=os.getenv(
            "DATABASE_URL",
            (
                "postgresql://platform_admin:local_secure_password@"
                "localhost:5432/core_platform"
            ),
        ),
        vector_db_url=os.getenv("VECTOR_DB_URL", "http://localhost:6333"),
        storage_provider=os.getenv("STORAGE_PROVIDER", "local"),
        local_storage_path=os.getenv("LOCAL_STORAGE_PATH", "/app/storage"),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )
