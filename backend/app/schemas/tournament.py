"""Validated, database-independent tournament API contracts."""

from datetime import datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
    model_validator,
)

from app.simulation.models import Move, PayoffMatrix
from app.simulation.strategies import STRATEGY_REGISTRY

MAX_TOTAL_ROUNDS = 100_000
Integer = Annotated[int, Field(strict=True)]
PayoffValue = Annotated[int, Field(strict=True, ge=-(2**31), le=2**31 - 1)]


class PayoffConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temptation: PayoffValue = 5
    reward: PayoffValue = 3
    punishment: PayoffValue = 1
    sucker: PayoffValue = 0

    @model_validator(mode="after")
    def validate_incentives(self) -> Self:
        PayoffMatrix(**self.model_dump())
        return self


class TournamentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategies: list[str] = Field(min_length=2, max_length=len(STRATEGY_REGISTRY))
    rounds: Integer = Field(ge=1, le=10_000)
    seed: Integer = Field(ge=-(2**63), le=2**63 - 1)
    include_self_play: StrictBool = False
    payoffs: PayoffConfig = Field(default_factory=PayoffConfig)

    @field_validator("strategies")
    @classmethod
    def validate_strategies(cls, keys: list[str]) -> list[str]:
        if len(set(keys)) != len(keys):
            raise ValueError("strategy identifiers must be unique")
        if any(key not in STRATEGY_REGISTRY for key in keys):
            raise ValueError("unknown strategy identifier")
        return keys

    @model_validator(mode="after")
    def limit_work(self) -> Self:
        count = len(self.strategies)
        matches = count * (count - 1) // 2 + (count if self.include_self_play else 0)
        if matches * self.rounds > MAX_TOTAL_ROUNDS:
            raise ValueError(
                f"a tournament may contain at most {MAX_TOTAL_ROUNDS:,} total rounds"
            )
        return self


class LeaderboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    strategy_key: str
    matches_played: int
    wins: int
    losses: int
    ties: int
    total_score: int
    cooperations: int
    total_rounds: int
    cooperation_rate: float


class MatchSummary(BaseModel):
    id: UUID
    tournament_id: UUID
    strategy_a: str
    strategy_b: str
    rounds: int
    seed: int
    score_a: int
    score_b: int
    winner: Literal["a", "b", "tie"]
    cooperations_a: int
    cooperations_b: int
    cooperation_rate_a: float
    cooperation_rate_b: float


class RoundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    round_number: int
    move_a: Move
    move_b: Move
    payoff_a: int
    payoff_b: int
    cumulative_score_a: int
    cumulative_score_b: int


class MatchDetail(MatchSummary):
    history: list[RoundResponse]


class TournamentResponse(BaseModel):
    id: UUID
    configuration: TournamentCreate
    leaderboard: list[LeaderboardResponse]
    matches: list[MatchSummary]
    created_at: datetime


class TournamentPage(BaseModel):
    items: list[TournamentResponse]
    total: int
    limit: int
    offset: int
