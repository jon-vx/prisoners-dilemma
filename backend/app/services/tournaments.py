from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.schemas.tournament import (
    LeaderboardResponse,
    MatchDetail,
    MatchSummary,
    RoundResponse,
    TournamentCreate,
    TournamentResponse,
)
from app.services.storage import TournamentStore
from app.simulation.match import MatchResult
from app.simulation.models import PayoffMatrix
from app.simulation.tournament import build_leaderboard, run_tournament


def make_tournament_response(
    tournament_id: UUID,
    configuration: TournamentCreate,
    created_at: datetime,
    matches: list[MatchSummary],
) -> TournamentResponse:
    # Leaderboards depend only on persisted match totals, never on rerunning a seed.
    results = [
        MatchResult(**match.model_dump(exclude={"id", "tournament_id"}), history=())
        for match in matches
    ]
    return TournamentResponse(
        id=tournament_id,
        configuration=configuration,
        created_at=created_at.astimezone(timezone.utc),
        matches=matches,
        leaderboard=[
            LeaderboardResponse.model_validate(entry)
            for entry in build_leaderboard(tuple(configuration.strategies), results)
        ],
    )


def create_tournament(
    configuration: TournamentCreate, store: TournamentStore
) -> TournamentResponse:
    result = run_tournament(
        configuration.strategies,
        rounds=configuration.rounds,
        matches_per_pair=configuration.matches_per_pair,
        seed=configuration.seed,
        include_self_play=configuration.include_self_play,
        payoffs=PayoffMatrix(**configuration.payoffs.model_dump()),
    )
    tournament_id = uuid4()
    matches = [
        MatchDetail(
            id=uuid4(),
            tournament_id=tournament_id,
            strategy_a=match.strategy_a,
            strategy_b=match.strategy_b,
            rounds=match.rounds,
            seed=match.seed,
            score_a=match.score_a,
            score_b=match.score_b,
            winner=match.winner,
            cooperations_a=match.cooperations_a,
            cooperations_b=match.cooperations_b,
            cooperation_rate_a=match.cooperation_rate_a,
            cooperation_rate_b=match.cooperation_rate_b,
            history=[RoundResponse.model_validate(row) for row in match.history],
        )
        for match in result.matches
    ]
    response = TournamentResponse(
        id=tournament_id,
        configuration=configuration,
        created_at=datetime.now(timezone.utc),
        matches=[
            MatchSummary(**match.model_dump(exclude={"history"})) for match in matches
        ],
        leaderboard=[
            LeaderboardResponse.model_validate(entry) for entry in result.leaderboard
        ],
    )
    store.save(response, matches)
    return response
