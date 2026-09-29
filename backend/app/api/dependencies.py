from typing import Annotated

from fastapi import Depends, Request

from app.services.storage import TournamentStore


def get_store(request: Request) -> TournamentStore:
    return request.app.state.tournament_store


Store = Annotated[TournamentStore, Depends(get_store)]
