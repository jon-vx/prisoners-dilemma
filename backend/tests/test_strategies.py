import random

from app.simulation.models import HistoryEntry, MatchHistory, Move
from app.simulation.strategies import (
    Pavlov,
    TitForTat,
)


RNG = random.Random(42)


def history(own_move: Move, opponent_move: Move) -> MatchHistory:
    return MatchHistory((HistoryEntry(own_move, opponent_move, 0, 0),))


def test_tit_for_tat_cooperates_first_then_copies_opponent() -> None:
    strategy = TitForTat()

    assert strategy.choose_move(MatchHistory(), RNG) is Move.COOPERATE
    assert (
        strategy.choose_move(history(Move.COOPERATE, Move.DEFECT), RNG) is Move.DEFECT
    )
    assert (
        strategy.choose_move(history(Move.DEFECT, Move.COOPERATE), RNG)
        is Move.COOPERATE
    )


def test_pavlov_cooperates_after_matching_moves_and_defects_after_mismatch() -> None:
    strategy = Pavlov()

    assert strategy.choose_move(MatchHistory(), RNG) is Move.COOPERATE
    assert (
        strategy.choose_move(history(Move.COOPERATE, Move.COOPERATE), RNG)
        is Move.COOPERATE
    )
    assert (
        strategy.choose_move(history(Move.DEFECT, Move.DEFECT), RNG) is Move.COOPERATE
    )
    assert (
        strategy.choose_move(history(Move.COOPERATE, Move.DEFECT), RNG) is Move.DEFECT
    )
