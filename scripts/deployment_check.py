#!/usr/bin/env python3
"""Check frontend proxying, database readiness, and a persisted tournament."""

import argparse
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID


def request(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {} if payload is None else {"Content-Type": "application/json"}
    with urlopen(Request(url, data=data, headers=headers), timeout=10) as response:
        return response.status, response.read()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(api_url, frontend_url, wait_seconds):
    api_url = api_url.rstrip("/")
    frontend_url = frontend_url.rstrip("/")
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            _, body = request(f"{api_url}/health")
            health = json.loads(body)
            require(
                health.get("status") == "ok" and health.get("database") == "connected",
                "API must be healthy and connected to PostgreSQL",
            )
            request(frontend_url)
            break
        except (OSError, URLError, ValueError) as error:
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Readiness deadline exceeded: {error}") from error
            time.sleep(2)

    configuration = {
        "strategies": ["tit_for_tat", "always_defect"],
        "rounds": 10,
        "matches_per_pair": 1,
        "seed": 42,
    }
    # Do not retry creation: a timed-out request may already have persisted data.
    status, body = request(f"{frontend_url}/api/tournaments", configuration)
    require(status == 201, "Frontend tournament creation did not return HTTP 201")
    created = json.loads(body)
    tournament_id = str(UUID(created["id"]))
    for key, value in configuration.items():
        require(created["configuration"][key] == value, f"Unexpected configuration: {key}")

    _, body = request(f"{api_url}/tournaments/{tournament_id}")
    require(json.loads(body) == created, "Retrieved tournament differs from created data")
    require(len(created["matches"]) == 1, "Expected exactly one match")
    require(len(created["leaderboard"]) == 2, "Expected two leaderboard entries")
    match = created["matches"][0]
    match_id = str(UUID(match["id"]))
    _, body = request(f"{frontend_url}/api/matches/{match_id}")
    detail = json.loads(body)
    require(detail["tournament_id"] == tournament_id, "Match belongs to another tournament")
    require(
        [row["round_number"] for row in detail["history"]] == list(range(1, 11)),
        "Match history must contain rounds 1 through 10",
    )
    scores = {detail["strategy_a"]: detail["score_a"], detail["strategy_b"]: detail["score_b"]}
    require(scores == {"tit_for_tat": 9, "always_defect": 14}, "Unexpected seeded match scores")
    require(
        detail["history"][-1]["cumulative_score_a"] == detail["score_a"]
        and detail["history"][-1]["cumulative_score_b"] == detail["score_b"],
        "Final round totals differ from match totals",
    )
    print(f"Deployment check passed: tournament {tournament_id}, match {match_id}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--frontend-url", required=True)
    parser.add_argument("--wait-seconds", type=int, default=60)
    args = parser.parse_args()
    if args.wait_seconds < 0:
        parser.error("--wait-seconds must be nonnegative")
    try:
        run(args.api_url, args.frontend_url, args.wait_seconds)
    except (OSError, HTTPError, URLError, ValueError, KeyError, TypeError, IndexError, RuntimeError) as error:
        print(f"Deployment check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
