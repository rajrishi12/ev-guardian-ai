"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Bell, Search } from "lucide-react";

/**
 * Signature element: a small animated bar-waveform whose bar heights and
 * color reflect real fleet health (avg_health_score from the live API),
 * not decoration — it's the one piece of motion on an otherwise still UI.
 */
function FleetHeartbeat() {
  const { data } = useQuery({
    queryKey: ["fleet-overview-heartbeat"],
    queryFn: api.fleet.overview,
    refetchInterval: 15_000,
  });

  const health = data?.avg_health_score ?? 0;
  const color =
    health >= 85
      ? "var(--signal-positive)"
      : health >= 70
      ? "var(--signal-warning)"
      : "var(--signal-critical)";

  // 7 bars with varying base heights to look like a waveform, scaled by health
  const bars = [0.5, 0.8, 1, 0.65, 0.9, 0.55, 0.75];

  return (
    <div className="flex items-center gap-3 rounded-full border border-border-default bg-surface-elevated px-3 py-1.5">
      <div className="flex items-end gap-[3px] h-4" aria-hidden>
        {bars.map((h, i) => (
          <span
            key={i}
            className="heartbeat-bar w-[3px] rounded-full"
            style={{
              height: `${h * 100}%`,
              background: color,
              animationDelay: `${i * 0.12}s`,
            }}
          />
        ))}
      </div>
      <span className="text-xs data-mono text-foreground-muted">
        Fleet health{" "}
        <span className="font-semibold" style={{ color }}>
          {health.toFixed(1)}
        </span>
      </span>
    </div>
  );
}

export function Topbar() {
  return (
    <header className="flex h-16 items-center justify-between gap-4 border-b border-border-subtle bg-background/60 backdrop-blur-xl px-6">
      <div className="relative max-w-md flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-dim" />
        <input
          placeholder="Search vehicle ID, supplier, model..."
          className="w-full rounded-[var(--radius-sm)] border border-border-subtle bg-surface py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-dim focus:outline-none focus:border-[var(--signal-info)]"
        />
      </div>

      <div className="flex items-center gap-4">
        <FleetHeartbeat />
        <button
          className="relative flex h-9 w-9 items-center justify-center rounded-full border border-border-default text-foreground-muted hover:text-foreground hover:bg-surface-elevated transition-colors"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-[var(--signal-critical)]" />
        </button>
        <div className="flex items-center gap-2.5 pl-1">
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-[var(--signal-info)] to-[var(--signal-agent)] flex items-center justify-center text-xs font-semibold text-white">
            FM
          </div>
        </div>
      </div>
    </header>
  );
}
