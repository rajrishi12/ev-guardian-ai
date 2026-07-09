"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Search, ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/badge";
import { api } from "@/lib/api";

const RISK_FILTERS = [
  { label: "All", value: undefined },
  { label: "High risk", value: "high" as const },
  { label: "Medium risk", value: "medium" as const },
  { label: "Low risk", value: "low" as const },
];

function riskBandFor(p: number | null): "low" | "medium" | "high" {
  const prob = p ?? 0;
  if (prob > 0.4) return "high";
  if (prob > 0.15) return "medium";
  return "low";
}

export default function FleetPage() {
  const [search, setSearch] = useState("");
  const [risk, setRisk] = useState<"low" | "medium" | "high" | undefined>(
    undefined
  );

  const { data: vehicles, isLoading } = useQuery({
    queryKey: ["vehicles", search, risk],
    queryFn: () => api.fleet.vehicles({ limit: 200, search: search || undefined, risk }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">
          Fleet &amp; digital twin
        </h1>
        <p className="text-sm text-foreground-muted">
          Every vehicle&apos;s live profile — battery, health, and history. Click a vehicle for its full digital twin.
        </p>
      </div>

      <Card flat className="!p-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-dim" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by vehicle ID..."
              className="w-full rounded-[var(--radius-sm)] border border-border-subtle bg-surface py-2 pl-9 pr-3 text-sm placeholder:text-foreground-dim focus:outline-none focus:border-[var(--signal-info)]"
            />
          </div>
          <div className="flex gap-1.5">
            {RISK_FILTERS.map((f) => (
              <button
                key={f.label}
                onClick={() => setRisk(f.value)}
                className={`rounded-[var(--radius-sm)] px-3 py-2 text-xs font-medium transition-colors ${
                  risk === f.value
                    ? "bg-surface-elevated text-foreground"
                    : "text-foreground-muted hover:bg-surface-elevated/60"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </Card>

      <Card flat className="!p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle text-left text-xs uppercase tracking-wide text-foreground-dim">
                <th className="px-4 py-3 font-medium">Vehicle</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Depot</th>
                <th className="px-4 py-3 font-medium text-right">SOH</th>
                <th className="px-4 py-3 font-medium text-right">Health</th>
                <th className="px-4 py-3 font-medium text-right">Odometer</th>
                <th className="px-4 py-3 font-medium">Risk</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                [...Array(8)].map((_, i) => (
                  <tr key={i} className="border-b border-border-subtle/50">
                    <td colSpan={8} className="px-4 py-3">
                      <div className="h-5 animate-pulse rounded bg-surface-elevated" />
                    </td>
                  </tr>
                ))
              ) : vehicles?.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-foreground-dim">
                    No vehicles match this search.
                  </td>
                </tr>
              ) : (
                vehicles?.map((v) => (
                  <tr
                    key={v.vehicle_id}
                    className="border-b border-border-subtle/50 hover:bg-surface-elevated/40 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/fleet/${v.vehicle_id}`}
                        className="flex items-center gap-2 group"
                      >
                        <span className="data-mono font-medium group-hover:text-[var(--signal-info)]">
                          {v.vehicle_id}
                        </span>
                        <span className="text-xs text-foreground-dim truncate max-w-[140px]">
                          {v.model}
                        </span>
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-foreground-muted">
                      {v.vehicle_type}
                    </td>
                    <td className="px-4 py-3 text-foreground-muted">
                      {v.depot}
                    </td>
                    <td className="px-4 py-3 text-right data-mono">
                      {v.final_soh_pct?.toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 text-right data-mono">
                      {v.health_score?.toFixed(1)}
                    </td>
                    <td className="px-4 py-3 text-right data-mono text-foreground-muted">
                      {v.odometer_km?.toLocaleString("en-IN", { maximumFractionDigits: 0 })} km
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge band={riskBandFor(v.failure_probability)} />
                    </td>
                    <td className="px-4 py-3">
                      <ChevronRight className="h-4 w-4 text-foreground-dim" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
