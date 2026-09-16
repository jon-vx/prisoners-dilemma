from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "not_configured"}


def test_strategy_endpoint_returns_stable_identifiers() -> None:
    response = client.get("/api/v1/strategies")

    assert response.status_code == 200
    strategies = response.json()
    assert [strategy["key"] for strategy in strategies] == [
        "tit_for_tat",
        "pavlov",
        "random",
        "always_cooperate",
        "always_defect",
    ]
    assert all(strategy["name"] for strategy in strategies)
    assert all(strategy["description"] for strategy in strategies)


def test_openapi_document_is_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/strategies" in paths
