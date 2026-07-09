import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium data-mono",
  {
    variants: {
      variant: {
        neutral: "bg-surface-elevated text-foreground-muted border border-border-default",
        positive: "bg-[var(--signal-positive-dim)] text-[var(--signal-positive)]",
        warning: "bg-[var(--signal-warning-dim)] text-[var(--signal-warning)]",
        critical: "bg-[var(--signal-critical-dim)] text-[var(--signal-critical)]",
        info: "bg-[var(--signal-info-dim)] text-[var(--signal-info)]",
        agent: "bg-[var(--signal-agent-dim)] text-[var(--signal-agent)]",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

/** Maps a low/medium/high risk band to the right badge variant + label. */
export function RiskBadge({ band }: { band: "low" | "medium" | "high" | string }) {
  const map: Record<string, { variant: BadgeProps["variant"]; label: string }> = {
    low: { variant: "positive", label: "LOW RISK" },
    medium: { variant: "warning", label: "MEDIUM RISK" },
    high: { variant: "critical", label: "HIGH RISK" },
  };
  const cfg = map[band] ?? { variant: "neutral", label: band.toUpperCase() };
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
}
