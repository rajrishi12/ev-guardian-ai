"use client";

import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import { Car, BatteryMedium, Leaf, Gauge } from "lucide-react";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { RiskBreakdownChart } from "@/components/dashboard/risk-breakdown-chart";
import { CarbonTrendChart } from "@/components/dashboard/carbon-trend-chart";
import { MaintenanceAlertsFeed } from "@/components/dashboard/maintenance-alerts-feed";
import { api } from "@/lib/api";

const FleetMap = dynamic(
  () => import("@/components/dashboard/fleet-map").then((m) => m.FleetMap),
  { ssr: false, loading: () => <div className="h-[420px] animate-pulse rounded-[var(--radius-lg)] bg-surface" /> }
);

export default function OverviewPage() {
  const { data: overview, isLoading } = useQuery({
    queryKey: ["fleet-overview"],
    queryFn: api.fleet.overview,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Fleet overview</h1>
        <p className="text-sm text-foreground-muted">
          Real-time intelligence across your EV fleet, battery health, and carbon impact.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Active vehicles"
          value={isLoading ? "—" : `${overview?.active_vehicles}/${overview?.total_vehicles}`}
          icon={Car}
          accent="info"
          sublabel={`${overview?.in_maintenance ?? 0} in maintenance`}
        />
        <KpiCard
          label="Avg. health score"
          value={isLoading ? "—" : overview?.avg_health_score.toFixed(1) ?? "—"}
          icon={Gauge}
          accent="positive"
          sublabel="out of 100"
        />
        <KpiCard
          label="Avg. battery SOH"
          value={isLoading ? "—" : `${overview?.avg_soh_pct.toFixed(1)}%`}
          icon={BatteryMedium}
          accent="positive"
          sublabel={`${overview?.high_risk_count ?? 0} vehicles high-risk`}
        />
        <KpiCard
          label="CO₂ saved (total)"
          value={
            isLoading
              ? "—"
              : `${((overview?.total_co2_saved_kg ?? 0) / 1000).toFixed(1)}t`
          }
          icon={Leaf}
          accent="positive"
          sublabel="vs. ICE equivalent fleet"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <FleetMap />
        </div>
        <RiskBreakdownChart />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <CarbonTrendChart />
        </div>
        <MaintenanceAlertsFeed />
      </div>
    </div>
  );
}
