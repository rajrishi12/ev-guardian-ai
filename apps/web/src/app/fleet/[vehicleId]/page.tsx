"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Battery,
  Gauge,
  MapPin,
  Calendar,
  AlertTriangle,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge, RiskBadge } from "@/components/ui/badge";
import { api } from "@/lib/api";

export default function VehicleDetailPage() {
  const params = useParams();
  const vehicleId = params.vehicleId as string;

  const { data: vehicle, isLoading: vLoading } = useQuery({
    queryKey: ["vehicle", vehicleId],
    queryFn: () => api.fleet.vehicle(vehicleId),
  });

  const { data: telemetry, isLoading: tLoading } = useQuery({
    queryKey: ["telemetry", vehicleId],
    queryFn: () => api.fleet.telemetry(vehicleId),
  });

  const { data: maintenance } = useQuery({
    queryKey: ["maintenance", vehicleId],
    queryFn: () => api.fleet.maintenance(vehicleId),
  });

  const { data: prediction, isLoading: pLoading } = useQuery({
    queryKey: ["battery-predict", vehicleId],
    queryFn: () => api.battery.predict(vehicleId),
  });

  if (vLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-64 animate-pulse rounded bg-surface-elevated" />
        <div className="h-48 animate-pulse rounded-[var(--radius-lg)] bg-surface-elevated" />
      </div>
    );
  }

  if (!vehicle) {
    return (
      <div className="py-16 text-center text-foreground-muted">
        Vehicle not found.{" "}
        <Link href="/fleet" className="text-[var(--signal-info)]">
          Back to fleet
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/fleet"
          className="inline-flex items-center gap-1.5 text-xs text-foreground-muted hover:text-foreground mb-3"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to fleet
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-xl font-semibold tracking-tight data-mono">
            {vehicle.vehicle_id}
          </h1>
          <Badge variant={vehicle.status === "active" ? "positive" : "warning"}>
            {vehicle.status}
          </Badge>
          {prediction && <RiskBadge band={prediction.risk_band} />}
        </div>
        <p className="text-sm text-foreground-muted mt-1">{vehicle.model}</p>
      </div>

      {/* Vehicle profile strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <ProfileStat icon={Battery} label="Battery capacity" value={`${vehicle.battery_capacity_kwh} kWh`} />
        <ProfileStat icon={Gauge} label="Rated range" value={`${vehicle.rated_range_km} km`} />
        <ProfileStat icon={MapPin} label="Depot" value={vehicle.depot} />
        <ProfileStat
          icon={Calendar}
          label="In service"
          value={`${vehicle.days_active ?? "—"} days`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Battery intelligence panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Battery intelligence</CardTitle>
          </CardHeader>
          <CardContent>
            {pLoading ? (
              <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-10 animate-pulse rounded bg-surface-elevated" />
                ))}
              </div>
            ) : prediction ? (
              <div className="space-y-4">
                <Metric
                  label="Current SOH"
                  value={`${prediction.current_soh_pct.toFixed(1)}%`}
                  accent="positive"
                />
                <Metric
                  label="Predicted SOH (next interval)"
                  value={`${prediction.predicted_soh_pct.toFixed(1)}%`}
                  accent="info"
                />
                <Metric
                  label="Failure probability"
                  value={`${(prediction.failure_probability * 100).toFixed(2)}%`}
                  accent={prediction.risk_band === "high" ? "critical" : prediction.risk_band === "medium" ? "warning" : "positive"}
                />
                <Metric
                  label="Estimated remaining useful life"
                  value={`${Math.round(prediction.estimated_rul_days)} days`}
                  accent="neutral"
                />
              </div>
            ) : (
              <div className="text-sm text-foreground-dim py-4">
                No prediction available for this vehicle.
              </div>
            )}
          </CardContent>
        </Card>

        {/* SOH / SOC trend */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Battery health timeline</CardTitle>
          </CardHeader>
          <CardContent>
            {tLoading ? (
              <div className="h-64 animate-pulse rounded-lg bg-surface-elevated" />
            ) : (
              <ResponsiveContainer width="100%" height={256}>
                <LineChart data={telemetry ?? []} margin={{ left: -16, right: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: "var(--foreground-dim)" }}
                    axisLine={false}
                    tickLine={false}
                    minTickGap={40}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "var(--foreground-dim)" }}
                    axisLine={false}
                    tickLine={false}
                    width={40}
                    domain={[0, 100]}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "var(--surface-elevated)",
                      border: "1px solid var(--border-default)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="soh_pct" stroke="#00e5a0" strokeWidth={2} dot={false} name="SOH %" />
                  <Line type="monotone" dataKey="soc_pct" stroke="#3b82f6" strokeWidth={1.5} dot={false} name="SOC %" strokeOpacity={0.6} />
                  <Line type="monotone" dataKey="health_score" stroke="#a78bfa" strokeWidth={1.5} dot={false} name="Health score" strokeOpacity={0.6} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Temperature & wear */}
        <Card>
          <CardHeader>
            <CardTitle>Thermal &amp; wear profile</CardTitle>
          </CardHeader>
          <CardContent>
            {tLoading ? (
              <div className="h-56 animate-pulse rounded-lg bg-surface-elevated" />
            ) : (
              <ResponsiveContainer width="100%" height={224}>
                <LineChart data={telemetry ?? []} margin={{ left: -16, right: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: "var(--foreground-dim)" }} axisLine={false} tickLine={false} minTickGap={40} />
                  <YAxis tick={{ fontSize: 11, fill: "var(--foreground-dim)" }} axisLine={false} tickLine={false} width={40} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--surface-elevated)",
                      border: "1px solid var(--border-default)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="motor_temp_c" stroke="#f5a524" strokeWidth={1.5} dot={false} name="Motor temp °C" />
                  <Line type="monotone" dataKey="brake_wear_pct" stroke="#ff5c5c" strokeWidth={1.5} dot={false} name="Brake wear %" strokeOpacity={0.7} />
                  <Line type="monotone" dataKey="tyre_wear_pct" stroke="#94a3b8" strokeWidth={1.5} dot={false} name="Tyre wear %" strokeOpacity={0.7} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Maintenance history */}
        <Card>
          <CardHeader>
            <CardTitle>Maintenance history</CardTitle>
            <Badge variant="neutral">{maintenance?.length ?? 0} events</Badge>
          </CardHeader>
          <CardContent>
            {!maintenance || maintenance.length === 0 ? (
              <div className="py-8 text-center text-sm text-foreground-dim">
                No maintenance events recorded.
              </div>
            ) : (
              <div className="space-y-1.5 max-h-56 overflow-y-auto">
                {maintenance.map((m, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 rounded-[var(--radius-sm)] border border-border-subtle px-3 py-2.5"
                  >
                    <AlertTriangle className="h-4 w-4 shrink-0 text-[var(--signal-warning)]" />
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium truncate">{m.issue_type}</div>
                      <div className="text-xs text-foreground-dim data-mono">
                        {m.date} · ₹{m.cost_inr.toLocaleString("en-IN")} · {m.downtime_hours}h downtime
                      </div>
                    </div>
                    <Badge variant={m.status === "completed" ? "positive" : "warning"}>
                      {m.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ProfileStat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Battery;
  label: string;
  value: string;
}) {
  return (
    <Card flat className="!p-4">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-surface-elevated shrink-0">
          <Icon className="h-4 w-4 text-foreground-muted" />
        </div>
        <div className="min-w-0">
          <div className="text-[10px] uppercase tracking-wide text-foreground-dim truncate">
            {label}
          </div>
          <div className="text-sm font-medium data-mono truncate">{value}</div>
        </div>
      </div>
    </Card>
  );
}

function Metric({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: "positive" | "warning" | "critical" | "info" | "neutral";
}) {
  const colorMap = {
    positive: "var(--signal-positive)",
    warning: "var(--signal-warning)",
    critical: "var(--signal-critical)",
    info: "var(--signal-info)",
    neutral: "var(--foreground)",
  };
  return (
    <div>
      <div className="text-xs text-foreground-muted">{label}</div>
      <div className="text-xl font-semibold data-mono" style={{ color: colorMap[accent] }}>
        {value}
      </div>
    </div>
  );
}
