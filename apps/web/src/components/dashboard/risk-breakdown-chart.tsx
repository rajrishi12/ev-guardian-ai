"use client";

import { useQuery } from "@tanstack/react-query";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

const COLORS = {
  low: "#00e5a0",
  medium: "#f5a524",
  high: "#ff5c5c",
};

export function RiskBreakdownChart() {
  const { data, isLoading } = useQuery({
    queryKey: ["battery-risk-summary"],
    queryFn: api.battery.fleetRiskSummary,
  });

  const chartData = data
    ? [
        { name: "Low risk", key: "low", value: data.low },
        { name: "Medium risk", key: "medium", value: data.medium },
        { name: "High risk", key: "high", value: data.high },
      ]
    : [];

  const total = data ? data.low + data.medium + data.high : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Battery risk distribution</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-48 animate-pulse rounded-lg bg-surface-elevated" />
        ) : (
          <div className="flex items-center gap-6">
            <div className="relative h-44 w-44 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={3}
                    stroke="none"
                  >
                    {chartData.map((entry) => (
                      <Cell
                        key={entry.key}
                        fill={COLORS[entry.key as keyof typeof COLORS]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: "var(--surface-elevated)",
                      border: "1px solid var(--border-default)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-2xl font-semibold data-mono">
                  {total}
                </span>
                <span className="text-[10px] text-foreground-dim uppercase tracking-wide">
                  vehicles
                </span>
              </div>
            </div>
            <div className="space-y-2.5 flex-1">
              {chartData.map((d) => (
                <div key={d.key} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ background: COLORS[d.key as keyof typeof COLORS] }}
                    />
                    <span className="text-foreground-muted">{d.name}</span>
                  </div>
                  <span className="data-mono font-medium">{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
