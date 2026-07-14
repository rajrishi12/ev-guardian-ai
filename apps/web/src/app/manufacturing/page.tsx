"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Factory, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

export default function ManufacturingPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["manufacturing-qc-summary"],
    queryFn: api.manufacturing.qcSummary,
  });

  const { data: recent, isLoading: recentLoading } = useQuery({
    queryKey: ["manufacturing-qc-recent"],
    queryFn: () => api.manufacturing.qcRecent(6),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Manufacturing quality intelligence</h1>
        <p className="text-sm text-foreground-muted">
          Supplier QC, defect drift detection, and quality traceability for EV manufacturing.
        </p>
      </div>

      <Card flat className="border-[var(--signal-warning)]/30 bg-[color:var(--surface-elevated)]/80">
        <div className="flex items-start gap-2">
          <AlertTriangle className="mt-0.5 h-4 w-4 text-[var(--signal-warning)]" />
          <div>
            <div className="text-sm font-medium">Evaluation focus: defect detection quality</div>
            <p className="mt-1 text-sm text-foreground-muted">
              Incoming inspection defect rates and supplier quality signals are turned into early warnings so teams can prioritize quality issues before they spread into field failures.
            </p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SummaryStat
          icon={Factory}
          label="Inspections logged"
          value={isLoading ? "—" : String(data?.total_inspections ?? 0)}
          accent="info"
        />
        <SummaryStat
          icon={AlertTriangle}
          label="Average defect rate"
          value={isLoading ? "—" : `${((data?.avg_defect_rate ?? 0) * 100).toFixed(1)}%`}
          accent="warning"
        />
        <SummaryStat
          icon={ShieldCheck}
          label="Suppliers flagged"
          value={isLoading ? "—" : String(data?.suppliers_flagged?.length ?? 0)}
          accent="positive"
        />
      </div>

      <Card flat className="!p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-border-subtle">
          <h3 className="text-sm font-medium text-foreground-muted tracking-wide uppercase">
            Recent inspection signals
          </h3>
        </div>
        {recentLoading ? (
          <div className="p-4 space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-surface-elevated" />
            ))}
          </div>
        ) : (
          <div className="divide-y divide-border-subtle">
            {recent?.map((item) => (
              <div key={`${item.supplier_id}-${item.date}`} className="flex items-center justify-between px-5 py-3">
                <div>
                  <div className="text-sm font-medium">{item.supplier_id}</div>
                  <div className="text-xs text-foreground-dim">{item.date}</div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={item.defect_rate > 0.02 ? "critical" : "warning"}>
                    {(item.defect_rate * 100).toFixed(1)}%
                  </Badge>
                  <span className="text-sm text-foreground-muted">{item.notes ?? "No notes"}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function SummaryStat({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: typeof Factory;
  label: string;
  value: string;
  accent: "info" | "warning" | "positive";
}) {
  const colorMap = {
    info: "var(--signal-info)",
    warning: "var(--signal-warning)",
    positive: "var(--signal-positive)",
  };

  return (
    <Card className="relative overflow-hidden">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-foreground-muted">{label}</div>
          <div className="mt-2 text-2xl font-semibold data-mono">{value}</div>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg" style={{ background: `${colorMap[accent]}1f` }}>
          <Icon className="h-4.5 w-4.5" style={{ color: colorMap[accent] }} />
        </div>
      </div>
    </Card>
  );
}
