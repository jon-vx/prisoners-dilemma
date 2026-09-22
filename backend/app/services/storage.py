from threading import Lock
from typing import Protocol
from uuid import UUID

from app.schemas.tournament import MatchDetail, TournamentPage, TournamentResponse


class TournamentStore(Protocol):
    def save(
        self, tournament: TournamentResponse, matches: list[MatchDetail]
    ) -> None: ...
    def get_tournament(self, tournament_id: UUID) -> TournamentResponse | None: ...
    def get_match(self, match_id: UUID) -> MatchDetail | None: ...
    def list_tournaments(self, limit: int, offset: int) -> TournamentPage: ...
    def check_health(self) -> str: ...
    def close(self) -> None: ...


class MemoryTournamentStore:
    """Process-local development storage; results disappear on restart."""

    def __init__(self) -> None:
        self._tournaments: dict[UUID, TournamentResponse] = {}
        self._matches: dict[UUID, MatchDetail] = {}
        self._lock = Lock()

    def save(self, tournament: TournamentResponse, matches: list[MatchDetail]) -> None:
        with self._lock:
            self._tournaments[tournament.id] = tournament.model_copy(deep=True)
            self._matches.update(
                {match.id: match.model_copy(deep=True) for match in matches}
            )

    def get_tournament(self, tournament_id: UUID) -> TournamentResponse | None:
        with self._lock:
            result = self._tournaments.get(tournament_id)
            return result.model_copy(deep=True) if result else None

    def get_match(self, match_id: UUID) -> MatchDetail | None:
        with self._lock:
            result = self._matches.get(match_id)
            return result.model_copy(deep=True) if result else None

    def list_tournaments(self, limit: int, offset: int) -> TournamentPage:
        with self._lock:
            ordered = sorted(
                self._tournaments.values(),
                key=lambda item: (item.created_at, item.id),
                reverse=True,
            )
            return TournamentPage(
                items=[
                    item.model_copy(deep=True)
                    for item in ordered[offset : offset + limit]
                ],
                total=len(ordered),
                limit=limit,
                offset=offset,
            )

    def check_health(self) -> str:
        return "not_configured"

    def close(self) -> None:
        pass
