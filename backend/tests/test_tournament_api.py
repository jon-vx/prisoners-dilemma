from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.storage import MemoryTournamentStore


@pytest.fixture
def client():
    with TestClient(create_app(store=MemoryTournamentStore())) as client:
        yield client


@pytest.fixture
def configuration():
    return {
        "strategies": ["always_cooperate", "always_defect", "tit_for_tat"],
        "rounds": 3,
        "seed": 42,
        "include_self_play": False,
        "payoffs": {"temptation": 7, "reward": 4, "punishment": 2, "sucker": 0},
    }


def test_create_and_retrieve_tournament_and_match(client, configuration):
    response = client.post("/api/v1/tournaments", json=configuration)
    assert response.status_code == 201
    tournament = response.json()
    assert tournament["configuration"] == configuration
    assert tournament["created_at"]
    assert len(tournament["matches"]) == 3
    assert all("history" not in match for match in tournament["matches"])
    assert client.get(response.headers["Location"]).json() == tournament

    match = tournament["matches"][0]
    detail_response = client.get(f"/api/v1/matches/{match['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert {key: value for key, value in detail.items() if key != "history"} == match
    assert [row["round_number"] for row in detail["history"]] == [1, 2, 3]
    assert detail["score_a"] == 0
    assert detail["score_b"] == 21
    assert detail["history"][-1]["cumulative_score_b"] == 21
    assert detail["history"][0]["move_a"] == "cooperate"
    assert detail["history"][0]["move_b"] == "defect"
    assert detail["tournament_id"] == tournament["id"]
    standings = {row["strategy_key"]: row for row in tournament["leaderboard"]}
    assert standings["always_defect"]["total_score"] == 32
    assert standings["always_defect"]["wins"] == 2
    assert standings["always_cooperate"]["ties"] == 1
    assert standings["tit_for_tat"]["cooperations"] == 4
    assert standings["tit_for_tat"]["cooperation_rate"] == pytest.approx(4 / 6)


def test_list_is_paginated_and_newest_first(client, configuration):
    assert client.get("/api/v1/tournaments").json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }
    first = client.post("/api/v1/tournaments", json=configuration).json()
    second = client.post("/api/v1/tournaments", json=configuration).json()
    page = client.get("/api/v1/tournaments?limit=1&offset=0").json()
    assert page == {"items": [second], "total": 2, "limit": 1, "offset": 0}
    assert client.get("/api/v1/tournaments?limit=1&offset=1").json()["items"] == [first]
    assert client.get("/api/v1/tournaments?offset=2").json()["items"] == []


@pytest.mark.parametrize(
    "updates",
    [
        {"strategies": ["always_cooperate"]},
        {"strategies": ["always_cooperate", "always_cooperate"]},
        {"strategies": ["always_cooperate", "unknown"]},
        {"rounds": 0},
        {"rounds": 10_001},
        {"payoffs": {"temptation": 3}},
        {
            "strategies": [
                "tit_for_tat",
                "pavlov",
                "random",
                "always_cooperate",
                "always_defect",
            ],
            "rounds": 10_000,
            "include_self_play": True,
        },
    ],
)
def test_invalid_configuration_is_rejected_without_saving(
    client, configuration, updates
):
    response = client.post("/api/v1/tournaments", json=configuration | updates)
    assert response.status_code == 422
    assert client.get("/api/v1/tournaments").json()["total"] == 0


@pytest.mark.parametrize("path", ["tournaments", "matches"])
def test_unknown_ids_return_404(client, path):
    assert client.get(f"/api/v1/{path}/{uuid4()}").status_code == 404
