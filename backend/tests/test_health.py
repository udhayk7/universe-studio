from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_root_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openai_health_reports_missing_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    try:
        response = client.get("/api/v1/health/openai")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json()["status"] == "missing"
    assert response.json()["api_key_found"] is False
    assert response.json()["client_initialized"] is False
    assert response.json()["required_variable"] == "OPENAI_API_KEY"


def test_openai_health_reports_configured_client(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-universe-studio")
    get_settings.cache_clear()

    try:
        response = client.get("/api/v1/health/openai")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["api_key_found"] is True
    assert response.json()["client_initialized"] is True
    assert "sk-test-universe-studio" not in response.text


def test_api_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
