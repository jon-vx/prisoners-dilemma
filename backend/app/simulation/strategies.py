from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
import random

from app.simulation.models import MatchHistory, Move


class Strategy(ABC):
    @abstractmethod
    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        raise NotImplementedError


class TitForTat(Strategy):
    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        previous_round = history.last_round
        if previous_round is None:
            return Move.COOPERATE
        return previous_round.opponent_move


class Pavlov(Strategy):
    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        previous_round = history.last_round
        if previous_round is None:
            return Move.COOPERATE
        if previous_round.own_move is previous_round.opponent_move:
            return Move.COOPERATE
        return Move.DEFECT


class RandomStrategy(Strategy):
    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        return rng.choice((Move.COOPERATE, Move.DEFECT))


class AlwaysCooperate(Strategy):
    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        return Move.COOPERATE


class AlwaysDefect(Strategy):
    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        return Move.DEFECT


@dataclass(frozen=True)
class StrategyDefinition:
    key: str
    name: str
    description: str
    factory: Callable[[], Strategy]


STRATEGY_REGISTRY = {
    "tit_for_tat": StrategyDefinition(
        key="tit_for_tat",
        name="Tit for Tat",
        description="Cooperates first, then copies the opponent's previous move.",
        factory=TitForTat,
    ),
    "pavlov": StrategyDefinition(
        key="pavlov",
        name="Pavlov",
        description="Repeats successful behavior and switches after an unfavorable result.",
        factory=Pavlov,
    ),
    "random": StrategyDefinition(
        key="random",
        name="Random",
        description="Chooses cooperate or defect using the match's seeded random generator.",
        factory=RandomStrategy,
    ),
    "always_cooperate": StrategyDefinition(
        key="always_cooperate",
        name="Always Cooperate",
        description="Cooperates every round.",
        factory=AlwaysCooperate,
    ),
    "always_defect": StrategyDefinition(
        key="always_defect",
        name="Always Defect",
        description="Defects every round.",
        factory=AlwaysDefect,
    ),
}


def create_strategy(strategy_key: str) -> Strategy:
    try:
        definition = STRATEGY_REGISTRY[strategy_key]
    except KeyError as error:
        raise ValueError(f"unknown strategy: {strategy_key}") from error
    return definition.factory()
