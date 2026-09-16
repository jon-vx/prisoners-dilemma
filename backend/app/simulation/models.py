from dataclasses import dataclass
from enum import StrEnum
from numbers import Integral


class Move(StrEnum):
    COOPERATE = "cooperate"
    DEFECT = "defect"


@dataclass(frozen=True)
class PayoffMatrix:
    temptation: int = 5
    reward: int = 3
    punishment: int = 1
    sucker: int = 0

    def __post_init__(self) -> None:
        values = (self.temptation, self.reward, self.punishment, self.sucker)
        if any(isinstance(value, bool) or not isinstance(value, Integral) for value in values):
            raise TypeError("payoff values must be integers")
        if not self.temptation > self.reward > self.punishment > self.sucker:
            raise ValueError(
                "payoffs must satisfy temptation > reward > punishment > sucker"
            )
        if 2 * self.reward <= self.temptation + self.sucker:
            raise ValueError(
                "payoffs must satisfy 2 * reward > temptation + sucker"
            )

    def score(self, move_a: Move, move_b: Move) -> tuple[int, int]:
        if move_a is Move.COOPERATE and move_b is Move.COOPERATE:
            return self.reward, self.reward
        if move_a is Move.COOPERATE and move_b is Move.DEFECT:
            return self.sucker, self.temptation
        if move_a is Move.DEFECT and move_b is Move.COOPERATE:
            return self.temptation, self.sucker
        if move_a is Move.DEFECT and move_b is Move.DEFECT:
            return self.punishment, self.punishment
        raise TypeError("moves must be Move values")


@dataclass(frozen=True)
class HistoryEntry:
    own_move: Move
    opponent_move: Move
    own_payoff: int
    opponent_payoff: int


@dataclass(frozen=True)
class MatchHistory:
    rounds: tuple[HistoryEntry, ...] = ()

    @property
    def last_round(self) -> HistoryEntry | None:
        return self.rounds[-1] if self.rounds else None


@dataclass(frozen=True)
class RoundResult:
    round_number: int
    move_a: Move
    move_b: Move
    payoff_a: int
    payoff_b: int
    cumulative_score_a: int
    cumulative_score_b: int
