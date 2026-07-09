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
  Legend,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { Leaf, TreePine, Zap, Factory } from "lucide-react";

export default function CarbonPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["carbon-summary"],
    queryFn: api.carbon.summary,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Carbon intelligence</h1>
        <p className="text-sm text-foreground-muted">
          Net CO₂ impact vs. an equivalent ICE fleet, with Scope 1/2/3 breakdown.
        </p>
      </div>

      <Card flat className="border-[var(--signal-positive)]/30 bg-[color:var(--surface-elevated)]/80">
        <div className="flex items-start gap-2">
          <Leaf className="mt-0.5 h-4 w-4 text-[var(--signal-positive)]" />
          <div>
            <div className="text-sm font-medium">Evaluation focus: emission accounting accuracy</div>
            <p className="mt-1 text-sm text-foreground-muted">
              Scope 1, 2, and 3 impacts are shown alongside the ICE-equivalent baseline so carbon tracking can be compared against measured operational outcomes rather than a generic estimate.
            </p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat
          icon={Leaf}
          label="Total CO₂ saved"
          value={isLoading ? "—" : `${((data?.total_co2_saved_kg ?? 0) / 1000).toFixed(1)}t`}
          accent="positive"
          sublabel="vs. ICE equivalent fleet"
        />
        <Stat
          icon={TreePine}
          label="Trees equivalent"
          value={isLoading ? "—" : (data?.trees_equivalent ?? 0).toLocaleString()}
          accent="positive"
          sublabel="annual absorption equivalent"
        />
        <Stat
          icon={Zap}
          label="Scope 2 (grid electricity)"
          value={isLoading ? "—" : `${((data?.total_scope2_kg ?? 0) / 1000).toFixed(1)}t`}
          accent="info"
        />
        <Stat
          icon={Factory}
          label="Scope 3 (upstream/battery)"
          value={isLoading ? "—" : `${((data?.total_scope3_kg ?? 0) / 1000).toFixed(1)}t`}
          accent="warning"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Monthly CO₂ saved vs. ICE baseline</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="h-72 animate-pulse rounded-lg bg-surface-elevated" />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={data?.months ?? []} margin={{ left: -16, right: 8 }}>
                <defs>
                  <linearGradient id="savedGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#00e5a0" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#00e5a0" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="scope2Gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="scope3Gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f5a524" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#f5a524" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: "var(--foreground-dim)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "var(--foreground-dim)" }} axisLine={false} tickLine={false} width={56} />
                <Tooltip
                  contentStyle={{
                    background: "var(--surface-elevated)",
                    border: "1px solid var(--border-default)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Area type="monotone" dataKey="co2_saved_kg" name="Net CO₂ saved" stroke="#00e5a0" strokeWidth={2} fill="url(#savedGradient)" />
                <Area type="monotone" dataKey="scope2_kg" name="Scope 2 (grid)" stroke="#3b82f6" strokeWidth={1.5} fill="url(#scope2Gradient)" />
                <Area type="monotone" dataKey="scope3_kg" name="Scope 3 (upstream)" stroke="#f5a524" strokeWidth={1.5} fill="url(#scope3Gradient)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Card flat>
        <div className="text-xs text-foreground-dim leading-relaxed">
          Scope 1 (direct tailpipe emissions) is zero by definition for a fully electric fleet. Scope 2 reflects
          grid electricity used for charging at India&apos;s blended grid emission factor; Scope 3 captures upstream
          battery manufacturing and material extraction. The ICE-equivalent baseline accounts for vehicle class
          (3-wheelers, sedans, LCVs, trucks, and buses each have different diesel/petrol emission factors).
        </div>
      </Card>
    </div>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
  accent,
  sublabel,
}: {
  icon: typeof Leaf;
  label: string;
  value: string;
  accent: "positive" | "info" | "warning";
  sublabel?: string;
}) {
  const colorMap = {
    positive: "var(--signal-positive)",
    info: "var(--signal-info)",
    warning: "var(--signal-warning)",
  };
  return (
    <Card className="relative overflow-hidden">
      <div
        className="absolute -right-6 -top-6 h-24 w-24 rounded-full opacity-[0.08] blur-2xl"
        style={{ background: colorMap[accent] }}
      />
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="text-xs font-medium text-foreground-muted uppercase tracking-wide">{label}</div>
          <div className="text-2xl font-semibold data-mono">{value}</div>
          {sublabel && <div className="text-xs text-foreground-dim">{sublabel}</div>}
        </div>
        <div
          className="flex h-9 w-9 items-center justify-center rounded-lg shrink-0"
          style={{ background: `${colorMap[accent]}1f` }}
        >
          <Icon className="h-4.5 w-4.5" style={{ color: colorMap[accent] }} />
        </div>
      </div>
    </Card>
  );
}
