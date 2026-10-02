from collections import Counter
from itertools import combinations, combinations_with_replacement

import pytest

from app.simulation.tournament import run_tournament


STRATEGIES = (
    "tit_for_tat",
    "pavlov",
    "random",
    "always_defect",
)


def test_round_robin_runs_every_unique_pair_once() -> None:
    result = run_tournament(STRATEGIES, rounds=10, seed=42)

    pairings = [(match.strategy_a, match.strategy_b) for match in result.matches]
    assert len(pairings) == len(STRATEGIES) * (len(STRATEGIES) - 1) // 2
    assert len(set(pairings)) == len(pairings)
    assert all(strategy_a != strategy_b for strategy_a, strategy_b in pairings)


def test_self_play_adds_one_match_for_every_strategy() -> None:
    result = run_tournament(STRATEGIES, rounds=10, seed=42, include_self_play=True)

    self_play_matches = [
        match for match in result.matches if match.strategy_a == match.strategy_b
    ]
    assert len(result.matches) == len(STRATEGIES) * (len(STRATEGIES) + 1) // 2
    assert [match.strategy_a for match in self_play_matches] == list(STRATEGIES)
    # Each self-play match contributes both player positions to the standing.
    assert all(
        entry.matches_played == len(STRATEGIES) + 1 for entry in result.leaderboard
    )


def test_same_tournament_configuration_is_reproducible() -> None:
    first = run_tournament(STRATEGIES, rounds=100, seed=1234)
    second = run_tournament(STRATEGIES, rounds=100, seed=1234)

    assert first == second
    assert len({match.seed for match in first.matches}) == len(first.matches)


def test_leaderboard_aggregates_match_results_and_ranks_by_score() -> None:
    result = run_tournament(("always_cooperate", "always_defect"), rounds=3, seed=42)

    defector, cooperator = result.leaderboard
    assert defector.rank == 1
    assert defector.strategy_key == "always_defect"
    assert defector.matches_played == 1
    assert defector.wins == 1
    assert defector.losses == 0
    assert defector.ties == 0
    assert defector.total_score == 15
    assert defector.cooperation_rate == 0.0
    assert cooperator.rank == 2
    assert cooperator.strategy_key == "always_cooperate"
    assert cooperator.losses == 1
    assert cooperator.total_score == 0
    assert cooperator.cooperation_rate == 1.0


@pytest.mark.parametrize("self_play", [False, True])
def test_repeats_every_pair_with_reproducible_independent_seeds(self_play):
    result = run_tournament(
        STRATEGIES, rounds=20, seed=42, include_self_play=self_play, matches_per_pair=5
    )
    pairings = (combinations_with_replacement if self_play else combinations)(STRATEGIES, 2)
    assert Counter((m.strategy_a, m.strategy_b) for m in result.matches) == {
        pair: 5 for pair in pairings
    }
    assert result.matches_per_pair == 5
    assert len({m.seed for m in result.matches}) == len(result.matches)
    assert result == run_tournament(
        STRATEGIES, rounds=20, seed=42, include_self_play=self_play, matches_per_pair=5
    )
    original = run_tournament(STRATEGIES, rounds=20, seed=42, include_self_play=self_play)
    assert result.matches[::5] == original.matches
    assert all(
        entry.matches_played == (len(STRATEGIES) - 1 + (2 if self_play else 0)) * 5
        for entry in result.leaderboard
    )


def test_repeated_matches_reset_strategy_state_and_aggregate_scores():
    result = run_tournament(
        ("tit_for_tat", "always_defect"), rounds=3, seed=42, matches_per_pair=5
    )
    assert all(match.score_a == 2 and match.score_b == 7 for match in result.matches)
    defector, tit_for_tat = result.leaderboard
    assert defector.total_score == 35
    assert defector.wins == defector.matches_played == 5
    assert tit_for_tat.total_score == 10
    assert tit_for_tat.losses == 5
    assert tit_for_tat.cooperations == 5
    assert tit_for_tat.total_rounds == 15
    assert tit_for_tat.cooperation_rate == pytest.approx(1 / 3)


@pytest.mark.parametrize("repetitions", [0, -1, 10_001])
def test_invalid_repeat_count_is_rejected(repetitions):
    with pytest.raises(ValueError, match="matches_per_pair"):
        run_tournament(STRATEGIES, rounds=1, seed=42, matches_per_pair=repetitions)


@pytest.mark.parametrize("repetitions", [True, 1.5, "5", None])
def test_repeat_count_must_be_an_integer(repetitions):
    with pytest.raises(TypeError, match="matches_per_pair"):
        run_tournament(STRATEGIES, rounds=1, seed=42, matches_per_pair=repetitions)
