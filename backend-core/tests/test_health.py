from fastapi.testclient import TestClient

from backend_core.config import Settings
from backend_core.main import create_app


def test_health_includes_tenant_context(tmp_path):
    settings = Settings(
        tenant_id="default_tenant",
        database_url="postgresql://invalid:invalid@127.0.0.1:1/none",
        vector_db_url="http://127.0.0.1:1",
        storage_provider="local",
        local_storage_path=str(tmp_path),
        host="0.0.0.0",
        port=8080,
    )
    client = TestClient(create_app(settings))
    response = client.get("/health")
    assert response.status_code == 503
    body = response.json()
    assert body["tenant_id"] == "default_tenant"
    assert body["service"] == "backend-core"
