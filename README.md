# Prisoner's Dilemma Simulation

Author: Jon Allen

A deterministic Iterated Prisoner's Dilemma engine and FastAPI backend. Configure
round-robin tournaments, inspect leaderboard and match results, and save complete
round histories in PostgreSQL. Five strategies are available: Tit for Tat, Pavlov,
Random, Always Cooperate, and Always Defect.

## Run the backend and PostgreSQL

Requires Docker with Compose:

```bash
cp .env.example .env
# Choose a local password in .env and keep DATABASE_URL consistent with it.
docker compose up --build
```

Open [interactive API documentation](http://localhost:8000/docs).
Compose starts PostgreSQL with a named volume, waits for database health, applies
Alembic migrations, then starts the API on port 8000. This currently starts the
backend and database; there is no frontend service yet.

## Local Python development

Requires Python 3.12 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e './backend[test]'
uvicorn --app-dir backend app.main:app --reload
```

Without `DATABASE_URL`, the API uses temporary in-memory storage. Results disappear
on restart/reload, and each worker has its own data. Use a single worker in this
mode. Health reports `database: "not_configured"`.

To use PostgreSQL from a host Python process:

```bash
cp .env.example .env
# Edit the example values first; this app does not automatically load .env.
set -a
source .env
set +a
docker compose up -d db
python -m alembic -c backend/alembic.ini upgrade head
uvicorn --app-dir backend app.main:app --reload
```

An existing PostgreSQL 16+ server also works: export its `DATABASE_URL` and run the
same migration and server commands. If you change `POSTGRES_PORT`, update the host
`DATABASE_URL` too. Compose sets its own internal URL using the `db` hostname.
A configured but unavailable database never falls back to memory.

## API

Base path: `/api/v1`.

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/health` | Database readiness; `503` when unavailable or unmigrated |
| GET | `/strategies` | Stable strategy IDs, names, and descriptions |
| POST | `/tournaments` | Execute and save a tournament; return `201` and a `Location` header |
| GET | `/tournaments?limit=20&offset=0` | Newest first; `{items, total, limit, offset}`; maximum limit 100 |
| GET | `/tournaments/{id}` | Configuration, leaderboard, match summaries, and UTC creation time |
| GET | `/matches/{id}` | Match summary plus ordered round history and cumulative scores |

Example:

```bash
curl -X POST http://localhost:8000/api/v1/tournaments \
  -H 'Content-Type: application/json' \
  -d '{
    "strategies": ["tit_for_tat", "random", "always_defect"],
    "rounds": 100,
    "seed": 42,
    "include_self_play": false,
    "payoffs": {"temptation": 5, "reward": 3, "punishment": 1, "sucker": 0}
  }'
```

Responses include `id`, `configuration`, `leaderboard`, `matches`, and `created_at`.
Each match summary includes its ID for the match-detail endpoint. Round histories
are only included in match details, keeping tournament responses small.

Inputs require at least two distinct known strategies, integer rounds from 1 to
10,000, a signed 64-bit integer seed, and integer payoffs fitting PostgreSQL INTEGER.
Payoffs must satisfy `temptation > reward > punishment > sucker` and
`2 * reward > temptation + sucker`. Payoffs and the self-play flag have defaults;
strategies, rounds, and seed are required. Booleans and strings are not accepted as
integers. Unknown request fields are rejected. Work is capped at 100,000 total
simulated rounds per tournament, including self-play.

Invalid inputs or malformed UUIDs return `422`; unknown valid UUIDs return `404`.
Database failures return `503` without exposing SQL details. A failed save leaves
no partial tournament behind.

## Storage and migrations

Routes call an application service, which runs the independent simulation engine
and saves through either the in-memory or PostgreSQL store. SQLAlchemy handles
relational persistence; Pydantic defines separate API contracts.

- `tournaments`: UUID, round count, seed, payoff configuration, self-play, timestamp.
- `tournament_strategies`: selected strategy IDs and their original order.
- `matches`: strategy pair, seed, scores, cooperation counts, winner, scheduling order.
- `round_results`: moves, payoffs, and cumulative scores, keyed by match and round.

Foreign keys cascade when a tournament is deleted. Match and round cumulative
scores use BIGINT to support the full allowed payoff range. Leaderboards and
cooperation rates are reconstructed from saved totals without rerunning strategies.
Self-play counts both player positions in a strategy's aggregate statistics.

Apply schema changes explicitly; application startup outside Compose does not
create tables. The initial migration is reversible. See the
[Alembic migration workflow](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
and [SQLAlchemy transaction documentation](https://docs.sqlalchemy.org/en/20/core/connections.html#connect-and-begin-once-from-the-engine)
for the underlying tools.

```bash
python -m alembic -c backend/alembic.ini upgrade head
python -m alembic -c backend/alembic.ini current
# After editing table metadata:
python -m alembic -c backend/alembic.ini revision --autogenerate -m "Describe change"
# Review generated migrations before applying them.
```

## Configuration

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL URL; unset means temporary memory storage |
| `FRONTEND_ORIGINS` | Comma-separated allowed origins; defaults to `http://localhost:5173` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Compose database initialization settings |
| `POSTGRES_PORT` | Host database port in Compose; defaults to 5432 |
| `TEST_DATABASE_URL` | PostgreSQL server for isolated integration-test schemas |

Compose embeds its password in a URL, so use a URL-safe value. For manually supplied
URLs, percent-encode reserved characters in credentials. Keep `.env` uncommitted.

## Tests

```bash
python -m pytest backend/tests
```

That command runs engine and in-memory API tests. PostgreSQL cases are explicitly
skipped unless `TEST_DATABASE_URL` is set. To run the full backend suite:

```bash
export TEST_DATABASE_URL="$DATABASE_URL"
python -m pytest backend/tests
```

Each database test creates a unique schema, applies real Alembic migrations, and
drops only that schema afterward. The test user must have permission to create
schemas; use a development/test database. The suite keeps core simulation and
API checks, plus four PostgreSQL tests for persistence across app restarts,
multi-batch rollback, cascade deletion, and migration upgrade/downgrade consistency.

Or, with Compose:

```bash
docker compose run --rm api sh -c 'TEST_DATABASE_URL="$DATABASE_URL" pytest'
```

The trimmed suite contains **35 test cases**. Latest local run: **31 passed,
4 PostgreSQL tests skipped** because `TEST_DATABASE_URL` was unset. The retained
PostgreSQL tests passed against PostgreSQL 16 before the trim. Docker configuration
is included but container startup has not been verified in this environment.

Legacy root-level tests additionally require NumPy and can be run with
`python -m pytest test_game_state.py` in the original environment.

## Reproducibility and limitations

Identical selected strategy order, configuration, and seed produce identical engine
results in the same runtime. Every matchup derives a stable seed from the tournament
seed and strategy IDs. UUIDs and creation timestamps identify separate executions
and naturally differ. Reordering selected strategies preserves matchup seeds but
can change player positions, so selection order is retained in storage.

Tournaments execute synchronously and retain every round up to the configured work
limit. In-memory results have no persistence or eviction. Analytics endpoints,
frontend charts, and deployment beyond local development remain future work.
