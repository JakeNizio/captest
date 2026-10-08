import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    tenant_id: str
    vector_db_url: str
    llm_api_key: str
    host: str
    port: int


def get_settings() -> Settings:
    return Settings(
        tenant_id=os.getenv("TENANT_ID", "default_tenant"),
        vector_db_url=os.getenv("VECTOR_DB_URL", "http://localhost:6333"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )
