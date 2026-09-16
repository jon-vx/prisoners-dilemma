import pytest

from app.simulation.models import Move, PayoffMatrix


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
