"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Car,
  BatteryMedium,
  Wrench,
  Network,
  Leaf,
  ShoppingCart,
  MessageSquare,
  Shield,
  Gauge,
  Workflow,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/executive", label: "Executive Command Center", icon: Gauge },
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/fleet", label: "Fleet & Digital Twin", icon: Car },
  { href: "/battery", label: "Battery Intelligence", icon: BatteryMedium },
  { href: "/maintenance", label: "Predictive Maintenance", icon: Wrench },
  { href: "/manufacturing", label: "Manufacturing QC", icon: Shield },
  { href: "/supply-chain", label: "Supply Chain", icon: Network },
  { href: "/carbon", label: "Carbon Intelligence", icon: Leaf },
  { href: "/procurement", label: "Procurement", icon: ShoppingCart },
  { href: "/architecture", label: "Architecture", icon: Workflow },
  { href: "/assistant", label: "AI Assistant", icon: MessageSquare },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-64 shrink-0 flex-col border-r border-border-subtle bg-surface/40 backdrop-blur-xl">
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-border-subtle">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--signal-positive)] to-[var(--signal-info)]">
          <Shield className="h-4 w-4 text-background" strokeWidth={2.5} />
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold tracking-tight">
            EV Guardian
          </div>
          <div className="text-[10px] text-foreground-dim uppercase tracking-wider data-mono">
            Fleet Intelligence
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
        {NAV_ITEMS.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-surface-elevated text-foreground"
                  : "text-foreground-muted hover:bg-surface-elevated/60 hover:text-foreground"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0",
                  active && "text-[var(--signal-positive)]"
                )}
              />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="px-5 py-4 border-t border-border-subtle">
        <div className="text-[10px] text-foreground-dim data-mono leading-relaxed">
          v0.1.0 — hackathon build
          <br />
          100 vehicles · 20 suppliers
        </div>
      </div>
    </aside>
  );
}
