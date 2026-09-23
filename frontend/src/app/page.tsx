import { getHealth, getStrategies } from "@/lib/api";
import { TournamentDashboard } from "@/components/tournament-dashboard";
import { Button } from "@/components/ui/button";

export const dynamic = "force-dynamic";

export default async function Home() {
  const [strategies, health] = await Promise.allSettled([
    getStrategies(),
    getHealth(),
  ]);
  return (
    <main id="main">
      {strategies.status === "rejected" || strategies.value.length === 0 ? (
        <section className="service-error">
          <h1>Tournaments</h1>
          <p>
            The simulation service is unavailable. Start the backend and try
            again.
          </p>
          <form action="/" method="get">
            <Button type="submit">Try again</Button>
          </form>
        </section>
      ) : (
        <TournamentDashboard
          strategies={strategies.value}
          persistent={
            health.status === "fulfilled" &&
            health.value.database === "connected"
          }
        />
      )}
    </main>
  );
}
