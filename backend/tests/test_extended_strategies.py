import random
from unittest.mock import Mock

import pytest

from app.simulation.match import run_match
from app.simulation.models import HistoryEntry, MatchHistory, Move, PayoffMatrix
from app.simulation.strategies import STRATEGY_REGISTRY, create_strategy


C = Move.COOPERATE
D = Move.DEFECT


def play(key, opponents, rng=None, payoffs=None):
    strategy = create_strategy(key)
    entries = []
    moves = []
    rng = rng if rng is not None else random.Random(42)
    payoffs = payoffs if payoffs is not None else PayoffMatrix()
    for opponent in opponents:
        move = strategy.choose_move(MatchHistory(entries), rng)
        moves.append("C" if move is C else "D")
        opponent_move = C if opponent == "C" else D
        own_score, opponent_score = payoffs.score(move, opponent_move)
        entries.append(HistoryEntry(move, opponent_move, own_score, opponent_score))
    return "".join(moves)


@pytest.mark.parametrize("key,opponents,expected", [
    ("grim_trigger", "CDCCCC", "CCDDDD"),
    ("tit_for_two_tats", "CDDCCC", "CCCDCC"),
    ("two_tits_for_tat", "CDCCCC", "CCDDCC"),
    ("hard_tit_for_tat", "CDCCCC", "CCDDDC"),
    ("suspicious_tit_for_tat", "CDCC", "DCDC"),
    ("gradual", "DDDDDDDDDD", "CDCCDDDDCC"),
    ("soft_majority", "DCCC", "CDCC"),
    ("hard_majority", "DCCC", "DDDC"),
    ("alternate", "CCCCCC", "CDCDCD"),
    ("detective", "CCCCCCC", "CDCCDDD"),
    ("detective", "CDCDCCC", "CDCCDCC"),
    ("handshake", "CDCCCC", "CDCCCC"),
    ("handshake", "CCCCCC", "CDDDDD"),
    ("contrite_tit_for_tat", "CDCC", "CCDC"),
    ("adaptive", "CCCCCCCCCCCCCC", "CCCCCCDDDDDDDD"),
])
def test_scripted_behavior(key, opponents, expected):
    assert play(key, opponents) == expected


def test_adaptive_uses_average_payoff_and_cooperates_on_ties():
    # C earns 3 on average; five D rounds earn (5 + 4 * 1) / 5.
    assert play("adaptive", "CCCCCCCDDDDCC") == "CCCCCCDDDDDCC"
    # C earns 3; D earns (3 * 5 + 2 * 0) / 5 = 3. Ties cooperate.
    payoffs = PayoffMatrix(temptation=5, reward=3, punishment=0, sucker=-1)
    assert play("adaptive", "CCCCCCCCCDDCC", payoffs=payoffs) == "CCCCCCDDDDDCC"


@pytest.mark.parametrize("key,draw,expected", [
    ("generous_tit_for_tat", 0.09, "CCC"),
    ("generous_tit_for_tat", 0.1, "CDD"),
    ("naive_prober", 0.09, "DDD"),
    ("naive_prober", 0.1, "CCC"),
    ("random_cooperate_bias", 0.69, "CCC"),
    ("random_cooperate_bias", 0.7, "DDD"),
    ("random_defect_bias", 0.29, "CCC"),
    ("random_defect_bias", 0.3, "DDD"),
])
def test_probability_boundaries(key, draw, expected):
    rng = Mock(spec=random.Random)
    rng.random.return_value = draw
    opponents = "DDD" if key == "generous_tit_for_tat" else "CCC"
    assert play(key, opponents, rng=rng) == expected


def test_remorseful_prober_forgives_retaliation_after_a_probe():
    rng = Mock(spec=random.Random)
    rng.random.side_effect = [0.01, 0.9]
    assert play("remorseful_prober", "DCC", rng=rng) == "DCC"


def test_contrite_tit_for_tat_recovers_from_execution_error():
    strategy = create_strategy("contrite_tit_for_tat")
    rng = random.Random(1)
    entries = []
    assert strategy.choose_move(MatchHistory(entries), rng) is C
    # Simulate noise flipping intended cooperation to defection.
    entries.append(HistoryEntry(D, C, 5, 0))
    assert strategy.choose_move(MatchHistory(entries), rng) is C
    entries.append(HistoryEntry(C, D, 0, 5))
    assert strategy.choose_move(MatchHistory(entries), rng) is C
    entries.append(HistoryEntry(C, C, 3, 3))
    assert strategy.choose_move(MatchHistory(entries), rng) is C
    entries.append(HistoryEntry(C, D, 0, 5))
    assert strategy.choose_move(MatchHistory(entries), rng) is D


@pytest.mark.parametrize("key", STRATEGY_REGISTRY)
def test_strategies_are_reproducible_and_match_state_is_isolated(key):
    first = run_match(key, "random", rounds=100, seed=42)
    run_match(key, "always_defect", rounds=100, seed=3)
    assert run_match(key, "random", rounds=100, seed=42) == first
    assert create_strategy(key) is not create_strategy(key)


def test_handshake_self_play_recognizes_both_independent_players():
    result = run_match("handshake", "handshake", rounds=20, seed=1)
    assert result.score_a == result.score_b == 58
