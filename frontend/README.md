# Frontend

Next.js App Router, React, TypeScript, Tailwind CSS v4, shadcn/ui, and Recharts.

The dashboard runs real tournaments through FastAPI. Select strategies, set rounds
and an optional seed, set matches per pairing, optionally enable self-play or edit
payoffs, then run the tournament. Each repeat starts fresh with its own seeded RNG.
Results show a leaderboard and a match selector with cumulative-score charts.

## Development

Use Node.js 20.19+ and npm. Start the backend on port 8000, then:

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000. `API_BASE_URL` defaults to
`http://127.0.0.1:8000/api/v1` and is only used on the Next.js server.
The server loads strategies and checks database status. Browser requests to create
tournaments and retrieve matches go through two Next.js route handlers to FastAPI,
so no browser CORS changes are needed. FastAPI owns simulation, validation, and
persistence; Next.js does not duplicate those services.

The existing Compose setup runs the backend and database; run Next.js locally.

## Main files

- `src/app/layout.tsx`: compact application header and metadata.
- `src/app/page.tsx`: loads strategies and renders the dashboard.
- `src/components/tournament-dashboard.tsx`: tournament form and submission.
- `src/components/tournament-results.tsx`: leaderboard, match selection, and loading.
- `src/components/score-chart.tsx`: Recharts line chart using shadcn chart components.
- `src/app/api/tournaments/route.ts`: forwards tournament creation to FastAPI.
- `src/app/api/matches/[id]/route.ts`: forwards match retrieval to FastAPI.
- `src/lib/api.ts`: server-only backend access.
- `src/lib/types.ts`: shared TypeScript response and configuration types.
- `src/lib/http.ts`: browser response parsing and API errors.
- `src/app/globals.css`: Tailwind and shadcn theme tokens.
- `src/app/site.css`: dashboard layout and responsive styles.
- `src/components/ui/`: shadcn component source files.

Add shadcn components from this directory as needed:

```bash
npx shadcn add select
```

## Checks

```bash
npm run lint
npm run typecheck
npm run build
npm start
```

## Behavior and current limits

- Input settings remain in place after failed requests. Submission is disabled while running.
- The form enforces the backend's round budget and payoff ordering before submitting.
- Matches per pairing defaults to 1. Repeats count toward the 100,000-total-round budget;
  results combine all repeats and the match selector identifies each match number.
- Seeds entered in the browser are limited to JavaScript's safe integer range to avoid rounding.
- Changing settings does not change existing results; each result shows the configuration that produced it.
- Match requests are cancelled on selection changes so an older response cannot replace the current chart.
- Scores, cooperation rates, chart axes, and series names are shown as text. Chart lines also use different dash patterns.
- Saved history browsing and shareable result pages are not implemented. Refreshing clears the displayed result,
  but PostgreSQL-backed runs remain saved and retrievable through the API.
- A network failure after creation may leave a saved tournament even if the browser did not receive its response.
