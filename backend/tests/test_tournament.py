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
