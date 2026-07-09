import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { ArrowDown, ArrowUp, type LucideIcon } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  accent?: "positive" | "warning" | "critical" | "info" | "neutral";
  trend?: { value: string; direction: "up" | "down"; good: boolean };
  sublabel?: string;
}

const ACCENT_MAP: Record<NonNullable<KpiCardProps["accent"]>, string> = {
  positive: "var(--signal-positive)",
  warning: "var(--signal-warning)",
  critical: "var(--signal-critical)",
  info: "var(--signal-info)",
  neutral: "var(--foreground-muted)",
};

export function KpiCard({
  label,
  value,
  icon: Icon,
  accent = "neutral",
  trend,
  sublabel,
}: KpiCardProps) {
  const color = ACCENT_MAP[accent];

  return (
    <Card className="relative overflow-hidden">
      <div
        className="absolute -right-6 -top-6 h-24 w-24 rounded-full opacity-[0.08] blur-2xl"
        style={{ background: color }}
      />
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="text-xs font-medium text-foreground-muted uppercase tracking-wide">
            {label}
          </div>
          <div className="text-2xl font-semibold data-mono">{value}</div>
          {sublabel && (
            <div className="text-xs text-foreground-dim">{sublabel}</div>
          )}
        </div>
        <div
          className="flex h-9 w-9 items-center justify-center rounded-lg shrink-0"
          style={{ background: `${color}1f` }}
        >
          <Icon className="h-4.5 w-4.5" style={{ color }} />
        </div>
      </div>
      {trend && (
        <div
          className={cn(
            "mt-3 inline-flex items-center gap-1 text-xs font-medium data-mono",
            trend.good ? "text-[var(--signal-positive)]" : "text-[var(--signal-critical)]"
          )}
        >
          {trend.direction === "up" ? (
            <ArrowUp className="h-3 w-3" />
          ) : (
            <ArrowDown className="h-3 w-3" />
          )}
          {trend.value}
        </div>
      )}
    </Card>
  );
}
