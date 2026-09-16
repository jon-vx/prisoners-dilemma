from fastapi import APIRouter

from app.schemas.strategy import StrategyResponse


router = APIRouter(tags=["strategies"])

STRATEGIES = (
    StrategyResponse(
        key="tit_for_tat",
        name="Tit for Tat",
        description="Cooperates first, then copies the opponent's previous move.",
    ),
    StrategyResponse(
        key="pavlov",
        name="Pavlov",
        description="Repeats successful behavior and switches after an unfavorable result.",
    ),
    StrategyResponse(
        key="random",
        name="Random",
        description="Chooses cooperate or defect using the match's seeded random generator.",
    ),
    StrategyResponse(
        key="always_cooperate",
        name="Always Cooperate",
        description="Cooperates every round.",
    ),
    StrategyResponse(
        key="always_defect",
        name="Always Defect",
        description="Defects every round.",
    ),
)


@router.get("/strategies", response_model=list[StrategyResponse])
def list_strategies() -> list[StrategyResponse]:
    return list(STRATEGIES)
