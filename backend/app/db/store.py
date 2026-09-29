from collections.abc import Sequence
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
            id=row["id"],
            tournament_id=row["tournament_id"],
            strategy_a=row["strategy_a"],
            strategy_b=row["strategy_b"],
            seed=row["seed"],
            score_a=row["score_a"],
            score_b=row["score_b"],
            winner=row["winner"],
            cooperations_a=row["cooperations_a"],
            cooperations_b=row["cooperations_b"],
            rounds=rounds,
            cooperation_rate_a=row["cooperations_a"] / rounds,
            cooperation_rate_b=row["cooperations_b"] / rounds,
        )

    def _load_tournaments(
        self, connection: Connection, rows: Sequence[RowMapping]
    ) -> list[TournamentResponse]:
        if not rows:
            return []
        strategies_by_id: dict[UUID, list[str]] = {row["id"]: [] for row in rows}
        matches_by_id: dict[UUID, list[RowMapping]] = {row["id"]: [] for row in rows}
        strategy_rows = connection.execute(
            sa.select(tournament_strategies)
            .where(tournament_strategies.c.tournament_id.in_(strategies_by_id))
            .order_by(tournament_strategies.c.position)
        ).mappings()
        for strategy in strategy_rows:
            strategies_by_id[strategy["tournament_id"]].append(strategy["strategy_key"])
        match_rows = connection.execute(
            sa.select(matches)
            .where(matches.c.tournament_id.in_(matches_by_id))
            .order_by(matches.c.position)
        ).mappings()
        for match in match_rows:
            matches_by_id[match["tournament_id"]].append(match)
        return [
            self._tournament(row, strategies_by_id[row["id"]], matches_by_id[row["id"]])
            for row in rows
        ]

    def _tournament(
        self, row: RowMapping, strategies: list[str], match_rows: list[RowMapping]
    ) -> TournamentResponse:
        config = TournamentCreate(
            strategies=strategies,
            rounds=row["rounds"],
            seed=row["seed"],
            include_self_play=row["include_self_play"],
            payoffs={
                key: row[key]
                for key in ("temptation", "reward", "punishment", "sucker")
            },
        )
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
            if row is None:
                return None
            return self._load_tournaments(connection, [row])[0]

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
                items=self._load_tournaments(connection, rows),
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
