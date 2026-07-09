"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Clock, CheckCircle2, ChevronRight, PlugZap, Wrench } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge, RiskBadge } from "@/components/ui/badge";
import { api, type MaintenanceOptimizerSlot } from "@/lib/api";

const URGENCY_CONFIG = {
  immediate: { icon: AlertTriangle, variant: "critical" as const, label: "Immediate" },
  this_week: { icon: Clock, variant: "warning" as const, label: "This week" },
  this_month: { icon: CheckCircle2, variant: "info" as const, label: "This month" },
};

const FILTERS = [
  { label: "All", value: "this_month" as const },
  { label: "Immediate only", value: "immediate" as const },
  { label: "This week+", value: "this_week" as const },
];

export default function MaintenancePage() {
  const [minUrgency, setMinUrgency] = useState<"immediate" | "this_week" | "this_month">(
    "this_month"
  );

  const { data: alerts, isLoading } = useQuery({
    queryKey: ["maintenance-alerts", minUrgency],
    queryFn: () => api.maintenance.alerts(minUrgency),
  });

  const { data: optimizer, isLoading: optimizerLoading } = useQuery({
    queryKey: ["maintenance-optimizer"],
    queryFn: () => api.maintenance.optimizer(7),
  });

  const counts = {
    immediate: alerts?.filter((a) => a.urgency === "immediate").length ?? 0,
    this_week: alerts?.filter((a) => a.urgency === "this_week").length ?? 0,
    this_month: alerts?.filter((a) => a.urgency === "this_month").length ?? 0,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Predictive maintenance</h1>
        <p className="text-sm text-foreground-muted">
          Auto-generated maintenance plans, ranked by modeled failure probability and SOH degradation.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SummaryStat icon={AlertTriangle} label="Immediate" value={counts.immediate} accent="critical" />
        <SummaryStat icon={Clock} label="This week" value={counts.this_week} accent="warning" />
        <SummaryStat icon={CheckCircle2} label="This month / routine" value={counts.this_month} accent="info" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card flat className="lg:col-span-1">
          <div className="flex items-center gap-3 mb-4">
            <Wrench className="h-5 w-5 text-[var(--signal-info)]" />
            <div>
              <h3 className="text-sm font-medium text-foreground-muted tracking-wide uppercase">
                Optimizer
              </h3>
              <p className="text-xs text-foreground-dim">7-day workshop and charger plan</p>
            </div>
          </div>
          {optimizerLoading ? (
            <div className="h-32 animate-pulse rounded-lg bg-surface-elevated" />
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <Metric label="Jobs" value={optimizer?.total_planned_jobs ?? 0} />
              <Metric label="Charger conflicts" value={optimizer?.charger_conflicts ?? 0} />
              <Metric label="Overload depots" value={optimizer?.workshop_overload_depots.length ?? 0} />
              <Metric label="Window" value={`${optimizer?.generated_for_days ?? 7}d`} />
            </div>
          )}
        </Card>

        <Card flat className="lg:col-span-2 !p-0 overflow-hidden">
          <div className="px-5 py-4 border-b border-border-subtle">
            <h3 className="text-sm font-medium text-foreground-muted tracking-wide uppercase">
              Depot capacity
            </h3>
          </div>
          <div className="divide-y divide-border-subtle">
            {(optimizer?.depot_load ?? []).map((depot) => (
              <div key={depot.depot} className="px-5 py-3 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-medium">{depot.depot}</div>
                  <div className="text-xs text-foreground-dim data-mono">
                    {depot.workshop_bays} bays &middot; charger uptime {depot.charger_uptime_pct.toFixed(1)}%
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-foreground-muted data-mono">
                    {depot.planned_jobs} jobs &middot; {depot.capacity_utilization_pct.toFixed(1)}%
                  </span>
                  <RiskBadge band={depot.risk} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card flat className="!p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-border-subtle">
          <h3 className="text-sm font-medium text-foreground-muted tracking-wide uppercase">
            Optimized maintenance schedule
          </h3>
        </div>
        <div className="divide-y divide-border-subtle">
          {(optimizer?.schedule ?? []).slice(0, 8).map((slot) => (
            <OptimizerSlot key={`${slot.vehicle_id}-${slot.assigned_shift}`} slot={slot} />
          ))}
        </div>
      </Card>

      <Card flat className="!p-3">
        <div className="flex gap-1.5">
          {FILTERS.map((f) => (
            <button
              key={f.label}
              onClick={() => setMinUrgency(f.value)}
              className={`rounded-[var(--radius-sm)] px-3 py-2 text-xs font-medium transition-colors ${
                minUrgency === f.value
                  ? "bg-surface-elevated text-foreground"
                  : "text-foreground-muted hover:bg-surface-elevated/60"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </Card>

      <Card flat className="!p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-border-subtle flex items-center justify-between">
          <h3 className="text-sm font-medium text-foreground-muted tracking-wide uppercase">
            Maintenance alerts
          </h3>
          <span className="text-xs text-foreground-dim data-mono">{alerts?.length ?? 0} flagged</span>
        </div>
        <div>
          {isLoading ? (
            <div className="p-4 space-y-2">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-16 animate-pulse rounded-lg bg-surface-elevated" />
              ))}
            </div>
          ) : alerts?.length === 0 ? (
            <div className="py-12 text-center text-sm text-foreground-dim">
              No vehicles flagged at this urgency level - fleet is healthy.
            </div>
          ) : (
            <div className="divide-y divide-border-subtle">
              {alerts?.map((alert) => {
                const cfg = URGENCY_CONFIG[alert.urgency];
                const Icon = cfg.icon;
                return (
                  <Link
                    key={alert.vehicle_id}
                    href={`/fleet/${alert.vehicle_id}`}
                    className="flex items-center gap-4 px-5 py-4 hover:bg-surface-elevated/40 transition-colors"
                  >
                    <Icon
                      className="h-5 w-5 shrink-0"
                      style={{
                        color:
                          cfg.variant === "critical"
                            ? "var(--signal-critical)"
                            : cfg.variant === "warning"
                            ? "var(--signal-warning)"
                            : "var(--signal-info)",
                      }}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="data-mono font-medium">{alert.vehicle_id}</span>
                        <span className="text-xs text-foreground-dim">{alert.model}</span>
                        <RiskBadge band={alert.risk_band} />
                      </div>
                      <div className="text-sm text-foreground-muted mt-0.5">
                        {alert.recommended_action}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-xs text-foreground-dim">Failure probability</div>
                      <div className="data-mono font-medium">
                        {(alert.failure_probability * 100).toFixed(1)}%
                      </div>
                    </div>
                    <Badge variant={cfg.variant}>{cfg.label}</Badge>
                    <ChevronRight className="h-4 w-4 text-foreground-dim shrink-0" />
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-[var(--radius-sm)] border border-border-subtle bg-surface-elevated/40 p-3">
      <div className="text-xl font-semibold data-mono">{value}</div>
      <div className="text-xs text-foreground-dim mt-1">{label}</div>
    </div>
  );
}

function OptimizerSlot({ slot }: { slot: MaintenanceOptimizerSlot }) {
  const cfg = URGENCY_CONFIG[slot.urgency];
  return (
    <div className="px-5 py-4 flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="data-mono font-medium">{slot.vehicle_id}</span>
          <Badge variant={cfg.variant}>{cfg.label}</Badge>
          {slot.charger_required && (
            <Badge variant="info">
              <PlugZap className="h-3 w-3" />
              Charger
            </Badge>
          )}
        </div>
        <div className="mt-1 text-sm text-foreground-muted">{slot.action}</div>
      </div>
      <div className="text-right text-xs text-foreground-dim data-mono">
        <div>{slot.depot}</div>
        <div>{slot.assigned_shift} &middot; Bay {slot.bay} &middot; {slot.estimated_hours.toFixed(1)}h</div>
      </div>
    </div>
  );
}

function SummaryStat({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: typeof AlertTriangle;
  label: string;
  value: number;
  accent: "critical" | "warning" | "info";
}) {
  const colorMap = {
    critical: "var(--signal-critical)",
    warning: "var(--signal-warning)",
    info: "var(--signal-info)",
  };
  return (
    <Card flat>
      <div className="flex items-center gap-3">
        <div
          className="flex h-10 w-10 items-center justify-center rounded-lg shrink-0"
          style={{ background: `${colorMap[accent]}1f` }}
        >
          <Icon className="h-5 w-5" style={{ color: colorMap[accent] }} />
        </div>
        <div>
          <div className="text-2xl font-semibold data-mono">{value}</div>
          <div className="text-xs text-foreground-muted">{label}</div>
        </div>
      </div>
    </Card>
  );
}
