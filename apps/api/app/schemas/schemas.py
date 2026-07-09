from datetime import date, datetime
from typing import Optional, List, Union
from pydantic import BaseModel, EmailStr


# ---------- Auth ----------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


# ---------- Vehicles ----------

class VehicleOut(BaseModel):
    vehicle_id: str
    model: str
    vehicle_type: str
    battery_capacity_kwh: float
    rated_range_km: float
    depot: str
    depot_lat: float
    depot_lon: float
    current_lat: Optional[float]
    current_lon: Optional[float]
    commission_date: date
    avg_daily_km: float
    final_soh_pct: Optional[float]
    cumulative_cycles: Optional[float]
    odometer_km: Optional[float]
    days_active: Optional[int]
    estimated_rul_days: Optional[float]
    failure_probability: Optional[float]
    health_score: Optional[float]
    status: str

    class Config:
        from_attributes = True


class FleetOverview(BaseModel):
    total_vehicles: int
    active_vehicles: int
    in_maintenance: int
    avg_health_score: float
    avg_soh_pct: float
    high_risk_count: int
    total_odometer_km: float
    total_co2_saved_kg: float


# ---------- Telemetry ----------

class TelemetryOut(BaseModel):
    date: date
    odometer_km: float
    soc_pct: float
    soh_pct: float
    ambient_temp_c: float
    motor_temp_c: float
    cumulative_cycles: float
    brake_wear_pct: float
    tyre_wear_pct: float
    daily_km: float
    energy_used_kwh: float
    health_score: float

    class Config:
        from_attributes = True


class BatteryPrediction(BaseModel):
    vehicle_id: str
    current_soh_pct: float
    predicted_soh_pct: float
    failure_probability: float
    risk_band: str
    estimated_rul_days: float


# ---------- Maintenance ----------

class MaintenanceEventOut(BaseModel):
    date: date
    issue_type: str
    category: str
    cost_inr: float
    downtime_hours: float
    status: str

    class Config:
        from_attributes = True


class MaintenanceAlert(BaseModel):
    vehicle_id: str
    model: str
    risk_band: str
    failure_probability: float
    recommended_action: str
    urgency: str  # "immediate", "this_week", "this_month"


class MaintenanceOptimizerSlot(BaseModel):
    vehicle_id: str
    depot: str
    urgency: str
    assigned_shift: str
    bay: int
    charger_required: bool
    estimated_hours: float
    action: str


class DepotMaintenanceLoad(BaseModel):
    depot: str
    workshop_bays: int
    charger_uptime_pct: float
    planned_jobs: int
    capacity_utilization_pct: float
    risk: str


class MaintenanceOptimization(BaseModel):
    generated_for_days: int
    total_planned_jobs: int
    charger_conflicts: int
    workshop_overload_depots: List[str]
    depot_load: List[DepotMaintenanceLoad]
    schedule: List[MaintenanceOptimizerSlot]


# ---------- Suppliers ----------

class SupplierOut(BaseModel):
    supplier_id: str
    name: str
    region: str
    material: str
    geopolitical_risk: float
    weather_risk: float
    quality_score: float
    lead_time_days: int
    on_time_delivery_pct: float
    overall_risk_score: float

    class Config:
        from_attributes = True


class SupplierInspectionOut(BaseModel):
    supplier_id: str
    date: date
    defect_rate: float
    batch_id: Optional[str] = None
    weld_temp_c: Optional[float] = None
    torque_nm: Optional[float] = None
    cell_voltage_variance_mv: Optional[float] = None
    moisture_ppm: Optional[float] = None
    electrode_thickness_um: Optional[float] = None
    is_defective: Optional[bool] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class QualityDriftAlert(BaseModel):
    supplier_id: str
    supplier_name: str
    parameter: str
    date: date
    value: float
    control_center: float
    control_limit_upper: float
    control_limit_lower: float
    sigma_deviation: float
    severity: str  # "watch" | "out_of_control"


class QualityModelPerformance(BaseModel):
    model_name: str
    trained_on_rows: int
    test_set_size: int
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    roc_auc: Optional[float] = None
    confusion_matrix: dict
    feature_importances: dict
    notes: str


class SupplyChainRiskDashboard(BaseModel):
    geopolitical_exposure: dict
    supplier_concentration: dict
    quality_incidents: List[SupplierInspectionOut]
    traceability_gaps: List[dict]


class TraceabilityNode(BaseModel):
    stage: str
    id: str
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    material: Optional[str] = None
    region: Optional[str] = None
    risk_score: Optional[float] = None
    traceable: bool


class VehicleGenealogy(BaseModel):
    vehicle_id: str
    pack_id: str
    cell_lot: str
    traceability_score: float
    open_gaps: List[str]
    genealogy: List[TraceabilityNode]


class ManufacturingQCSummary(BaseModel):
    total_inspections: int
    avg_defect_rate: float
    suppliers_flagged: List[str]
    ml_high_risk_batches: int = 0
    active_drift_alerts: int = 0


class DefectRiskRequest(BaseModel):
    weld_temp_c: float
    torque_nm: float
    cell_voltage_variance_mv: float
    moisture_ppm: float
    electrode_thickness_um: float


class DefectRiskPrediction(BaseModel):
    weld_temp_c: float
    torque_nm: float
    cell_voltage_variance_mv: float
    moisture_ppm: float
    electrode_thickness_um: float
    defect_risk_probability: float
    risk_band: str
    spc: dict


# ---------- Carbon ----------

class CarbonSummary(BaseModel):
    total_co2_saved_kg: float
    total_scope1_kg: float
    total_scope2_kg: float
    total_scope3_kg: float
    total_ice_equivalent_kg: float
    trees_equivalent: float
    months: List[dict]


# ---------- Procurement ----------

class ProcurementRecommendation(BaseModel):
    vehicle_id: str
    model: str
    current_health_score: float
    recommendation: str  # "replace", "monitor", "retain"
    expected_roi_pct: Optional[float]
    suggested_battery_kwh: Optional[float]
    confidence_score: float
    rationale: str


class ElectrificationReadiness(BaseModel):
    vehicle_id: str
    current_vehicle_type: str
    route_profile: str
    avg_daily_km: float
    payload_tonnes: float
    dwell_hours: float
    charger_access_score: float
    recommended_oem: str
    recommended_battery_kwh: float
    delivery_lead_time_days: int
    readiness_index: float
    readiness_band: str
    confidence_score: float
    blockers: List[str]


class ReadinessValidationRow(BaseModel):
    vehicle_id: str
    model_readiness_index: float
    model_band: str
    baseline_readiness_index: float
    baseline_band: str
    bands_agree: bool


class ReadinessValidationSummary(BaseModel):
    vehicles_scored: int
    band_agreement_pct: float
    mean_absolute_index_difference: float
    correlation: Optional[float] = None
    methodology: str
    rows: List[ReadinessValidationRow]


# ---------- Chat ----------

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    data: Optional[Union[dict, list]] = None
    mode: str = "fallback_no_key"


class ChatStatus(BaseModel):
    gemini_configured: bool
    model: str
