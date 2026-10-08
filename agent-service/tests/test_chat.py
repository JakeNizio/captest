from fastapi.testclient import TestClient

from agent_service.config import Settings
from agent_service.main import create_app


def test_chat_passes_tenant_into_graph():
    settings = Settings(
        tenant_id="default_tenant",
        vector_db_url="http://127.0.0.1:1",
        llm_api_key="",
        host="0.0.0.0",
        port=8000,
    )
    client = TestClient(create_app(settings))
    response = client.post(
        "/api/v1/chat",
        json={"message": "hello", "session_id": "sess-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == "default_tenant"
    assert "tenant=default_tenant" in body["reply"]
    assert "thread=sess-1" in body["reply"]
