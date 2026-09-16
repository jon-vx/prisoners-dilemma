from dataclasses import dataclass
from numbers import Integral
import random
from typing import Literal

from app.simulation.models import (
    HistoryEntry,
    MatchHistory,
    Move,
    PayoffMatrix,
    RoundResult,
)
from app.simulation.strategies import create_strategy


Winner = Literal["a", "b", "tie"]


@dataclass(frozen=True)
class MatchResult:
    strategy_a: str
    strategy_b: str
    rounds: int
    seed: int
    score_a: int
    score_b: int
    winner: Winner
    cooperations_a: int
    cooperations_b: int
    cooperation_rate_a: float
    cooperation_rate_b: float
    history: tuple[RoundResult, ...]


def run_match(
    strategy_a_key: str,
    strategy_b_key: str,
    rounds: int,
    seed: int,
    payoffs: PayoffMatrix | None = None,
) -> MatchResult:
    if isinstance(rounds, bool) or not isinstance(rounds, Integral):
        raise TypeError("rounds must be an integer")
    if not 1 <= rounds <= 10_000:
        raise ValueError("rounds must be between 1 and 10,000")
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise TypeError("seed must be an integer")

    round_count = int(rounds)
    match_seed = int(seed)
    payoff_matrix = payoffs or PayoffMatrix()
    strategy_a = create_strategy(strategy_a_key)
    strategy_b = create_strategy(strategy_b_key)
    rng = random.Random(match_seed)

    history_a: list[HistoryEntry] = []
    history_b: list[HistoryEntry] = []
    round_results: list[RoundResult] = []
    score_a = 0
    score_b = 0
    cooperations_a = 0
    cooperations_b = 0

    for round_number in range(1, round_count + 1):
        move_a = strategy_a.choose_move(MatchHistory(tuple(history_a)), rng)
        move_b = strategy_b.choose_move(MatchHistory(tuple(history_b)), rng)
        payoff_a, payoff_b = payoff_matrix.score(move_a, move_b)

        score_a += payoff_a
        score_b += payoff_b
        cooperations_a += move_a is Move.COOPERATE
        cooperations_b += move_b is Move.COOPERATE

        round_results.append(
            RoundResult(
                round_number=round_number,
                move_a=move_a,
                move_b=move_b,
                payoff_a=payoff_a,
                payoff_b=payoff_b,
                cumulative_score_a=score_a,
                cumulative_score_b=score_b,
            )
        )
        history_a.append(HistoryEntry(move_a, move_b, payoff_a, payoff_b))
        history_b.append(HistoryEntry(move_b, move_a, payoff_b, payoff_a))

    if score_a > score_b:
        winner: Winner = "a"
    elif score_b > score_a:
        winner = "b"
    else:
        winner = "tie"

    return MatchResult(
        strategy_a=strategy_a_key,
        strategy_b=strategy_b_key,
        rounds=round_count,
        seed=match_seed,
        score_a=score_a,
        score_b=score_b,
        winner=winner,
        cooperations_a=cooperations_a,
        cooperations_b=cooperations_b,
        cooperation_rate_a=cooperations_a / round_count,
        cooperation_rate_b=cooperations_b / round_count,
        history=tuple(round_results),
    )
