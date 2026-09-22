from fastapi import APIRouter, Response
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.tournaments import Store
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health", response_model=HealthResponse, responses={503: {"model": HealthResponse}}
)
def get_health(store: Store, response: Response) -> HealthResponse:
    try:
        database = store.check_health()
    except SQLAlchemyError:
        response.status_code = 503
        return HealthResponse(status="error", database="unavailable")
    return HealthResponse(status="ok", database=database)
