"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type VehicleGenealogy } from "@/lib/api";
import { AlertOctagon, GitBranch, ShieldCheck, Truck } from "lucide-react";

function riskColor(score: number) {
  if (score > 0.5) return "#ff5c5c";
  if (score > 0.25) return "#f5a524";
  return "#00e5a0";
}

function riskLabel(score: number) {
  if (score > 0.5) return { variant: "critical" as const, label: "High" };
  if (score > 0.25) return { variant: "warning" as const, label: "Medium" };
  return { variant: "positive" as const, label: "Low" };
}

export default function SupplyChainPage() {
  const { data: riskSummary, isLoading: riskLoading } = useQuery({
    queryKey: ["supply-chain-risk-summary"],
    queryFn: api.supplyChain.riskSummary,
  });

  const { data: byMaterial, isLoading: materialLoading } = useQuery({
    queryKey: ["supply-chain-by-material"],
    queryFn: api.supplyChain.byMaterial,
  });

  const { data: suppliers, isLoading: suppliersLoading } = useQuery({
    queryKey: ["suppliers"],
    queryFn: api.supplyChain.suppliers,
  });

  const { data: genealogy, isLoading: genealogyLoading } = useQuery({
    queryKey: ["vehicle-genealogy"],
    queryFn: () => api.supplyChain.genealogy(8),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Supply chain intelligence</h1>
        <p className="text-sm text-foreground-muted">
          Battery material supplier risk - geopolitical, weather, and quality factors combined into a single score.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SummaryStat
          icon={Truck}
          label="Total suppliers"
          value={riskLoading ? "—" : String(riskSummary?.total_suppliers ?? 0)}
          accent="info"
        />
        <SummaryStat
          icon={AlertOctagon}
          label="High risk suppliers"
          value={riskLoading ? "—" : String(riskSummary?.high_risk ?? 0)}
          accent="critical"
        />
        <SummaryStat
          icon={ShieldCheck}
          label="Avg. risk score"
          value={riskLoading ? "—" : (riskSummary?.avg_risk_score ?? 0).toFixed(2)}
          accent="positive"
        />
      </div>

      <Card flat className="border-[var(--signal-warning)]/30 bg-[color:var(--surface-elevated)]/80">
        <div className="flex items-start gap-2">
          <AlertOctagon className="mt-0.5 h-4 w-4 text-[var(--signal-warning)]" />
          <div>
            <div className="text-sm font-medium">Evaluation focus: lead-time disruption detection</div>
            <p className="mt-1 text-sm text-foreground-muted">
              Supplier risk is surfaced before disruption through geopolitical exposure, weather pressure, lead-time strain, on-time delivery, and quality signals, so the platform can flag issues earlier than a manual review would.
            </p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Risk by material</CardTitle>
          </CardHeader>
          <CardContent>
            {materialLoading ? (
              <div className="h-56 animate-pulse rounded-lg bg-surface-elevated" />
            ) : (
              <ResponsiveContainer width="100%" height={224}>
                <BarChart
                  data={(byMaterial ?? []) as { material: string; avg_risk: number; supplier_count: number }[]}
                  margin={{ left: -16, right: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                  <XAxis dataKey="material" tick={{ fontSize: 11, fill: "var(--foreground-dim)" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: "var(--foreground-dim)" }} axisLine={false} tickLine={false} width={36} domain={[0, 1]} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--surface-elevated)",
                      border: "1px solid var(--border-default)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="avg_risk" radius={[4, 4, 0, 0]}>
                    {(byMaterial ?? []).map((m, i) => (
                      <Cell key={i} fill={riskColor((m as { avg_risk: number }).avg_risk)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Highest-risk suppliers</CardTitle>
          </CardHeader>
          <CardContent>
            {riskLoading ? (
              <div className="h-56 animate-pulse rounded-lg bg-surface-elevated" />
            ) : (
              <div className="space-y-2">
                {riskSummary?.highest_risk_suppliers.map((s, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-[var(--radius-sm)] border border-border-subtle px-3 py-2.5"
                  >
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">{s.name}</div>
                      <div className="text-xs text-foreground-dim">
                        {s.material} &middot; {s.region}
                      </div>
                    </div>
                    <Badge variant={riskLabel(s.risk).variant}>{(s.risk * 100).toFixed(0)}%</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card flat className="!p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-border-subtle flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-foreground-muted tracking-wide uppercase">
              Cell-to-pack-to-vehicle genealogy
            </h3>
            <p className="mt-1 text-xs text-foreground-dim">
              Critical material provenance, cell lot, pack ID, vehicle assignment, and unresolved traceability gaps.
            </p>
          </div>
          <GitBranch className="h-5 w-5 text-[var(--signal-agent)]" />
        </div>
        {genealogyLoading ? (
          <div className="p-4 space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg bg-surface-elevated" />
            ))}
          </div>
        ) : (
          <div className="divide-y divide-border-subtle">
            {(genealogy ?? []).map((item) => (
              <GenealogyCard key={item.vehicle_id} item={item} />
            ))}
          </div>
        )}
      </Card>

      <Card flat className="!p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-border-subtle">
          <h3 className="text-sm font-medium text-foreground-muted tracking-wide uppercase">
            All suppliers
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle text-left text-xs uppercase tracking-wide text-foreground-dim">
                <th className="px-4 py-3 font-medium">Supplier</th>
                <th className="px-4 py-3 font-medium">Material</th>
                <th className="px-4 py-3 font-medium">Region</th>
                <th className="px-4 py-3 font-medium text-right">Lead time</th>
                <th className="px-4 py-3 font-medium text-right">On-time %</th>
                <th className="px-4 py-3 font-medium text-right">Quality</th>
                <th className="px-4 py-3 font-medium">Risk</th>
              </tr>
            </thead>
            <tbody>
              {suppliersLoading ? (
                [...Array(6)].map((_, i) => (
                  <tr key={i} className="border-b border-border-subtle/50">
                    <td colSpan={7} className="px-4 py-3">
                      <div className="h-5 animate-pulse rounded bg-surface-elevated" />
                    </td>
                  </tr>
                ))
              ) : (
                suppliers?.map((s) => {
                  const r = riskLabel(s.overall_risk_score);
                  return (
                    <tr key={s.supplier_id} className="border-b border-border-subtle/50 hover:bg-surface-elevated/40 transition-colors">
                      <td className="px-4 py-3 font-medium">{s.name}</td>
                      <td className="px-4 py-3 text-foreground-muted">{s.material}</td>
                      <td className="px-4 py-3 text-foreground-muted">{s.region}</td>
                      <td className="px-4 py-3 text-right data-mono">{s.lead_time_days}d</td>
                      <td className="px-4 py-3 text-right data-mono">{s.on_time_delivery_pct.toFixed(1)}%</td>
                      <td className="px-4 py-3 text-right data-mono">{s.quality_score.toFixed(2)}</td>
                      <td className="px-4 py-3">
                        <Badge variant={r.variant}>{r.label}</Badge>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function GenealogyCard({ item }: { item: VehicleGenealogy }) {
  const scoreVariant =
    item.traceability_score >= 80 ? "positive" : item.traceability_score >= 60 ? "warning" : "critical";

  return (
    <div className="px-5 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="data-mono font-medium">{item.vehicle_id}</span>
            <Badge variant={scoreVariant}>{item.traceability_score.toFixed(0)} traceability</Badge>
          </div>
          <div className="text-xs text-foreground-dim data-mono mt-1">
            {item.cell_lot} &middot; {item.pack_id}
          </div>
        </div>
        <div className="text-xs text-foreground-dim max-w-lg text-right">
          {item.open_gaps.length > 0 ? item.open_gaps[0] : "No open certificate gaps in mapped chain."}
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
        {item.genealogy.map((node) => (
          <div
            key={`${item.vehicle_id}-${node.stage}-${node.id}`}
            className="rounded-[var(--radius-sm)] border border-border-subtle bg-surface-elevated/35 p-3"
          >
            <div className="text-[10px] uppercase tracking-wide text-foreground-dim">{node.stage}</div>
            <div className="mt-1 text-xs data-mono truncate">{node.id}</div>
            <div className="mt-2 flex items-center justify-between gap-2">
              <span className="text-xs text-foreground-muted truncate">
                {node.supplier_name ?? node.material ?? "internal"}
              </span>
              <Badge variant={node.traceable ? "positive" : "critical"}>
                {node.traceable ? "cert" : "gap"}
              </Badge>
            </div>
          </div>
        ))}
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
  icon: typeof Truck;
  label: string;
  value: string;
  accent: "critical" | "warning" | "info" | "positive";
}) {
  const colorMap = {
    critical: "var(--signal-critical)",
    warning: "var(--signal-warning)",
    info: "var(--signal-info)",
    positive: "var(--signal-positive)",
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
