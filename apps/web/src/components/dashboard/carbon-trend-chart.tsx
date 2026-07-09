"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

export function CarbonTrendChart() {
  const { data, isLoading } = useQuery({
    queryKey: ["carbon-summary"],
    queryFn: api.carbon.summary,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>CO₂ saved vs. ICE baseline (monthly)</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-56 animate-pulse rounded-lg bg-surface-elevated" />
        ) : (
          <ResponsiveContainer width="100%" height={224}>
            <AreaChart data={data?.months ?? []} margin={{ left: -16, right: 8 }}>
              <defs>
                <linearGradient id="carbonGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00e5a0" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#00e5a0" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border-subtle)"
                vertical={false}
              />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 11, fill: "var(--foreground-dim)" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--foreground-dim)" }}
                axisLine={false}
                tickLine={false}
                width={48}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--surface-elevated)",
                  border: "1px solid var(--border-default)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                labelStyle={{ color: "var(--foreground-muted)" }}
              />
              <Area
                type="monotone"
                dataKey="co2_saved_kg"
                stroke="#00e5a0"
                strokeWidth={2}
                fill="url(#carbonGradient)"
                name="CO₂ saved (kg)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
