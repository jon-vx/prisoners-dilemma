from fastapi.testclient import TestClient

from app.main import create_app
from app.services.storage import MemoryTournamentStore
from app.simulation.strategies import STRATEGY_REGISTRY


client = TestClient(create_app(store=MemoryTournamentStore()))


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "not_configured"}


def test_strategy_endpoint_returns_stable_identifiers() -> None:
    response = client.get("/api/v1/strategies")

    assert response.status_code == 200
    strategies = response.json()
    assert {strategy["key"] for strategy in strategies} == {
        "tit_for_tat",
        "pavlov",
        "random",
        "always_cooperate",
        "always_defect",
        "grim_trigger",
        "tit_for_two_tats",
        "two_tits_for_tat",
        "generous_tit_for_tat",
        "suspicious_tit_for_tat",
        "gradual",
        "naive_prober",
        "remorseful_prober",
        "hard_tit_for_tat",
        "soft_majority",
        "hard_majority",
        "adaptive",
        "random_cooperate_bias",
        "random_defect_bias",
        "alternate",
        "detective",
        "handshake",
        "contrite_tit_for_tat",
    }
    assert all(strategy["name"] for strategy in strategies)
    assert all(strategy["description"] for strategy in strategies)


def test_all_strategies_can_run_together_through_the_api() -> None:
    response = client.post("/api/v1/tournaments", json={
        "strategies": list(STRATEGY_REGISTRY),
        "rounds": 12,
        "seed": 42,
        "include_self_play": True,
    })
    assert response.status_code == 201
    tournament = response.json()
    assert len(tournament["leaderboard"]) == 23
    assert len(tournament["matches"]) == 276
    saved = client.get(f"/api/v1/tournaments/{tournament['id']}")
    assert saved.json() == tournament
