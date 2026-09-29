import pytest

from app.simulation.match import run_match
from app.simulation.models import HistoryEntry, Move


def test_retained_strategy_histories_preserve_each_players_past(monkeypatch):
    class RecordingStrategy:
        def __init__(self, move):
            self.move = move
            self.histories = []

        def choose_move(self, history, rng):
            self.histories.append(history)
            return self.move

    players = {
        "cooperator": RecordingStrategy(Move.COOPERATE),
        "defector": RecordingStrategy(Move.DEFECT),
    }
    monkeypatch.setattr("app.simulation.match.create_strategy", players.__getitem__)
    result = run_match("cooperator", "defector", rounds=4, seed=42)

    for key, expected in (
        ("cooperator", HistoryEntry(Move.COOPERATE, Move.DEFECT, 0, 5)),
        ("defector", HistoryEntry(Move.DEFECT, Move.COOPERATE, 5, 0)),
    ):
        histories = players[key].histories
        assert len(histories) == 4
        for completed_rounds, history in enumerate(histories):
            assert history.rounds == (expected,) * completed_rounds
            assert history.last_round == (expected if completed_rounds else None)
    assert (result.score_a, result.score_b) == (0, 20)


def test_match_returns_scores_cooperations_and_round_history() -> None:
    result = run_match("always_cooperate", "always_defect", rounds=3, seed=42)

    assert result.score_a == 0
    assert result.score_b == 15
    assert result.winner == "b"
    assert result.cooperations_a == 3
    assert result.cooperations_b == 0
    assert result.cooperation_rate_a == 1.0
    assert result.cooperation_rate_b == 0.0
    assert len(result.history) == 3
    assert result.history[-1].cumulative_score_a == result.score_a
    assert result.history[-1].cumulative_score_b == result.score_b


def test_strategies_choose_without_seeing_the_opponents_current_move() -> None:
    result = run_match("tit_for_tat", "always_defect", rounds=2, seed=42)

    assert result.history[0].move_a is Move.COOPERATE
    assert result.history[0].move_b is Move.DEFECT
    assert result.history[1].move_a is Move.DEFECT
    assert result.history[1].move_b is Move.DEFECT


def test_different_seeds_can_change_random_results() -> None:
    first = run_match("random", "always_cooperate", rounds=100, seed=1)
    second = run_match("random", "always_cooperate", rounds=100, seed=2)

    assert first.history != second.history
    assert {row.move_a for row in first.history} == {Move.COOPERATE, Move.DEFECT}


def test_strategy_state_does_not_leak_between_matches() -> None:
    first = run_match("tit_for_tat", "always_defect", rounds=2, seed=1)
    second = run_match("tit_for_tat", "always_cooperate", rounds=1, seed=1)

    assert first.history[-1].move_a is Move.DEFECT
    assert second.history[0].move_a is Move.COOPERATE


@pytest.mark.parametrize("rounds", [0, 10_001])
def test_match_rejects_round_counts_outside_limit(rounds: int) -> None:
    with pytest.raises(ValueError):
        run_match("tit_for_tat", "always_defect", rounds=rounds, seed=1)
