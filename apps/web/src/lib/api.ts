/**
 * EV Guardian AI — API Client
 * Thin typed wrapper around the FastAPI backend. Every function here
 * corresponds to a verified, working endpoint (see apps/api/app/routers).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function parseErrorMessage(res: Response): Promise<string> {
  const text = await res.text().catch(() => "");
  if (!text) return res.statusText;
  try {
    const parsed = JSON.parse(text);
    if (typeof parsed?.detail === "string") return parsed.detail;
  } catch {
    // not JSON — fall through to raw text
  }
  return text;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!res.ok) {
    throw new ApiError(await parseErrorMessage(res), res.status);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------

export interface FleetOverview {
  total_vehicles: number;
  active_vehicles: number;
  in_maintenance: number;
  avg_health_score: number;
  avg_soh_pct: number;
  high_risk_count: number;
  total_odometer_km: number;
  total_co2_saved_kg: number;
}

export interface Vehicle {
  vehicle_id: string;
  model: string;
  vehicle_type: string;
  battery_capacity_kwh: number;
  rated_range_km: number;
  depot: string;
  depot_lat: number;
  depot_lon: number;
  current_lat: number | null;
  current_lon: number | null;
  commission_date: string;
  avg_daily_km: number;
  final_soh_pct: number | null;
  cumulative_cycles: number | null;
  odometer_km: number | null;
  days_active: number | null;
  estimated_rul_days: number | null;
  failure_probability: number | null;
  health_score: number | null;
  status: string;
}

export interface VehicleTelemetryPoint {
  date: string;
  odometer_km: number;
  soc_pct: number;
  soh_pct: number;
  ambient_temp_c: number;
  motor_temp_c: number;
  cumulative_cycles: number;
  brake_wear_pct: number;
  tyre_wear_pct: number;
  daily_km: number;
  energy_used_kwh: number;
  health_score: number;
}

export interface MaintenanceEvent {
  date: string;
  issue_type: string;
  category: string;
  cost_inr: number;
  downtime_hours: number;
  status: string;
}

export interface Depot {
  depot: string;
  lat: number;
  lon: number;
  vehicle_count: number;
}

export interface BatteryPrediction {
  vehicle_id: string;
  current_soh_pct: number;
  predicted_soh_pct: number;
  failure_probability: number;
  risk_band: "low" | "medium" | "high";
  estimated_rul_days: number;
}

export interface FleetRiskSummary {
  low: number;
  medium: number;
  high: number;
}

export interface ModelInfo {
  feature_cols: string[];
  soh_regressor_metrics: { mae: number; r2: number; feature_importances: Record<string, number> };
  failure_classifier_metrics: { accuracy: number; roc_auc: number | null };
  trained_on_rows: number;
  trained_on_vehicles: number;
}

export interface MaintenanceAlert {
  vehicle_id: string;
  model: string;
  risk_band: string;
  failure_probability: number;
  recommended_action: string;
  urgency: "immediate" | "this_week" | "this_month";
}

export interface MaintenanceOptimizerSlot {
  vehicle_id: string;
  depot: string;
  urgency: "immediate" | "this_week" | "this_month";
  assigned_shift: string;
  bay: number;
  charger_required: boolean;
  estimated_hours: number;
  action: string;
}

export interface DepotMaintenanceLoad {
  depot: string;
  workshop_bays: number;
  charger_uptime_pct: number;
  planned_jobs: number;
  capacity_utilization_pct: number;
  risk: "low" | "medium" | "high";
}

export interface MaintenanceOptimization {
  generated_for_days: number;
  total_planned_jobs: number;
  charger_conflicts: number;
  workshop_overload_depots: string[];
  depot_load: DepotMaintenanceLoad[];
  schedule: MaintenanceOptimizerSlot[];
}

export interface Supplier {
  supplier_id: string;
  name: string;
  region: string;
  material: string;
  geopolitical_risk: number;
  weather_risk: number;
  quality_score: number;
  lead_time_days: number;
  on_time_delivery_pct: number;
  overall_risk_score: number;
}

export interface SupplyChainRiskSummary {
  total_suppliers: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  avg_risk_score: number;
  highest_risk_suppliers: { name: string; material: string; region: string; risk: number }[];
}

export interface MaterialRisk {
  material: string;
  avg_risk: number;
  supplier_count: number;
}

export interface SupplierInspection {
  supplier_id: string;
  date: string;
  defect_rate: number;
  notes: string | null;
}

export interface SupplyChainRiskDashboard {
  geopolitical_exposure: Record<string, number>;
  supplier_concentration: Record<
    string,
    { top_3_share_pct: number; supplier_count: number }
  >;
  quality_incidents: SupplierInspection[];
  traceability_gaps: { supplier_id: string; name: string; material: string }[];
}

export interface TraceabilityNode {
  stage: string;
  id: string;
  supplier_id: string | null;
  supplier_name: string | null;
  material: string | null;
  region: string | null;
  risk_score: number | null;
  traceable: boolean;
}

export interface VehicleGenealogy {
  vehicle_id: string;
  pack_id: string;
  cell_lot: string;
  traceability_score: number;
  open_gaps: string[];
  genealogy: TraceabilityNode[];
}

export interface ManufacturingQCSummary {
  total_inspections: number;
  avg_defect_rate: number;
  suppliers_flagged: string[];
}

export interface CarbonSummary {
  total_co2_saved_kg: number;
  total_scope1_kg: number;
  total_scope2_kg: number;
  total_scope3_kg: number;
  total_ice_equivalent_kg: number;
  trees_equivalent: number;
  months: { month: string; co2_saved_kg: number; scope2_kg: number; scope3_kg: number }[];
}

export interface ProcurementRecommendation {
  vehicle_id: string;
  model: string;
  current_health_score: number;
  recommendation: "replace" | "monitor" | "retain";
  expected_roi_pct: number | null;
  suggested_battery_kwh: number | null;
  confidence_score: number;
  rationale: string;
}

export interface ElectrificationReadiness {
  vehicle_id: string;
  current_vehicle_type: string;
  route_profile: string;
  avg_daily_km: number;
  payload_tonnes: number;
  dwell_hours: number;
  charger_access_score: number;
  recommended_oem: string;
  recommended_battery_kwh: number;
  delivery_lead_time_days: number;
  readiness_index: number;
  readiness_band: "ready_now" | "pilot_candidate" | "defer_until_infra_ready";
  confidence_score: number;
  blockers: string[];
}

export interface ExecutiveDashboard {
  generated_at: string;
  fleet_health_score: number;
  avg_battery_soh_pct: number;
  vehicles_online: number;
  vehicles_in_maintenance: number;
  vehicles_idle: number;
  total_vehicles: number;
  charging: { charging_now: number; charged_ready: number };
  critical_alerts_count: number;
  maintenance_due_count: number;
  carbon_saved_kg: number;
  emission_trend_pct: number;
  supplier_risk_score: number;
  top_risk_suppliers: { name: string; material: string; risk: number }[];
  procurement_savings_est_inr: number;
  replace_recommended_count: number;
  monthly_operating_cost_inr: number;
  downtime_trend: { month: string; downtime_hours: number }[];
  live_notifications: {
    id: number;
    vehicle_id: string;
    message: string;
    date: string;
    severity: "critical" | "warning" | "info";
    cost_inr: number | null;
  }[];
  ai_insights: string[];
  recent_incidents: {
    vehicle_id: string;
    issue_type: string;
    category: string;
    date: string;
    downtime_hours: number;
    cost_inr: number | null;
    status: string;
  }[];
  maintenance_due_soon: {
    vehicle_id: string;
    issue_type: string;
    category: string;
    date: string;
  }[];
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  data: Record<string, unknown> | unknown[] | null;
  mode: string;
}

export interface ChatStatus {
  gemini_configured: boolean;
  model: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: { id: number; email: string; full_name: string; role: string };
}

// ---------------------------------------------------------------------
// Fleet
// ---------------------------------------------------------------------

export const api = {
  fleet: {
    overview: () => request<FleetOverview>("/api/fleet/overview"),
    vehicles: (params?: {
      limit?: number;
      offset?: number;
      status?: string;
      vehicle_type?: string;
      depot?: string;
      risk?: "low" | "medium" | "high";
      search?: string;
    }) => {
      const qs = new URLSearchParams();
      if (params?.limit) qs.set("limit", String(params.limit));
      if (params?.offset) qs.set("offset", String(params.offset));
      if (params?.status) qs.set("status", params.status);
      if (params?.vehicle_type) qs.set("vehicle_type", params.vehicle_type);
      if (params?.depot) qs.set("depot", params.depot);
      if (params?.risk) qs.set("risk", params.risk);
      if (params?.search) qs.set("search", params.search);
      return request<Vehicle[]>(`/api/fleet/vehicles?${qs.toString()}`);
    },
    vehicle: (vehicleId: string) =>
      request<Vehicle>(`/api/fleet/vehicles/${vehicleId}`),
    telemetry: (vehicleId: string) =>
      request<VehicleTelemetryPoint[]>(
        `/api/fleet/vehicles/${vehicleId}/telemetry`
      ),
    maintenance: (vehicleId: string) =>
      request<MaintenanceEvent[]>(
        `/api/fleet/vehicles/${vehicleId}/maintenance`
      ),
    depots: () => request<Depot[]>("/api/fleet/depots"),
  },

  battery: {
    predict: (vehicleId: string) =>
      request<BatteryPrediction>(`/api/battery/predict/${vehicleId}`),
    fleetRiskSummary: () =>
      request<FleetRiskSummary>("/api/battery/fleet-risk-summary"),
    modelInfo: () => request<ModelInfo>("/api/battery/model-info"),
  },

  maintenance: {
    alerts: (minUrgency?: "immediate" | "this_week" | "this_month") =>
      request<MaintenanceAlert[]>(
        `/api/maintenance/alerts${minUrgency ? `?min_urgency=${minUrgency}` : ""}`
      ),
    optimizer: (days = 7) =>
      request<MaintenanceOptimization>(`/api/maintenance/optimizer?days=${days}`),
  },

  supplyChain: {
    suppliers: () => request<Supplier[]>("/api/supply-chain/suppliers"),
    riskSummary: () =>
      request<SupplyChainRiskSummary>("/api/supply-chain/risk-summary"),
    byMaterial: () =>
      request<MaterialRisk[]>("/api/supply-chain/by-material"),
    riskDashboard: () =>
      request<SupplyChainRiskDashboard>("/api/supply-chain/risk-dashboard"),
    genealogy: (limit = 25) =>
      request<VehicleGenealogy[]>(`/api/supply-chain/traceability/genealogy?limit=${limit}`),
  },

  manufacturing: {
    qcSummary: () => request<ManufacturingQCSummary>("/api/manufacturing/qc/summary"),
    qcRecent: (limit = 25) =>
      request<SupplierInspection[]>(`/api/manufacturing/qc/recent?limit=${limit}`),
    ingestInspections: (records: SupplierInspection[]) =>
      request<SupplierInspection[]>("/api/manufacturing/qc/ingest", {
        method: "POST",
        body: JSON.stringify(records),
      }),
  },

  carbon: {
    summary: () => request<CarbonSummary>("/api/carbon/summary"),
    byVehicle: (vehicleId: string) =>
      request<Record<string, unknown>[]>(`/api/carbon/by-vehicle/${vehicleId}`),
  },

  procurement: {
    recommendations: (limit = 100) =>
      request<ProcurementRecommendation[]>(
        `/api/procurement/recommendations?limit=${limit}`
      ),
    readiness: (limit = 100) =>
      request<ElectrificationReadiness[]>(
        `/api/procurement/electrification-readiness?limit=${limit}`
      ),
    analyzeCsv: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_BASE}/api/procurement/analyze-csv`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        throw new ApiError(await parseErrorMessage(res), res.status);
      }
      return res.json() as Promise<ProcurementRecommendation[]>;
    },
  },

  executive: {
    dashboard: () => request<ExecutiveDashboard>("/api/executive/dashboard"),
  },

  chat: {
    send: (sessionId: string, message: string) =>
      request<ChatResponse>("/api/chat/", {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId, message }),
      }),
    status: () => request<ChatStatus>("/api/chat/status"),
    history: (sessionId: string) =>
      request<{ role: string; content: string }[]>(
        `/api/chat/history/${sessionId}`
      ),
  },

  auth: {
    login: (email: string, password: string) =>
      request<LoginResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
  },
};

export { ApiError, API_BASE };
