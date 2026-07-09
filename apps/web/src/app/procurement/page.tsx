"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { BatteryCharging, Route, Upload, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, type ElectrificationReadiness, type ProcurementRecommendation } from "@/lib/api";

const REC_CONFIG = {
  replace: { variant: "critical" as const, icon: TrendingDown, label: "Replace" },
  monitor: { variant: "warning" as const, icon: Minus, label: "Monitor" },
  retain: { variant: "positive" as const, icon: TrendingUp, label: "Retain" },
};

export default function ProcurementPage() {
  const [uploadResult, setUploadResult] = useState<ProcurementRecommendation[] | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["procurement-recommendations"],
    queryFn: () => api.procurement.recommendations(100),
  });

  const { data: readiness, isLoading: readinessLoading } = useQuery({
    queryKey: ["electrification-readiness"],
    queryFn: () => api.procurement.readiness(30),
  });

  const [uploadError, setUploadError] = useState<string | null>(null);
  const { mutate: analyzeCsv, isPending: isAnalyzing } = useMutation({
    mutationFn: (file: File) => api.procurement.analyzeCsv(file),
    onSuccess: (res) => {
      setUploadResult(res);
      setUploadError(null);
    },
    onError: (err) => {
      setUploadError(
        err instanceof Error ? err.message : "Could not analyze the uploaded file."
      );
    },
  });

  const displayData = uploadResult ?? data ?? [];
  const replaceCount = displayData.filter((r) => r.recommendation === "replace").length;
  const monitorCount = displayData.filter((r) => r.recommendation === "monitor").length;
  const retainCount = displayData.filter((r) => r.recommendation === "retain").length;
  const readyNowCount = readiness?.filter((r) => r.readiness_band === "ready_now").length ?? 0;

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) analyzeCsv(file);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Procurement intelligence</h1>
          <p className="text-sm text-foreground-muted">
            Replace / monitor / retain recommendations with transparent ROI and risk reasoning.
          </p>
        </div>
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileChange}
          />
          <Button variant="outline" onClick={() => fileInputRef.current?.click()} disabled={isAnalyzing}>
            <Upload className="h-4 w-4" />
            {isAnalyzing ? "Analyzing..." : "Upload fleet CSV"}
          </Button>
        </div>
      </div>

      {uploadError && (
        <Card flat className="border-[var(--signal-critical)]/40">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[var(--signal-critical)]">{uploadError}</span>
            <button
              onClick={() => setUploadError(null)}
              className="text-foreground-muted hover:text-foreground text-xs"
            >
              Dismiss
            </button>
          </div>
        </Card>
      )}

      {uploadResult && (
        <Card flat className="border-[var(--signal-info)]/40">
          <div className="flex items-center justify-between text-sm">
            <span className="text-foreground-muted">
              Showing analysis from your uploaded CSV ({uploadResult.length} vehicles).
            </span>
            <button
              onClick={() => setUploadResult(null)}
              className="text-[var(--signal-info)] hover:underline text-xs"
            >
              Clear &amp; show fleet defaults
            </button>
          </div>
        </Card>
      )}

      <Card flat className="border-[var(--signal-info)]/30 bg-[color:var(--surface-elevated)]/80">
        <div className="flex items-start gap-2">
          <BatteryCharging className="mt-0.5 h-4 w-4 text-[var(--signal-info)]" />
          <div>
            <div className="text-sm font-medium">Evaluation focus: electrification readiness scoring</div>
            <p className="mt-1 text-sm text-foreground-muted">
              Readiness is scored using route profile, payload, dwell time, charger access, OEM fit, and delivery lead time so the recommendation quality can be compared directly with expert decision-making.
            </p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SummaryStat label="Recommended to replace" value={replaceCount} accent="critical" />
        <SummaryStat label="Monitor closely" value={monitorCount} accent="warning" />
        <SummaryStat label="Retain - healthy" value={retainCount} accent="positive" />
      </div>

      <Card flat className="!p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-border-subtle flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-foreground-muted tracking-wide uppercase">
              Electrification readiness
            </h3>
            <p className="mt-1 text-xs text-foreground-dim">
              Route, payload, dwell time, charger access, OEM fit, and delivery lead time.
            </p>
          </div>
          <Badge variant="positive">{readyNowCount} ready now</Badge>
        </div>
        {readinessLoading ? (
          <div className="p-4 space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg bg-surface-elevated" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-subtle text-left text-xs uppercase tracking-wide text-foreground-dim">
                  <th className="px-4 py-3 font-medium">Asset</th>
                  <th className="px-4 py-3 font-medium">Duty cycle</th>
                  <th className="px-4 py-3 font-medium text-right">Payload</th>
                  <th className="px-4 py-3 font-medium text-right">Dwell</th>
                  <th className="px-4 py-3 font-medium text-right">Charger</th>
                  <th className="px-4 py-3 font-medium">OEM fit</th>
                  <th className="px-4 py-3 font-medium text-right">Lead</th>
                  <th className="px-4 py-3 font-medium">Readiness</th>
                </tr>
              </thead>
              <tbody>
                {(readiness ?? []).slice(0, 10).map((row) => (
                  <ReadinessRow key={row.vehicle_id} row={row} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card flat className="!p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-border-subtle">
          <h3 className="text-sm font-medium text-foreground-muted tracking-wide uppercase">
            Recommendations
          </h3>
        </div>
        <div>
          {isLoading && !uploadResult ? (
            <div className="p-4 space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-20 animate-pulse rounded-lg bg-surface-elevated" />
              ))}
            </div>
          ) : (
            <div className="divide-y divide-border-subtle">
              {displayData.map((rec) => {
                const cfg = REC_CONFIG[rec.recommendation];
                const Icon = cfg.icon;
                return (
                  <div key={rec.vehicle_id} className="px-5 py-4">
                    <div className="flex flex-wrap items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2">
                        <Icon
                          className="h-4 w-4"
                          style={{
                            color:
                              cfg.variant === "critical"
                                ? "var(--signal-critical)"
                                : cfg.variant === "warning"
                                ? "var(--signal-warning)"
                                : "var(--signal-positive)",
                          }}
                        />
                        <span className="data-mono font-medium">{rec.vehicle_id}</span>
                        <span className="text-xs text-foreground-dim">{rec.model}</span>
                        <Badge variant={cfg.variant}>{cfg.label}</Badge>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-foreground-muted">
                        {rec.expected_roi_pct !== null && (
                          <span className="data-mono">
                            5yr ROI: <span className={rec.expected_roi_pct >= 0 ? "text-[var(--signal-positive)]" : "text-[var(--signal-critical)]"}>{rec.expected_roi_pct.toFixed(0)}%</span>
                          </span>
                        )}
                        <span className="data-mono">Confidence: {(rec.confidence_score * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    <p className="text-sm text-foreground-muted leading-relaxed">{rec.rationale}</p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

function readinessVariant(band: ElectrificationReadiness["readiness_band"]) {
  if (band === "ready_now") return "positive" as const;
  if (band === "pilot_candidate") return "warning" as const;
  return "critical" as const;
}

function ReadinessRow({ row }: { row: ElectrificationReadiness }) {
  return (
    <tr className="border-b border-border-subtle/50 hover:bg-surface-elevated/40 transition-colors">
      <td className="px-4 py-3">
        <div className="data-mono font-medium">{row.vehicle_id}</div>
        <div className="text-xs text-foreground-dim">{row.current_vehicle_type}</div>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <Route className="h-3.5 w-3.5 text-[var(--signal-info)]" />
          <span className="text-foreground-muted">{row.route_profile}</span>
        </div>
        <div className="text-xs text-foreground-dim data-mono">{row.avg_daily_km.toFixed(0)} km/day</div>
      </td>
      <td className="px-4 py-3 text-right data-mono">{row.payload_tonnes.toFixed(2)}t</td>
      <td className="px-4 py-3 text-right data-mono">{row.dwell_hours.toFixed(1)}h</td>
      <td className="px-4 py-3 text-right">
        <div className="inline-flex items-center gap-1 data-mono">
          <BatteryCharging className="h-3.5 w-3.5 text-[var(--signal-positive)]" />
          {row.charger_access_score.toFixed(0)}
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="text-foreground-muted">{row.recommended_oem}</div>
        <div className="text-xs text-foreground-dim data-mono">{row.recommended_battery_kwh.toFixed(0)} kWh</div>
      </td>
      <td className="px-4 py-3 text-right data-mono">{row.delivery_lead_time_days}d</td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <Badge variant={readinessVariant(row.readiness_band)}>
            {row.readiness_index.toFixed(0)}
          </Badge>
          {row.blockers.length > 0 && (
            <span className="text-xs text-foreground-dim truncate max-w-48">
              {row.blockers[0]}
            </span>
          )}
        </div>
      </td>
    </tr>
  );
}

function SummaryStat({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: "critical" | "warning" | "positive";
}) {
  const colorMap = {
    critical: "var(--signal-critical)",
    warning: "var(--signal-warning)",
    positive: "var(--signal-positive)",
  };
  return (
    <Card flat>
      <div className="text-2xl font-semibold data-mono" style={{ color: colorMap[accent] }}>
        {value}
      </div>
      <div className="text-xs text-foreground-muted mt-1">{label}</div>
    </Card>
  );
}
