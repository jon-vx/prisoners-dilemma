from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import islice
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


@dataclass(frozen=True, init=False, eq=False)
class MatchHistory:
    """A fixed view of an append-only history, with tuple conversion on demand."""

    _entries: Sequence[HistoryEntry] = field(repr=False)
    _length: int

    def __init__(self, rounds: Sequence[HistoryEntry] = ()) -> None:
        object.__setattr__(self, "_entries", rounds)
        object.__setattr__(self, "_length", len(rounds))

    @property
    def rounds(self) -> tuple[HistoryEntry, ...]:
        return tuple(islice(self._entries, self._length))

    @property
    def last_round(self) -> HistoryEntry | None:
        return self._entries[self._length - 1] if self._length else None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MatchHistory):
            return NotImplemented
        return self.rounds == other.rounds

    def __hash__(self) -> int:
        return hash((self.rounds,))


@dataclass(frozen=True)
class RoundResult:
    round_number: int
    move_a: Move
    move_b: Move
    payoff_a: int
    payoff_b: int
    cumulative_score_a: int
    cumulative_score_b: int
