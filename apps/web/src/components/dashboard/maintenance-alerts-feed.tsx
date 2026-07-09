"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { AlertTriangle, Clock, CheckCircle2 } from "lucide-react";

const URGENCY_CONFIG = {
  immediate: { icon: AlertTriangle, variant: "critical" as const, label: "Immediate" },
  this_week: { icon: Clock, variant: "warning" as const, label: "This week" },
  this_month: { icon: CheckCircle2, variant: "info" as const, label: "This month" },
};

export function MaintenanceAlertsFeed() {
  const { data, isLoading } = useQuery({
    queryKey: ["maintenance-alerts"],
    queryFn: () => api.maintenance.alerts(),
  });

  const alerts = (data ?? []).slice(0, 6);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Maintenance alerts</CardTitle>
        <Badge variant="neutral">{data?.length ?? 0} flagged</Badge>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-14 animate-pulse rounded-lg bg-surface-elevated" />
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <div className="py-8 text-center text-sm text-foreground-dim">
            No vehicles currently flagged for maintenance.
          </div>
        ) : (
          <div className="space-y-1.5">
            {alerts.map((alert) => {
              const cfg = URGENCY_CONFIG[alert.urgency];
              const Icon = cfg.icon;
              return (
                <div
                  key={alert.vehicle_id}
                  className="flex items-center gap-3 rounded-[var(--radius-sm)] border border-border-subtle px-3 py-2.5 hover:bg-surface-elevated/50 transition-colors"
                >
                  <Icon
                    className="h-4 w-4 shrink-0"
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
                      <span className="text-sm font-medium data-mono">
                        {alert.vehicle_id}
                      </span>
                      <span className="text-xs text-foreground-dim truncate">
                        {alert.model}
                      </span>
                    </div>
                    <div className="text-xs text-foreground-muted truncate">
                      {alert.recommended_action}
                    </div>
                  </div>
                  <Badge variant={cfg.variant} className="shrink-0">
                    {cfg.label}
                  </Badge>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
