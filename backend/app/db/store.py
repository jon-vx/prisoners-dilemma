from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import Connection, Engine, RowMapping

from app.db.models import matches, round_results, tournament_strategies, tournaments
from app.schemas.tournament import (
    MatchDetail,
    MatchSummary,
    TournamentCreate,
    TournamentPage,
    TournamentResponse,
)
from app.services.tournaments import make_tournament_response


class PostgresTournamentStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def save(self, tournament: TournamentResponse, details: list[MatchDetail]) -> None:
        config = tournament.configuration
        # One transaction includes the configuration, all matches, and every round.
        with self.engine.begin() as connection:
            connection.execute(
                tournaments.insert(),
                {
                    "id": tournament.id,
                    "rounds": config.rounds,
                    "seed": config.seed,
                    "include_self_play": config.include_self_play,
                    "created_at": tournament.created_at,
                    **config.payoffs.model_dump(),
                },
            )
            connection.execute(
                tournament_strategies.insert(),
                [
                    {
                        "tournament_id": tournament.id,
                        "strategy_key": key,
                        "position": position,
                    }
                    for position, key in enumerate(config.strategies)
                ],
            )
            connection.execute(
                matches.insert(),
                [
                    {
                        "position": position,
                        **match.model_dump(
                            include={
                                "id",
                                "tournament_id",
                                "strategy_a",
                                "strategy_b",
                                "seed",
                                "score_a",
                                "score_b",
                                "cooperations_a",
                                "cooperations_b",
                                "winner",
                            }
                        ),
                    }
                    for position, match in enumerate(details)
                ],
            )
            for match in details:
                for start in range(0, len(match.history), 1000):
                    connection.execute(
                        round_results.insert(),
                        [
                            {"match_id": match.id, **row.model_dump()}
                            for row in match.history[start : start + 1000]
                        ],
                    )

    @staticmethod
    def _summary(row: RowMapping, rounds: int) -> MatchSummary:
        return MatchSummary(
            **{
                key: row[key]
                for key in MatchSummary.model_fields
                if key not in {"rounds", "cooperation_rate_a", "cooperation_rate_b"}
            },
            rounds=rounds,
            cooperation_rate_a=row["cooperations_a"] / rounds,
            cooperation_rate_b=row["cooperations_b"] / rounds,
        )

    def _tournament(
        self, connection: Connection, row: RowMapping
    ) -> TournamentResponse:
        strategies = (
            connection.execute(
                sa.select(tournament_strategies.c.strategy_key)
                .where(tournament_strategies.c.tournament_id == row["id"])
                .order_by(tournament_strategies.c.position)
            )
            .scalars()
            .all()
        )
        config = TournamentCreate(
            strategies=list(strategies),
            rounds=row["rounds"],
            seed=row["seed"],
            include_self_play=row["include_self_play"],
            payoffs={
                key: row[key]
                for key in ("temptation", "reward", "punishment", "sucker")
            },
        )
        match_rows = connection.execute(
            sa.select(matches)
            .where(matches.c.tournament_id == row["id"])
            .order_by(matches.c.position)
        ).mappings()
        return make_tournament_response(
            row["id"],
            config,
            row["created_at"],
            [self._summary(match, row["rounds"]) for match in match_rows],
        )

    def get_tournament(self, tournament_id: UUID) -> TournamentResponse | None:
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    sa.select(tournaments).where(tournaments.c.id == tournament_id)
                )
                .mappings()
                .first()
            )
            return self._tournament(connection, row) if row is not None else None

    def get_match(self, match_id: UUID) -> MatchDetail | None:
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    sa.select(matches, tournaments.c.rounds)
                    .join(tournaments, matches.c.tournament_id == tournaments.c.id)
                    .where(matches.c.id == match_id)
                )
                .mappings()
                .first()
            )
            if row is None:
                return None
            history = (
                connection.execute(
                    sa.select(round_results)
                    .where(round_results.c.match_id == match_id)
                    .order_by(round_results.c.round_number)
                )
                .mappings()
                .all()
            )
            return MatchDetail(
                **self._summary(row, row["rounds"]).model_dump(), history=history
            )

    def list_tournaments(self, limit: int, offset: int) -> TournamentPage:
        with self.engine.connect() as connection:
            total = connection.scalar(
                sa.select(sa.func.count()).select_from(tournaments)
            )
            rows = (
                connection.execute(
                    sa.select(tournaments)
                    .order_by(tournaments.c.created_at.desc(), tournaments.c.id.desc())
                    .limit(limit)
                    .offset(offset)
                )
                .mappings()
                .all()
            )
            return TournamentPage(
                items=[self._tournament(connection, row) for row in rows],
                total=total,
                limit=limit,
                offset=offset,
            )

    def check_health(self) -> str:
        with self.engine.connect() as connection:
            # Also catches an unmigrated database, not just an unavailable server.
            connection.execute(sa.select(tournaments.c.id).limit(0))
        return "connected"

    def close(self) -> None:
        self.engine.dispose()
