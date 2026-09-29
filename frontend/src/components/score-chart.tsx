"use client";

import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart";
import type { MatchDetail } from "@/lib/types";

export function ScoreChart({
  match,
  nameA,
  nameB,
}: {
  match: MatchDetail;
  nameA: string;
  nameB: string;
}) {
  const config = {
    cumulative_score_a: { label: `${nameA} (A)`, color: "var(--chart-1)" },
    cumulative_score_b: { label: `${nameB} (B)`, color: "var(--chart-2)" },
  };
  return (
    <ChartContainer config={config} className="h-72 w-full">
      <LineChart
        accessibilityLayer
        data={match.history}
        margin={{ top: 10, right: 15, left: 0, bottom: 20 }}
      >
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey="round_number"
          type="number"
          domain={match.rounds === 1 ? [0, 1] : [1, match.rounds]}
          allowDecimals={false}
          tickLine={false}
          label={{ value: "Round", position: "insideBottom", offset: -10 }}
        />
        <YAxis
          width={65}
          tickLine={false}
          label={{ value: "Score", angle: -90, position: "insideLeft" }}
        />
        <ChartTooltip
          content={
            <ChartTooltipContent labelFormatter={(value) => `Round ${value}`} />
          }
        />
        <ChartLegend content={<ChartLegendContent />} verticalAlign="top" />
        <Line
          type="linear"
          dataKey="cumulative_score_a"
          stroke="var(--color-cumulative_score_a)"
          strokeWidth={2}
          dot={match.rounds === 1}
          isAnimationActive={false}
        />
        <Line
          type="linear"
          dataKey="cumulative_score_b"
          stroke="var(--color-cumulative_score_b)"
          strokeWidth={2}
          dot={match.rounds === 1}
          isAnimationActive={false}
        />
      </LineChart>
    </ChartContainer>
  );
}
