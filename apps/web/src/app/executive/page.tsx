"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  Activity,
  BatteryCharging,
  ShieldAlert,
  Wrench,
  Leaf,
  Network,
  Wallet,
  TrendingDown,
  TrendingUp,
  Sparkles,
  Bell,
  AlertOctagon,
  Car,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { api } from "@/lib/api";

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.05, duration: 0.35, ease: "easeOut" as const },
  }),
};

function formatINR(n: number) {
  if (Math.abs(n) >= 10_000_000) return `₹${(n / 10_000_000).toFixed(2)}Cr`;
  if (Math.abs(n) >= 100_000) return `₹${(n / 100_000).toFixed(2)}L`;
  return `₹${n.toLocaleString("en-IN")}`;
}

const SEVERITY_DOT: Record<string, string> = {
  critical: "var(--signal-critical)",
  warning: "var(--signal-warning)",
  info: "var(--signal-info)",
};

export default function ExecutiveCommandCenterPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["executive-dashboard"],
    queryFn: api.executive.dashboard,
    refetchInterval: 30_000,
  });

  const chargingData = data
    ? [
        { name: "Charging now", key: "charging", value: data.charging.charging_now },
        { name: "Charged / ready", key: "ready", value: data.charging.charged_ready },
        {
          name: "In maintenance",
          key: "maint",
          value: data.vehicles_in_maintenance,
        },
      ]
    : [];
  const CHARGE_COLORS: Record<string, string> = {
    charging: "#3b82f6",
    ready: "#00e5a0",
    maint: "#f5a524",
  };

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between flex-wrap gap-3"
      >
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold tracking-tight">
              Executive Command Center
            </h1>
            <span className="flex items-center gap-1.5 rounded-full bg-[var(--signal-positive-dim)] px-2 py-0.5 text-[10px] font-medium text-[var(--signal-positive)] data-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--signal-positive)] animate-pulse" />
              LIVE
            </span>
          </div>
          <p className="text-sm text-foreground-muted">
            Fleet-wide operational, financial, and sustainability posture — refreshed every 30s.
          </p>
        </div>
        {data && (
          <div className="text-xs text-foreground-dim data-mono">
            Last updated {data.generated_at}
          </div>
        )}
      </motion.div>

      {/* KPI grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: "Fleet health score",
            value: isLoading ? "—" : data?.fleet_health_score.toFixed(1),
            icon: Activity,
            accent: "positive" as const,
            sublabel: "out of 100",
          },
          {
            label: "Avg. battery SOH",
            value: isLoading ? "—" : `${data?.avg_battery_soh_pct.toFixed(1)}%`,
            icon: BatteryCharging,
            accent: "positive" as const,
            sublabel: `${data?.charging.charging_now ?? 0} charging now`,
          },
          {
            label: "Vehicles online",
            value: isLoading ? "—" : `${data?.vehicles_online}/${data?.total_vehicles}`,
            icon: Car,
            accent: "info" as const,
            sublabel: `${data?.vehicles_in_maintenance ?? 0} in maintenance`,
          },
          {
            label: "Critical alerts",
            value: isLoading ? "—" : String(data?.critical_alerts_count),
            icon: ShieldAlert,
            accent: (data?.critical_alerts_count ?? 0) > 0 ? ("critical" as const) : ("positive" as const),
            sublabel: "immediate action required",
          },
          {
            label: "Maintenance due",
            value: isLoading ? "—" : String(data?.maintenance_due_count),
            icon: Wrench,
            accent: "warning" as const,
            sublabel: "scheduled, next 7 days",
          },
          {
            label: "Carbon saved (total)",
            value: isLoading ? "—" : `${((data?.carbon_saved_kg ?? 0) / 1000).toFixed(1)}t`,
            icon: Leaf,
            accent: "positive" as const,
            sublabel: `${data && data.emission_trend_pct <= 0 ? "↓" : "↑"} ${Math.abs(
              data?.emission_trend_pct ?? 0
            ).toFixed(1)}% MoM`,
          },
          {
            label: "Supplier risk score",
            value: isLoading ? "—" : data?.supplier_risk_score.toFixed(2),
            icon: Network,
            accent:
              (data?.supplier_risk_score ?? 0) > 0.4
                ? ("critical" as const)
                : (data?.supplier_risk_score ?? 0) > 0.25
                ? ("warning" as const)
                : ("positive" as const),
            sublabel: `${data?.top_risk_suppliers[0]?.name ?? "—"} highest`,
          },
          {
            label: "Monthly operating cost",
            value: isLoading ? "—" : formatINR(data?.monthly_operating_cost_inr ?? 0),
            icon: Wallet,
            accent: "neutral" as const,
            sublabel: "maintenance + charging",
          },
        ].map((kpi, i) => (
          <motion.div key={kpi.label} variants={fadeUp} initial="hidden" animate="show" custom={i}>
            <KpiCard
              label={kpi.label}
              value={kpi.value ?? "—"}
              icon={kpi.icon}
              accent={kpi.accent}
              sublabel={kpi.sublabel}
            />
          </motion.div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div variants={fadeUp} initial="hidden" animate="show" custom={8} className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Downtime trend (monthly hours)</CardTitle>
              <Badge variant="neutral">last 6 months</Badge>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-56 animate-pulse rounded-lg bg-surface-elevated" />
              ) : (
                <ResponsiveContainer width="100%" height={224}>
                  <BarChart data={data?.downtime_trend ?? []} margin={{ left: -16, right: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
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
                      width={40}
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
                    <Bar dataKey="downtime_hours" name="Downtime (hrs)" fill="#f5a524" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeUp} initial="hidden" animate="show" custom={9}>
          <Card>
            <CardHeader>
              <CardTitle>Fleet status</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-44 animate-pulse rounded-lg bg-surface-elevated" />
              ) : (
                <div className="flex items-center gap-4">
                  <div className="relative h-36 w-36 shrink-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={chargingData}
                          dataKey="value"
                          nameKey="name"
                          innerRadius={44}
                          outerRadius={65}
                          paddingAngle={3}
                          stroke="none"
                        >
                          {chargingData.map((entry) => (
                            <Cell key={entry.key} fill={CHARGE_COLORS[entry.key]} />
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
                      <span className="text-xl font-semibold data-mono">{data?.total_vehicles}</span>
                      <span className="text-[9px] text-foreground-dim uppercase tracking-wide">vehicles</span>
                    </div>
                  </div>
                  <div className="space-y-2 flex-1 text-xs">
                    {chargingData.map((d) => (
                      <div key={d.key} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span
                            className="h-2 w-2 rounded-full"
                            style={{ background: CHARGE_COLORS[d.key] }}
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
        </motion.div>
      </div>

      {/* AI insights + notifications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div variants={fadeUp} initial="hidden" animate="show" custom={10}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-[var(--signal-agent)]" />
                AI insights
              </CardTitle>
              <Badge variant="agent">{data?.ai_insights.length ?? 0} generated</Badge>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-12 animate-pulse rounded-lg bg-surface-elevated" />
                  ))}
                </div>
              ) : (
                <div className="space-y-2">
                  {data?.ai_insights.map((insight, i) => (
                    <div
                      key={i}
                      className="flex gap-2.5 rounded-[var(--radius-sm)] border border-border-subtle bg-[var(--signal-agent-dim)]/30 px-3 py-2.5 text-xs text-foreground-muted leading-relaxed"
                    >
                      <Sparkles className="h-3.5 w-3.5 shrink-0 mt-0.5 text-[var(--signal-agent)]" />
                      <span>{insight}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeUp} initial="hidden" animate="show" custom={11}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-1.5">
                <Bell className="h-3.5 w-3.5" />
                Live notifications
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-10 animate-pulse rounded-lg bg-surface-elevated" />
                  ))}
                </div>
              ) : (data?.live_notifications.length ?? 0) === 0 ? (
                <div className="py-8 text-center text-sm text-foreground-dim">No recent events.</div>
              ) : (
                <div className="space-y-1.5">
                  {data?.live_notifications.map((n) => (
                    <div
                      key={n.id}
                      className="flex items-center gap-3 rounded-[var(--radius-sm)] border border-border-subtle px-3 py-2 hover:bg-surface-elevated/50 transition-colors"
                    >
                      <span
                        className="h-2 w-2 rounded-full shrink-0"
                        style={{ background: SEVERITY_DOT[n.severity] }}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium data-mono">{n.vehicle_id}</span>
                          <span className="text-[10px] text-foreground-dim">{n.date}</span>
                        </div>
                        <div className="text-xs text-foreground-muted truncate">{n.message}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Incidents + suppliers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div variants={fadeUp} initial="hidden" animate="show" custom={12}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-1.5">
                <AlertOctagon className="h-3.5 w-3.5 text-[var(--signal-critical)]" />
                Recent incidents
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-40 animate-pulse rounded-lg bg-surface-elevated" />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-left text-foreground-dim uppercase tracking-wide text-[10px]">
                        <th className="pb-2 font-medium">Vehicle</th>
                        <th className="pb-2 font-medium">Issue</th>
                        <th className="pb-2 font-medium text-right">Downtime</th>
                        <th className="pb-2 font-medium text-right">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data?.recent_incidents.map((inc, i) => (
                        <tr key={i} className="border-t border-border-subtle">
                          <td className="py-2 data-mono">{inc.vehicle_id}</td>
                          <td className="py-2 text-foreground-muted">{inc.issue_type}</td>
                          <td className="py-2 text-right data-mono">{inc.downtime_hours}h</td>
                          <td className="py-2 text-right data-mono">
                            {inc.cost_inr ? formatINR(inc.cost_inr) : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeUp} initial="hidden" animate="show" custom={13}>
          <Card>
            <CardHeader>
              <CardTitle>Highest-risk suppliers</CardTitle>
              <Badge variant="neutral">
                {data?.replace_recommended_count ?? 0} vehicles flagged for replacement
              </Badge>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-40 animate-pulse rounded-lg bg-surface-elevated" />
              ) : (
                <div className="space-y-2.5">
                  {data?.top_risk_suppliers.map((s) => (
                    <div key={s.name} className="flex items-center justify-between text-sm">
                      <div>
                        <div className="font-medium">{s.name}</div>
                        <div className="text-xs text-foreground-dim">{s.material}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        {s.risk > 0.4 ? (
                          <TrendingUp className="h-3.5 w-3.5 text-[var(--signal-critical)]" />
                        ) : (
                          <TrendingDown className="h-3.5 w-3.5 text-[var(--signal-positive)]" />
                        )}
                        <span className="data-mono font-medium">{s.risk.toFixed(2)}</span>
                      </div>
                    </div>
                  ))}
                  <div className="pt-2 mt-2 border-t border-border-subtle text-xs text-foreground-muted">
                    Projected annualized savings from executing all current replacement
                    recommendations:{" "}
                    <span className="data-mono font-medium text-[var(--signal-positive)]">
                      {formatINR(data?.procurement_savings_est_inr ?? 0)}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
