"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ScoreChart } from "@/components/score-chart";
import { readResponse } from "@/lib/http";
import type { MatchDetail, Strategy, Tournament } from "@/lib/types";

const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

export function TournamentResults({
  result,
  strategies,
  pending,
}: {
  result: Tournament | null;
  strategies: Strategy[];
  pending: boolean;
}) {
  const [matchId, setMatchId] = useState(result?.matches[0]?.id ?? "");
  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [matchError, setMatchError] = useState("");
  const [retry, setRetry] = useState(0);
  const name = (key: string) =>
    strategies.find((strategy) => strategy.key === key)?.name ?? key;

  useEffect(() => {
    if (!matchId) return;
    const controller = new AbortController();
    fetch(`/api/matches/${matchId}`, { signal: controller.signal })
      .then(readResponse<MatchDetail>)
      .then((detail) => {
        if (!controller.signal.aborted) setMatch(detail);
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setMatchError(
            error instanceof Error
              ? error.message
              : "Could not load this match.",
          );
      });
    return () => controller.abort();
  }, [matchId, retry]);

  function chooseMatch(id: string) {
    setMatch(null);
    setMatchError("");
    setMatchId(id);
  }

  return (
    <section
      className="results"
      aria-labelledby="results-title"
      aria-busy={pending}
    >
      <div className="results-heading">
        <h2 id="results-title">Results</h2>
        <p role="status">
          {pending
            ? "Running tournament…"
            : result
              ? `${result.matches.length} ${result.matches.length === 1 ? "match" : "matches"} · ${result.configuration.rounds} rounds each · seed ${result.configuration.seed}`
              : "No tournament run yet"}
        </p>
      </div>
      {!result ? (
        <div className="empty-results">
          <h3>Run a tournament to compare strategies.</h3>
          <p>
            Choose at least two strategies and set the number of rounds. Scores
            and match details will appear here.
          </p>
        </div>
      ) : (
        <>
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label="Tournament leaderboard"
          >
            <table className="results-table">
              <caption>Leaderboard</caption>
              <thead>
                <tr>
                  <th scope="col">Rank</th>
                  <th scope="col">Strategy</th>
                  <th scope="col">Score</th>
                  <th scope="col">W</th>
                  <th scope="col">L</th>
                  <th scope="col">T</th>
                  <th scope="col">Cooperation</th>
                </tr>
              </thead>
              <tbody>
                {result.leaderboard.map((entry) => (
                  <tr key={entry.strategy_key}>
                    <td>{entry.rank}</td>
                    <th scope="row">{name(entry.strategy_key)}</th>
                    <td>{entry.total_score.toLocaleString()}</td>
                    <td>{entry.wins}</td>
                    <td>{entry.losses}</td>
                    <td>{entry.ties}</td>
                    <td>{percent(entry.cooperation_rate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <section className="match-section" aria-labelledby="match-title">
            <div className="match-heading">
              <h2 id="match-title">Match details</h2>
              <div>
                <Label htmlFor="match">Match</Label>
                <select
                  id="match"
                  value={matchId}
                  onChange={(event) => chooseMatch(event.target.value)}
                >
                  {result.matches.map((item) => (
                    <option key={item.id} value={item.id}>
                      {name(item.strategy_a)} vs {name(item.strategy_b)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {matchError ? (
              <div className="error-message" role="alert">
                <p>{matchError}</p>
                <Button
                  variant="outline"
                  className="mt-2"
                  onClick={() => {
                    setMatchError("");
                    setRetry((value) => value + 1);
                  }}
                >
                  Retry match
                </Button>
              </div>
            ) : !match ? (
              <p className="chart-loading" role="status">
                Loading match…
              </p>
            ) : (
              <>
                <div className="match-totals">
                  <p>
                    {name(match.strategy_a)}{" "}
                    <strong>{match.score_a.toLocaleString()}</strong>
                    <span>{percent(match.cooperation_rate_a)} cooperation</span>
                  </p>
                  <p>
                    {name(match.strategy_b)}{" "}
                    <strong>{match.score_b.toLocaleString()}</strong>
                    <span>{percent(match.cooperation_rate_b)} cooperation</span>
                  </p>
                </div>
                <h3 className="chart-title">Cumulative score by round</h3>
                <ScoreChart
                  match={match}
                  nameA={name(match.strategy_a)}
                  nameB={name(match.strategy_b)}
                />
              </>
            )}
          </section>
        </>
      )}
    </section>
  );
}
