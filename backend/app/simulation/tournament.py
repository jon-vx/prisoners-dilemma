from collections.abc import Sequence
from dataclasses import dataclass, replace
import hashlib
from itertools import combinations, combinations_with_replacement
from numbers import Integral

from app.simulation.match import MatchResult, run_match
from app.simulation.models import PayoffMatrix
from app.simulation.strategies import STRATEGY_REGISTRY


@dataclass(frozen=True)
class LeaderboardEntry:
    rank: int
    strategy_key: str
    matches_played: int
    wins: int
    losses: int
    ties: int
    total_score: int
    cooperations: int
    total_rounds: int
    cooperation_rate: float


@dataclass(frozen=True)
class TournamentResult:
    strategy_keys: tuple[str, ...]
    rounds: int
    seed: int
    include_self_play: bool
    payoffs: PayoffMatrix
    matches: tuple[MatchResult, ...]
    leaderboard: tuple[LeaderboardEntry, ...]
    matches_per_pair: int = 1


@dataclass
class _Standing:
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    ties: int = 0
    total_score: int = 0
    cooperations: int = 0
    total_rounds: int = 0


def _derive_match_seed(
    tournament_seed: int, strategy_a: str, strategy_b: str, repetition: int = 0
) -> int:
    first_key, second_key = sorted((strategy_a, strategy_b))
    seed_material = f"{tournament_seed}\0{first_key}\0{second_key}".encode()
    # Preserve existing single-match results while giving repeats independent seeds.
    if repetition:
        seed_material += f"\0{repetition}".encode()
    digest = hashlib.sha256(seed_material).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


def _record_result(
    standing: _Standing,
    *,
    score: int,
    cooperations: int,
    rounds: int,
    outcome: str,
) -> None:
    standing.matches_played += 1
    standing.total_score += score
    standing.cooperations += cooperations
    standing.total_rounds += rounds
    if outcome == "win":
        standing.wins += 1
    elif outcome == "loss":
        standing.losses += 1
    else:
        standing.ties += 1


def build_leaderboard(
    strategy_keys: tuple[str, ...], matches: Sequence[MatchResult]
) -> tuple[LeaderboardEntry, ...]:
    standings = {strategy_key: _Standing() for strategy_key in strategy_keys}

    for match in matches:
        if match.winner == "a":
            outcome_a, outcome_b = "win", "loss"
        elif match.winner == "b":
            outcome_a, outcome_b = "loss", "win"
        else:
            outcome_a = outcome_b = "tie"

        _record_result(
            standings[match.strategy_a],
            score=match.score_a,
            cooperations=match.cooperations_a,
            rounds=match.rounds,
            outcome=outcome_a,
        )
        _record_result(
            standings[match.strategy_b],
            score=match.score_b,
            cooperations=match.cooperations_b,
            rounds=match.rounds,
            outcome=outcome_b,
        )

    unranked = [
        LeaderboardEntry(
            rank=0,
            strategy_key=strategy_key,
            matches_played=standing.matches_played,
            wins=standing.wins,
            losses=standing.losses,
            ties=standing.ties,
            total_score=standing.total_score,
            cooperations=standing.cooperations,
            total_rounds=standing.total_rounds,
            cooperation_rate=(
                standing.cooperations / standing.total_rounds
                if standing.total_rounds
                else 0.0
            ),
        )
        for strategy_key, standing in standings.items()
    ]
    ordered = sorted(
        unranked,
        key=lambda entry: (
            -entry.total_score,
            -entry.wins,
            -entry.cooperation_rate,
            entry.strategy_key,
        ),
    )
    return tuple(
        replace(entry, rank=index) for index, entry in enumerate(ordered, start=1)
    )


def run_tournament(
    strategy_keys: Sequence[str],
    rounds: int,
    seed: int,
    include_self_play: bool = False,
    payoffs: PayoffMatrix | None = None,
    matches_per_pair: int = 1,
) -> TournamentResult:
    if isinstance(strategy_keys, (str, bytes)):
        raise TypeError("strategy_keys must be a sequence of strategy identifiers")
    selected_strategies = tuple(strategy_keys)
    if len(selected_strategies) < 2:
        raise ValueError("at least two strategies are required")
    if len(set(selected_strategies)) != len(selected_strategies):
        raise ValueError("strategy identifiers must be unique")
    unknown_strategies = [
        key for key in selected_strategies if key not in STRATEGY_REGISTRY
    ]
    if unknown_strategies:
        raise ValueError(f"unknown strategy: {unknown_strategies[0]}")
    if isinstance(rounds, bool) or not isinstance(rounds, Integral):
        raise TypeError("rounds must be an integer")
    if not 1 <= rounds <= 10_000:
        raise ValueError("rounds must be between 1 and 10,000")
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise TypeError("seed must be an integer")
    if not isinstance(include_self_play, bool):
        raise TypeError("include_self_play must be a boolean")
    if isinstance(matches_per_pair, bool) or not isinstance(matches_per_pair, Integral):
        raise TypeError("matches_per_pair must be an integer")
    if not 1 <= matches_per_pair <= 10_000:
        raise ValueError("matches_per_pair must be between 1 and 10,000")

    round_count = int(rounds)
    tournament_seed = int(seed)
    payoff_matrix = payoffs or PayoffMatrix()
    pairings = (
        combinations_with_replacement(selected_strategies, 2)
        if include_self_play
        else combinations(selected_strategies, 2)
    )
    matches = tuple(
        run_match(
            strategy_a_key=strategy_a,
            strategy_b_key=strategy_b,
            rounds=round_count,
            seed=_derive_match_seed(tournament_seed, strategy_a, strategy_b, repetition),
            payoffs=payoff_matrix,
        )
        for strategy_a, strategy_b in pairings
        for repetition in range(int(matches_per_pair))
    )

    return TournamentResult(
        strategy_keys=selected_strategies,
        rounds=round_count,
        seed=tournament_seed,
        include_self_play=include_self_play,
        payoffs=payoff_matrix,
        matches=matches,
        leaderboard=build_leaderboard(selected_strategies, matches),
        matches_per_pair=int(matches_per_pair),
    )
