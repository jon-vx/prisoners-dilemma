from uuid import UUID, uuid4

from alembic import command
from fastapi.testclient import TestClient
import sqlalchemy as sa

from app.db.models import (
    matches,
    metadata,
    round_results,
    tournament_strategies,
    tournaments,
)
from app.db.store import PostgresTournamentStore
from app.main import create_app
from conftest import migration_config

CONFIGURATION = {
    "strategies": ["random", "tit_for_tat", "always_defect"],
    "rounds": 10,
    "seed": 42,
    "include_self_play": True,
}


def test_listing_batches_related_rows_and_preserves_pagination(db_engine):
    with TestClient(create_app(store=PostgresTournamentStore(db_engine))) as client:
        saved = [
            client.post(
                "/api/v1/tournaments",
                json=CONFIGURATION | {"seed": seed, "strategies": strategies},
            ).json()
            for seed, strategies in (
                (1, ["random", "tit_for_tat"]),
                (2, ["always_defect", "tit_for_tat", "random"]),
                (3, ["tit_for_tat", "always_defect"]),
            )
        ]
        statements = []

        def record_query(connection, cursor, statement, parameters, context, many):
            statements.append(statement)

        sa.event.listen(db_engine, "before_cursor_execute", record_query)
        try:
            response = client.get("/api/v1/tournaments?limit=2&offset=1")
        finally:
            sa.event.remove(db_engine, "before_cursor_execute", record_query)

        assert response.status_code == 200
        assert response.json() == {
            "items": [saved[1], saved[0]],
            "total": 3,
            "limit": 2,
            "offset": 1,
        }
        # Count, page, strategies, matches; query count must not grow per item.
        assert len(statements) == 4
        assert client.get("/api/v1/tournaments?offset=3").json()["items"] == []


def test_postgres_survives_app_restart_and_health_checks_database(
    db_engine, monkeypatch
):
    monkeypatch.setenv(
        "DATABASE_URL", db_engine.url.render_as_string(hide_password=False)
    )
    with TestClient(create_app()) as first:
        assert first.get("/api/v1/health").json() == {
            "status": "ok",
            "database": "connected",
        }
        response = first.post(
            "/api/v1/tournaments",
            json=CONFIGURATION
            | {
                "seed": -(2**63),
                "matches_per_pair": 5,
                "payoffs": {
                    "temptation": 2**31 - 1,
                    "reward": 2_000_000_000,
                    "punishment": 1_000_000_000,
                    "sucker": 0,
                },
            },
        )
        assert response.status_code == 201
        saved = response.json()
        assert saved["configuration"]["matches_per_pair"] == 5
        assert len(saved["matches"]) == 30
        assert max(match["score_b"] for match in saved["matches"]) > 2**31 - 1
        match_path = f"/api/v1/matches/{saved['matches'][0]['id']}"
        detail = first.get(match_path).json()

    with TestClient(create_app()) as restarted:
        assert restarted.get(f"/api/v1/tournaments/{saved['id']}").json() == saved
        assert restarted.get(match_path).json() == detail
        assert restarted.get("/api/v1/tournaments").json()["items"] == [saved]

    with db_engine.connect() as connection:
        assert (
            connection.scalar(sa.select(sa.func.count()).select_from(round_results))
            == 300
        )


def test_failed_round_insert_rolls_back_entire_tournament(db_engine, monkeypatch):
    store = PostgresTournamentStore(db_engine)
    save = store.save

    def fail_in_second_batch(tournament, details):
        # The first 1,000 valid round rows are inserted before this constraint fails.
        details[0].history[1000].round_number = 0
        save(tournament, details)

    monkeypatch.setattr(store, "save", fail_in_second_batch)
    with TestClient(create_app(store=store)) as client:
        response = client.post(
            "/api/v1/tournaments", json=CONFIGURATION | {"rounds": 1001}
        )
        assert response.status_code == 503
        assert response.json() == {"detail": "Database operation failed"}
        assert client.get("/api/v1/tournaments").json()["total"] == 0
        with db_engine.connect() as connection:
            for table in (tournaments, tournament_strategies, matches, round_results):
                assert (
                    connection.scalar(sa.select(sa.func.count()).select_from(table))
                    == 0
                )
        monkeypatch.setattr(store, "save", save)
        assert client.post("/api/v1/tournaments", json=CONFIGURATION).status_code == 201


def test_deleting_tournament_cascades_without_removing_other_results(db_engine):
    with TestClient(create_app(store=PostgresTournamentStore(db_engine))) as client:
        first = client.post("/api/v1/tournaments", json=CONFIGURATION).json()
        second = client.post("/api/v1/tournaments", json=CONFIGURATION).json()
        with db_engine.begin() as connection:
            connection.execute(
                tournaments.delete().where(tournaments.c.id == UUID(first["id"]))
            )
        assert client.get(f"/api/v1/tournaments/{first['id']}").status_code == 404
        assert (
            client.get(f"/api/v1/matches/{first['matches'][0]['id']}").status_code
            == 404
        )
        assert client.get(f"/api/v1/tournaments/{second['id']}").json() == second
        with db_engine.connect() as connection:
            for table, count in (
                (tournaments, 1),
                (tournament_strategies, 3),
                (matches, 6),
                (round_results, 60),
            ):
                assert (
                    connection.scalar(sa.select(sa.func.count()).select_from(table))
                    == count
                )


def test_migration_upgrade_downgrade_and_metadata_agree(db_engine):
    with db_engine.begin() as connection:
        config = migration_config(connection)
        command.check(config)
        command.downgrade(config, "base")
        assert not set(metadata.tables).intersection(
            sa.inspect(connection).get_table_names()
        )
        command.upgrade(config, "head")
        command.check(config)
    with TestClient(create_app(store=PostgresTournamentStore(db_engine))) as client:
        assert client.post("/api/v1/tournaments", json=CONFIGURATION).status_code == 201


def test_repeat_count_migration_defaults_existing_tournaments_to_one(db_engine):
    with db_engine.begin() as connection:
        config = migration_config(connection)
        command.downgrade(config, "a15c03909edf")
        tournament_id = uuid4()
        connection.execute(tournaments.insert().values(
            id=tournament_id,
            rounds=10,
            seed=42,
            include_self_play=False,
            temptation=5,
            reward=3,
            punishment=1,
            sucker=0,
        ))
        command.upgrade(config, "head")
        assert connection.scalar(
            sa.select(tournaments.c.matches_per_pair).where(tournaments.c.id == tournament_id)
        ) == 1
