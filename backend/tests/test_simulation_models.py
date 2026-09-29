import pytest

from app.simulation.models import HistoryEntry, MatchHistory, Move, PayoffMatrix


def test_history_snapshots_remain_read_only_and_stop_at_their_original_round():
    entries = []
    empty = MatchHistory(entries)
    first = HistoryEntry(Move.COOPERATE, Move.DEFECT, 0, 5)
    entries.append(first)
    snapshot = MatchHistory(entries)
    original_hash = hash(snapshot)
    entries.append(HistoryEntry(Move.DEFECT, Move.DEFECT, 1, 1))

    assert empty.rounds == ()
    assert empty.last_round is None
    assert snapshot.last_round is first
    assert snapshot.rounds == (first,)
    assert snapshot == MatchHistory(rounds=(first,))
    assert hash(snapshot) == original_hash == hash(MatchHistory((first,)))
    assert snapshot != MatchHistory(entries)
    with pytest.raises(IndexError):
        snapshot.rounds[1]
    with pytest.raises(TypeError):
        snapshot.rounds[0] = first
    with pytest.raises(AttributeError):
        snapshot.rounds = ()
    with pytest.raises(AttributeError):
        first.own_move = Move.DEFECT


def test_default_payoff_matrix_scores_all_outcomes() -> None:
    payoffs = PayoffMatrix()

    assert payoffs.score(Move.COOPERATE, Move.COOPERATE) == (3, 3)
    assert payoffs.score(Move.COOPERATE, Move.DEFECT) == (0, 5)
    assert payoffs.score(Move.DEFECT, Move.COOPERATE) == (5, 0)
    assert payoffs.score(Move.DEFECT, Move.DEFECT) == (1, 1)


@pytest.mark.parametrize(
    "values",
    [
        (3, 3, 1, 0),
        (5, 3, 3, 0),
        (5, 3, 1, 1),
        (6, 3, 1, 0),
    ],
)
def test_invalid_payoff_matrix_is_rejected(values: tuple[int, int, int, int]) -> None:
    with pytest.raises(ValueError):
        PayoffMatrix(*values)


def test_payoff_values_must_be_integers() -> None:
    with pytest.raises(TypeError):
        PayoffMatrix(temptation=5.5)
