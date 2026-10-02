from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
import random

from app.simulation.models import MatchHistory, Move


class Strategy(ABC):
    """One instance per player per match; choose_move is called once per round."""

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


class GrimTrigger(Strategy):
    def __init__(self) -> None:
        self.triggered = False

    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        if history.last_round and history.last_round.opponent_move is Move.DEFECT:
            self.triggered = True
        return Move.DEFECT if self.triggered else Move.COOPERATE


class WindowRetaliator(Strategy):
    window = 2
    require_all = False

    def __init__(self) -> None:
        self.moves: deque[Move] = deque(maxlen=self.window)

    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        if history.last_round:
            self.moves.append(history.last_round.opponent_move)
        if self.require_all:
            retaliate = len(self.moves) == self.window and all(
                move is Move.DEFECT for move in self.moves
            )
        else:
            retaliate = Move.DEFECT in self.moves
        return Move.DEFECT if retaliate else Move.COOPERATE


class TitForTwoTats(WindowRetaliator):
    require_all = True


class TwoTitsForTat(WindowRetaliator):
    pass


class HardTitForTat(WindowRetaliator):
    window = 3


class GenerousTitForTat(TitForTat):
    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        move = super().choose_move(history, rng)
        if move is Move.DEFECT and rng.random() < 0.1:
            return Move.COOPERATE
        return move


class SuspiciousTitForTat(TitForTat):
    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        if history.last_round is None:
            return Move.DEFECT
        return super().choose_move(history, rng)


class Gradual(Strategy):
    def __init__(self) -> None:
        self.defections = 0
        self.punishment = 0
        self.calm = 0

    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        betrayed = history.last_round and history.last_round.opponent_move is Move.DEFECT
        if betrayed:
            self.defections += 1
        if self.punishment:
            self.punishment -= 1
            return Move.DEFECT
        if self.calm:
            self.calm -= 1
            return Move.COOPERATE
        if betrayed:
            self.punishment = self.defections - 1
            self.calm = 2
            return Move.DEFECT
        return Move.COOPERATE


class NaiveProber(TitForTat):
    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        move = super().choose_move(history, rng)
        if move is Move.COOPERATE and rng.random() < 0.1:
            return Move.DEFECT
        return move


class RemorsefulProber(NaiveProber):
    def __init__(self) -> None:
        self.probed = False

    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        if self.probed and history.last_round and history.last_round.opponent_move is Move.DEFECT:
            self.probed = False
            return Move.COOPERATE
        baseline = TitForTat.choose_move(self, history, rng)
        move = super().choose_move(history, rng)
        self.probed = baseline is Move.COOPERATE and move is Move.DEFECT
        return move


class SoftMajority(Strategy):
    defect_on_tie = False

    def __init__(self) -> None:
        self.balance = 0

    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        if history.last_round:
            self.balance += 1 if history.last_round.opponent_move is Move.COOPERATE else -1
        if self.balance < 0 or (self.balance == 0 and self.defect_on_tie):
            return Move.DEFECT
        return Move.COOPERATE


class HardMajority(SoftMajority):
    defect_on_tie = True


class Adaptive(Strategy):
    opening = (Move.COOPERATE,) * 6 + (Move.DEFECT,) * 5

    def __init__(self) -> None:
        self.turn = 0
        self.scores = {Move.COOPERATE: 0, Move.DEFECT: 0}
        self.counts = {Move.COOPERATE: 0, Move.DEFECT: 0}

    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        previous = history.last_round
        if previous:
            self.scores[previous.own_move] += previous.own_payoff
            self.counts[previous.own_move] += 1
        if self.turn < len(self.opening):
            move = self.opening[self.turn]
        else:
            cooperate_average = self.scores[Move.COOPERATE] / self.counts[Move.COOPERATE]
            defect_average = self.scores[Move.DEFECT] / self.counts[Move.DEFECT]
            move = Move.COOPERATE if cooperate_average >= defect_average else Move.DEFECT
        self.turn += 1
        return move


class RandomCooperateBias(Strategy):
    cooperation_probability = 0.7

    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        return Move.COOPERATE if rng.random() < self.cooperation_probability else Move.DEFECT


class RandomDefectBias(RandomCooperateBias):
    cooperation_probability = 0.3


class Alternate(Strategy):
    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        if history.last_round and history.last_round.own_move is Move.COOPERATE:
            return Move.DEFECT
        return Move.COOPERATE


class Detective(Strategy):
    opening = (Move.COOPERATE, Move.DEFECT, Move.COOPERATE, Move.COOPERATE)

    def __init__(self) -> None:
        self.turn = 0
        self.saw_defection = False

    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        if self.turn <= len(self.opening) and history.last_round:
            self.saw_defection |= history.last_round.opponent_move is Move.DEFECT
        if self.turn < len(self.opening):
            move = self.opening[self.turn]
        elif self.saw_defection:
            move = history.last_round.opponent_move
        else:
            move = Move.DEFECT
        self.turn += 1
        return move


class Handshake(Strategy):
    opening = (Move.COOPERATE, Move.DEFECT)

    def __init__(self) -> None:
        self.turn = 0
        self.matched = True

    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        if 0 < self.turn <= len(self.opening) and history.last_round:
            self.matched &= history.last_round.opponent_move is self.opening[self.turn - 1]
        if self.turn < len(self.opening):
            move = self.opening[self.turn]
        else:
            move = Move.COOPERATE if self.matched else Move.DEFECT
        self.turn += 1
        return move


class ContriteTitForTat(TitForTat):
    def __init__(self) -> None:
        self.intended = Move.COOPERATE
        self.contrite = False

    def choose_move(self, history: MatchHistory, rng: random.Random) -> Move:
        previous = history.last_round
        if previous:
            if self.intended is Move.COOPERATE and previous.own_move is Move.DEFECT:
                self.contrite = True
            elif previous.own_move is previous.opponent_move is Move.COOPERATE:
                self.contrite = False
        self.intended = Move.COOPERATE if self.contrite else super().choose_move(history, rng)
        return self.intended


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


for key, name, description, factory in (
    ("grim_trigger", "Grim Trigger", "Cooperates until the first opponent defection, then defects forever.", GrimTrigger),
    ("tit_for_two_tats", "Tit for Two Tats", "Defects only after two consecutive opponent defections.", TitForTwoTats),
    ("two_tits_for_tat", "Two Tits for Tat", "Defects if either of the last two opponent moves was a defection.", TwoTitsForTat),
    ("generous_tit_for_tat", "Generous Tit for Tat", "Copies the opponent, with a 10% chance of forgiving a defection.", GenerousTitForTat),
    ("suspicious_tit_for_tat", "Suspicious Tit for Tat", "Defects first, then copies the opponent's previous move.", SuspiciousTitForTat),
    ("gradual", "Gradual", "Counts all opponent defections; when idle, punishes a new defection for that many rounds, then cooperates twice.", Gradual),
    ("naive_prober", "Naive Prober", "Tit for Tat with a 10% chance of defecting instead of cooperating.", NaiveProber),
    ("remorseful_prober", "Remorseful Prober", "Probes like Naive Prober, but cooperates if the opponent defects immediately after a probe.", RemorsefulProber),
    ("hard_tit_for_tat", "Hard Tit for Tat", "Defects if any of the last three opponent moves was a defection.", HardTitForTat),
    ("soft_majority", "Soft Majority", "Cooperates first and when opponent cooperations equal or outnumber defections.", SoftMajority),
    ("hard_majority", "Hard Majority", "Cooperates only when opponent cooperations strictly outnumber defections; defects first.", HardMajority),
    ("adaptive", "Adaptive", "Plays six cooperations then five defections; thereafter picks the move with the higher average payoff, cooperating on ties.", Adaptive),
    ("random_cooperate_bias", "Random Cooperate Bias", "Independently cooperates with 70% probability each round.", RandomCooperateBias),
    ("random_defect_bias", "Random Defect Bias", "Independently cooperates with 30% probability each round.", RandomDefectBias),
    ("alternate", "Alternate", "Starts with cooperation, then switches its own move every round (Always Switch).", Alternate),
    ("detective", "Detective", "Opens C, D, C, C; uses Tit for Tat if the opponent defected in those four rounds, otherwise defects forever.", Detective),
    ("handshake", "Handshake", "Opens C, D; then cooperates forever with opponents matching that opening and defects against others.", Handshake),
    ("contrite_tit_for_tat", "Contrite Tit for Tat", "Copies the opponent; after an accidental own defection, cooperates until mutual cooperation returns. Without noise, behaves like Tit for Tat.", ContriteTitForTat),
):
    STRATEGY_REGISTRY[key] = StrategyDefinition(key, name, description, factory)


def create_strategy(strategy_key: str) -> Strategy:
    try:
        definition = STRATEGY_REGISTRY[strategy_key]
    except KeyError as error:
        raise ValueError(f"unknown strategy: {strategy_key}") from error
    return definition.factory()
