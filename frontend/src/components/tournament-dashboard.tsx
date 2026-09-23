"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { TournamentResults } from "@/components/tournament-results";
import { readResponse } from "@/lib/http";
import type { Strategy, Tournament } from "@/lib/types";

const defaultPayoffs = {
  temptation: "5",
  reward: "3",
  punishment: "1",
  sucker: "0",
};
const payoffFields = [
  { key: "temptation", label: "Temptation" },
  { key: "reward", label: "Reward" },
  { key: "punishment", label: "Punishment" },
  { key: "sucker", label: "Sucker" },
] as const;

export function TournamentDashboard({
  strategies,
  persistent,
}: {
  strategies: Strategy[];
  persistent: boolean;
}) {
  const [selected, setSelected] = useState(
    strategies.map((strategy) => strategy.key),
  );
  const [rounds, setRounds] = useState("100");
  const [seed, setSeed] = useState("42");
  const [selfPlay, setSelfPlay] = useState(false);
  const [payoffs, setPayoffs] = useState(defaultPayoffs);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Tournament | null>(null);
  const pairCount =
    (selected.length * (selected.length - 1)) / 2 +
    (selfPlay ? selected.length : 0);

  async function run(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (selected.length < 2) {
      setError("Select at least two strategies.");
      return;
    }
    const count = Number(rounds);
    if (
      !Number.isInteger(count) ||
      count < 1 ||
      count > 10000 ||
      count * pairCount > 100000
    ) {
      setError(
        "Use 1–10,000 rounds per match, with no more than 100,000 rounds across all matches.",
      );
      return;
    }
    if (!Number.isSafeInteger(Number(seed))) {
      setError(
        "Use a whole-number seed between −9,007,199,254,740,991 and 9,007,199,254,740,991.",
      );
      return;
    }
    const matrix = {
      temptation: Number(payoffs.temptation),
      reward: Number(payoffs.reward),
      punishment: Number(payoffs.punishment),
      sucker: Number(payoffs.sucker),
    };
    if (!(
      matrix.temptation > matrix.reward &&
      matrix.reward > matrix.punishment &&
      matrix.punishment > matrix.sucker &&
      2 * matrix.reward > matrix.temptation + matrix.sucker
    )) {
      setError(
        "Payoffs must satisfy temptation > reward > punishment > sucker, and twice the reward must exceed temptation + sucker.",
      );
      return;
    }
    setPending(true);
    try {
      const response = await fetch("/api/tournaments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategies: selected,
          rounds: count,
          seed: Number(seed),
          include_self_play: selfPlay,
          payoffs: matrix,
        }),
      });
      const tournament = await readResponse<Tournament>(response);
      setResult(tournament);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Could not run the tournament. Your settings have been kept.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="dashboard">
      <aside className="settings">
        <h1>New tournament</h1>
        <form onSubmit={run}>
          <fieldset disabled={pending}>
            <legend>Strategies</legend>
            <div className="strategy-options">
              {strategies.map((strategy) => (
                <div className="strategy-option" key={strategy.key}>
                  <Checkbox
                    id={strategy.key}
                    checked={selected.includes(strategy.key)}
                    onCheckedChange={(checked) =>
                      setSelected((keys) =>
                        checked === true
                          ? [...keys, strategy.key]
                          : keys.filter((key) => key !== strategy.key),
                      )
                    }
                    aria-describedby={`${strategy.key}-description`}
                  />
                  <div>
                    <Label htmlFor={strategy.key}>{strategy.name}</Label>
                    <p id={`${strategy.key}-description`}>
                      {strategy.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            <div className="input-grid">
              <div>
                <Label htmlFor="rounds">Rounds per match</Label>
                <Input
                  id="rounds"
                  type="number"
                  min={1}
                  max={10000}
                  step={1}
                  required
                  value={rounds}
                  onChange={(event) => setRounds(event.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="seed">Seed</Label>
                <Input
                  id="seed"
                  type="number"
                  min={Number.MIN_SAFE_INTEGER}
                  max={Number.MAX_SAFE_INTEGER}
                  step={1}
                  required
                  value={seed}
                  onChange={(event) => setSeed(event.target.value)}
                />
              </div>
            </div>
            <div className="self-play">
              <Checkbox
                id="self-play"
                checked={selfPlay}
                onCheckedChange={(checked) => setSelfPlay(checked === true)}
              />
              <Label htmlFor="self-play">Include self-play</Label>
            </div>
            <details className="payoff-settings">
              <summary>Payoff settings</summary>
              <p>
                Points earned for each outcome. The same values apply to every
                match.
              </p>
              <div className="input-grid">
                {payoffFields.map(({ key, label }) => (
                  <div key={key}>
                    <Label htmlFor={key}>{label}</Label>
                    <Input
                      id={key}
                      type="number"
                      min={-(2 ** 31)}
                      max={2 ** 31 - 1}
                      step={1}
                      required
                      value={payoffs[key]}
                      onChange={(event) =>
                        setPayoffs({ ...payoffs, [key]: event.target.value })
                      }
                    />
                  </div>
                ))}
              </div>
              <p>
                Temptation: defect against cooperation. Reward: both cooperate.
                Punishment: both defect. Sucker: cooperate against defection.
              </p>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setPayoffs(defaultPayoffs)}
              >
                Reset payoffs
              </Button>
            </details>
            <p className="run-summary">
              {pairCount} {pairCount === 1 ? "match" : "matches"} ·{" "}
              {Number(rounds) > 0
                ? (pairCount * Number(rounds)).toLocaleString()
                : 0}{" "}
              total rounds
            </p>
            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={selected.length < 2 || pending}
            >
              {pending ? "Running…" : "Run tournament"}
            </Button>
          </fieldset>
          {error && (
            <p className="error-message" role="alert">
              {error}
            </p>
          )}
          {!persistent && (
            <p className="storage-note">
              Results may not persist. Check the database connection before
              running.
            </p>
          )}
        </form>
      </aside>
      <TournamentResults
        key={result?.id ?? "empty"}
        result={result}
        strategies={strategies}
        pending={pending}
      />
    </div>
  );
}
