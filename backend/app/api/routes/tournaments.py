from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response

from app.api.dependencies import Store
from app.schemas.tournament import (
    MatchDetail,
    TournamentCreate,
    TournamentPage,
    TournamentResponse,
)
from app.services.tournaments import create_tournament

router = APIRouter(tags=["tournaments"])


@router.post("/tournaments", response_model=TournamentResponse, status_code=201)
def post_tournament(
    configuration: TournamentCreate, store: Store, response: Response
) -> TournamentResponse:
    result = create_tournament(configuration, store)
    response.headers["Location"] = f"/api/v1/tournaments/{result.id}"
    return result


@router.get("/tournaments", response_model=TournamentPage)
def list_tournaments(
    store: Store,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TournamentPage:
    return store.list_tournaments(limit, offset)


@router.get("/tournaments/{tournament_id}", response_model=TournamentResponse)
def get_tournament(tournament_id: UUID, store: Store) -> TournamentResponse:
    result = store.get_tournament(tournament_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return result


@router.get("/matches/{match_id}", response_model=MatchDetail)
def get_match(match_id: UUID, store: Store) -> MatchDetail:
    result = store.get_match(match_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return result
