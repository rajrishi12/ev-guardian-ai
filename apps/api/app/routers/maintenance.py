from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Telemetry, Vehicle
from app.schemas.schemas import (
    DepotMaintenanceLoad,
    MaintenanceAlert,
    MaintenanceOptimization,
    MaintenanceOptimizerSlot,
)

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

DEPOT_WORKSHOP_CAPACITY = {
    "Bengaluru Plant": {"bays": 4, "charger_uptime_pct": 96.0},
    "Chennai Port": {"bays": 3, "charger_uptime_pct": 91.5},
    "Delhi NCR Hub": {"bays": 4, "charger_uptime_pct": 88.0},
    "Mumbai Depot": {"bays": 3, "charger_uptime_pct": 84.5},
    "Pune Plant": {"bays": 3, "charger_uptime_pct": 94.0},
}

SHIFT_WINDOWS = ["A shift 06:00-14:00", "B shift 14:00-22:00", "C shift 22:00-06:00"]


def _recommend_action(vehicle: Vehicle) -> tuple[str, str]:
    p = vehicle.failure_probability or 0
    soh = vehicle.final_soh_pct or 100

    if p > 0.55 or soh < 80:
        return ("Schedule battery pack inspection and BMS recalibration immediately.", "immediate")
    if p > 0.35 or soh < 86:
        return ("Plan preventive battery & motor diagnostic within 7 days.", "this_week")
    if p > 0.15 or soh < 92:
        return ("Add to monthly preventive maintenance cycle; monitor SOH trend.", "this_month")
    return ("No action needed. Continue standard maintenance schedule.", "this_month")


@router.get("/alerts", response_model=list[MaintenanceAlert])
def get_maintenance_alerts(db: Session = Depends(get_db), min_urgency: str = "this_month"):
    vehicles = db.query(Vehicle).order_by(Vehicle.failure_probability.desc()).all()
    urgency_rank = {"immediate": 0, "this_week": 1, "this_month": 2}
    threshold = urgency_rank.get(min_urgency, 2)

    alerts = []
    for v in vehicles:
        action, urgency = _recommend_action(v)
        if urgency_rank[urgency] <= threshold:
            risk_band = "high" if (v.failure_probability or 0) > 0.4 else ("medium" if (v.failure_probability or 0) > 0.15 else "low")
            alerts.append(MaintenanceAlert(
                vehicle_id=v.vehicle_id,
                model=v.model,
                risk_band=risk_band,
                failure_probability=round(v.failure_probability or 0, 4),
                recommended_action=action,
                urgency=urgency,
            ))
    return alerts


@router.get("/optimizer", response_model=MaintenanceOptimization)
def optimize_maintenance_plan(db: Session = Depends(get_db), days: int = 7):
    """
    Converts predictive alerts into an executable workshop plan using depot
    bay capacity, charging uptime, SOC, and shift windows.
    """
    vehicles = db.query(Vehicle).order_by(Vehicle.failure_probability.desc()).all()
    latest_rows = (
        db.query(Telemetry)
        .order_by(Telemetry.vehicle_id, Telemetry.date.desc())
        .all()
    )
    latest_by_vehicle = {}
    for row in latest_rows:
        latest_by_vehicle.setdefault(row.vehicle_id, row)

    candidates = []
    urgency_rank = {"immediate": 0, "this_week": 1, "this_month": 2}
    for vehicle in vehicles:
        action, urgency = _recommend_action(vehicle)
        if urgency == "this_month" and (vehicle.failure_probability or 0) < 0.2:
            continue
        telemetry = latest_by_vehicle.get(vehicle.vehicle_id)
        needs_charger = bool(telemetry and telemetry.soc_pct < 45)
        estimate = 2.0
        if urgency == "immediate":
            estimate = 5.5
        elif urgency == "this_week":
            estimate = 3.5
        if needs_charger:
            estimate += 1.0
        candidates.append((vehicle, action, urgency, needs_charger, estimate))

    candidates.sort(key=lambda c: (urgency_rank[c[2]], -(c[0].failure_probability or 0)))

    planned_by_depot = {}
    schedule = []
    charger_conflicts = 0

    for vehicle, action, urgency, needs_charger, estimate in candidates[: min(40, len(candidates))]:
        depot_state = DEPOT_WORKSHOP_CAPACITY.get(
            vehicle.depot,
            {"bays": 2, "charger_uptime_pct": 88.0},
        )
        planned_count = planned_by_depot.get(vehicle.depot, 0)
        bay = planned_count % depot_state["bays"] + 1
        shift = SHIFT_WINDOWS[(planned_count // depot_state["bays"]) % len(SHIFT_WINDOWS)]
        if needs_charger and depot_state["charger_uptime_pct"] < 90:
            charger_conflicts += 1
            action = f"{action} Reserve mobile charger due to depot uptime below 90%."
        planned_by_depot[vehicle.depot] = planned_count + 1
        schedule.append(MaintenanceOptimizerSlot(
            vehicle_id=vehicle.vehicle_id,
            depot=vehicle.depot,
            urgency=urgency,
            assigned_shift=shift,
            bay=bay,
            charger_required=needs_charger,
            estimated_hours=round(estimate, 1),
            action=action,
        ))

    depot_load = []
    overloaded = []
    for depot, planned_jobs in sorted(planned_by_depot.items()):
        depot_state = DEPOT_WORKSHOP_CAPACITY.get(
            depot,
            {"bays": 2, "charger_uptime_pct": 88.0},
        )
        weekly_capacity = depot_state["bays"] * len(SHIFT_WINDOWS) * max(1, days)
        utilization = round((planned_jobs / weekly_capacity) * 100, 1)
        risk = "high" if utilization > 80 or depot_state["charger_uptime_pct"] < 86 else (
            "medium" if utilization > 55 or depot_state["charger_uptime_pct"] < 91 else "low"
        )
        if risk == "high":
            overloaded.append(depot)
        depot_load.append(DepotMaintenanceLoad(
            depot=depot,
            workshop_bays=depot_state["bays"],
            charger_uptime_pct=depot_state["charger_uptime_pct"],
            planned_jobs=planned_jobs,
            capacity_utilization_pct=utilization,
            risk=risk,
        ))

    return MaintenanceOptimization(
        generated_for_days=days,
        total_planned_jobs=len(schedule),
        charger_conflicts=charger_conflicts,
        workshop_overload_depots=overloaded,
        depot_load=depot_load,
        schedule=schedule,
    )
