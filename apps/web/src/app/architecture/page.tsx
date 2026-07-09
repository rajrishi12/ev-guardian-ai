"use client";

import { ArrowRight, BrainCircuit, Database, Factory, Gauge, Network, Route, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const FLOW = [
  {
    title: "Data ingestion",
    icon: Database,
    accent: "info" as const,
    items: ["Telematics/BMS", "Maintenance history", "Supplier/QC", "Carbon reports"],
  },
  {
    title: "Digital twin",
    icon: Gauge,
    accent: "positive" as const,
    items: ["Vehicle health", "SOH/SOC", "Thermal wear", "Depot context"],
  },
  {
    title: "ML intelligence",
    icon: BrainCircuit,
    accent: "agent" as const,
    items: ["SOH regressor", "Failure classifier", "RUL estimator", "Risk bands"],
  },
  {
    title: "Agent layer",
    icon: Network,
    accent: "warning" as const,
    items: ["Fleet agent", "Battery agent", "Supply-chain agent", "Reporting agent"],
  },
  {
    title: "Decision outputs",
    icon: ShieldCheck,
    accent: "positive" as const,
    items: ["Maintenance plan", "Procurement readiness", "Traceability gaps", "Net-zero priorities"],
  },
];

const AGENTS = [
  "Fleet Agent: status, depot, digital-twin context",
  "Battery APM Agent: SOH, RUL, failure probability, charge guidance",
  "Maintenance Optimizer: bays, shifts, charger uptime, urgency",
  "Procurement Agent: route, payload, dwell, OEM fit, lead time",
  "Supply Chain Agent: supplier concentration, geopolitical risk, genealogy",
  "Carbon Agent: Scope 1/2/3, ICE baseline, CO2 savings",
  "Reporting Agent: executive narrative over all specialist outputs",
];

export default function ArchitecturePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Architecture</h1>
        <p className="text-sm text-foreground-muted">
          Multi-agent industrial EV intelligence platform from data ingestion to operational decisions.
        </p>
      </div>

      <Card flat>
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-3">
          {FLOW.map((stage, index) => {
            const Icon = stage.icon;
            return (
              <div key={stage.title} className="relative">
                <div className="rounded-[var(--radius-sm)] border border-border-subtle bg-surface-elevated/45 p-4 h-full">
                  <div className="flex items-center justify-between gap-2">
                    <Icon className={`h-5 w-5 ${accentClass(stage.accent)}`} />
                    <Badge variant={stage.accent}>{index + 1}</Badge>
                  </div>
                  <div className="mt-3 font-medium">{stage.title}</div>
                  <div className="mt-3 space-y-1">
                    {stage.items.map((item) => (
                      <div key={item} className="text-xs text-foreground-muted">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
                {index < FLOW.length - 1 && (
                  <ArrowRight className="hidden lg:block absolute -right-5 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-dim" />
                )}
              </div>
            );
          })}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <Network className="h-5 w-5 text-[var(--signal-agent)]" />
            <h2 className="text-sm font-medium text-foreground-muted tracking-wide uppercase">
              Multi-agent flow
            </h2>
          </div>
          <div className="space-y-2">
            {AGENTS.map((agent) => (
              <div key={agent} className="rounded-[var(--radius-sm)] border border-border-subtle px-3 py-2 text-sm text-foreground-muted">
                {agent}
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3 mb-4">
            <Factory className="h-5 w-5 text-[var(--signal-warning)]" />
            <h2 className="text-sm font-medium text-foreground-muted tracking-wide uppercase">
              Challenge coverage
            </h2>
          </div>
          <div className="space-y-3">
            <Coverage icon={Gauge} title="EV APM" text="Battery degradation, thermal events, RUL, and high-risk fleet assets." />
            <Coverage icon={Route} title="Electrification readiness" text="Route, payload, dwell windows, charger access, OEM options, and lead times." />
            <Coverage icon={Network} title="Supply chain and QMS" text="Supplier risk, QC drift, traceability gaps, and cell-pack-vehicle genealogy." />
            <Coverage icon={ShieldCheck} title="Net zero operations" text="Scope accounting, ICE baseline savings, and carbon-aware priority decisions." />
          </div>
        </Card>
      </div>
    </div>
  );
}

function accentClass(accent: "positive" | "warning" | "critical" | "info" | "agent") {
  const map = {
    positive: "text-[var(--signal-positive)]",
    warning: "text-[var(--signal-warning)]",
    critical: "text-[var(--signal-critical)]",
    info: "text-[var(--signal-info)]",
    agent: "text-[var(--signal-agent)]",
  };
  return map[accent];
}

function Coverage({
  icon: Icon,
  title,
  text,
}: {
  icon: typeof Gauge;
  title: string;
  text: string;
}) {
  return (
    <div className="flex gap-3 rounded-[var(--radius-sm)] border border-border-subtle bg-surface-elevated/35 p-3">
      <Icon className="h-4 w-4 shrink-0 text-[var(--signal-positive)] mt-0.5" />
      <div>
        <div className="text-sm font-medium">{title}</div>
        <div className="text-xs text-foreground-muted mt-1">{text}</div>
      </div>
    </div>
  );
}
