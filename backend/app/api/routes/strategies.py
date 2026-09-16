from fastapi import APIRouter

from app.schemas.strategy import StrategyResponse
from app.simulation.strategies import STRATEGY_REGISTRY


router = APIRouter(tags=["strategies"])

@router.get("/strategies", response_model=list[StrategyResponse])
def list_strategies() -> list[StrategyResponse]:
    return [
        StrategyResponse(
            key=definition.key,
            name=definition.name,
            description=definition.description,
        )
        for definition in STRATEGY_REGISTRY.values()
    ]
