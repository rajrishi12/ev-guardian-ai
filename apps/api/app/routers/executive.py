"""
EV Guardian AI — Executive Command Center
==========================================

A single aggregation endpoint that rolls up real data already computed by
the fleet, battery, maintenance, supply-chain, carbon, and procurement
modules into one enterprise "mission control" view. Nothing here is
hardcoded or randomly generated — every figure is derived from the same
Vehicle / Telemetry / MaintenanceEvent / Supplier / CarbonReport rows the
rest of the platform uses, so this stays consistent with every other page.

Where a metric requires an assumption (e.g. converting energy usage into
an operating-cost estimate), the assumption is a named constant defined
here, mirroring the pattern already used in procurement.py.
"""

from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.models import Vehicle, Telemetry, MaintenanceEvent, Supplier, CarbonReport
from app.routers.procurement import _build_recommendation
from app.routers.maintenance import _recommend_action

router = APIRouter(prefix="/api/executive", tags=["executive"])

# Named assumptions (transparent, not magic numbers) — same spirit as procurement.py
GRID_ENERGY_COST_INR_PER_KWH = 8.5
ANNUAL_MAINTENANCE_OLD_INR = 220_000
ANNUAL_MAINTENANCE_NEW_INR = 60_000
ANNUAL_DOWNTIME_COST_PER_PT_HEALTH_LOSS = 4_500


def _urgency_rank(u: str) -> int:
    return {"immediate": 0, "this_week": 1, "this_month": 2}.get(u, 3)


@router.get("/dashboard")
def executive_dashboard(db: Session = Depends(get_db)):
    today = date.today()
    vehicles = db.query(Vehicle).all()
    total_vehicles = len(vehicles)

    # ---------------- Fleet health & battery ----------------
    avg_health = db.query(func.avg(Vehicle.health_score)).scalar() or 0
    avg_soh = db.query(func.avg(Vehicle.final_soh_pct)).scalar() or 0
    active_count = sum(1 for v in vehicles if v.status == "active")
    maintenance_count = sum(1 for v in vehicles if v.status == "maintenance")
    idle_count = sum(1 for v in vehicles if v.status not in ("active", "maintenance"))

    # ---------------- Charging status (derived from latest telemetry SOC) ----------------
    latest_telemetry_sub = (
        db.query(
            Telemetry.vehicle_id,
            func.max(Telemetry.date).label("max_date"),
        )
        .group_by(Telemetry.vehicle_id)
        .subquery()
    )
    latest_rows = (
        db.query(Telemetry)
        .join(
            latest_telemetry_sub,
            (Telemetry.vehicle_id == latest_telemetry_sub.c.vehicle_id)
            & (Telemetry.date == latest_telemetry_sub.c.max_date),
        )
        .all()
    )
    soc_by_vehicle = {r.vehicle_id: r.soc_pct for r in latest_rows}
    charging_now = sum(1 for v in vehicles if v.status == "active" and (soc_by_vehicle.get(v.vehicle_id, 100) or 100) < 35)
    charged_ready = sum(1 for v in vehicles if v.status == "active" and (soc_by_vehicle.get(v.vehicle_id, 0) or 0) >= 35)

    # ---------------- Maintenance / alerts ----------------
    alerts = []
    for v in vehicles:
        action, urgency = _recommend_action(v)
        alerts.append((v, action, urgency))
    critical_alerts = [a for a in alerts if a[2] == "immediate"]

    window_end = today + timedelta(days=7)
    due_soon_events = (
        db.query(MaintenanceEvent)
        .filter(MaintenanceEvent.status == "Scheduled")
        .filter(MaintenanceEvent.date >= today, MaintenanceEvent.date <= window_end)
        .order_by(MaintenanceEvent.date.asc())
        .all()
    )
    if not due_soon_events:
        # demo dataset window may not straddle "today" — fall back to the
        # nearest upcoming scheduled work so the panel still reflects real rows
        due_soon_events = (
            db.query(MaintenanceEvent)
            .filter(MaintenanceEvent.status == "Scheduled")
            .order_by(MaintenanceEvent.date.desc())
            .limit(8)
            .all()
        )
    maintenance_due_count = len(due_soon_events)

    # ---------------- Carbon ----------------
    total_co2_saved = db.query(func.sum(CarbonReport.co2_saved_kgco2)).scalar() or 0
    monthly_carbon = (
        db.query(CarbonReport.month, func.sum(CarbonReport.co2_saved_kgco2))
        .group_by(CarbonReport.month)
        .order_by(CarbonReport.month)
        .all()
    )
    emission_trend_pct = 0.0
    if len(monthly_carbon) >= 2:
        prev, last = monthly_carbon[-2][1], monthly_carbon[-1][1]
        if prev:
            emission_trend_pct = round(((last - prev) / prev) * 100, 1)

    # ---------------- Supply chain ----------------
    suppliers = db.query(Supplier).all()
    avg_supplier_risk = (
        sum(s.overall_risk_score for s in suppliers) / len(suppliers) if suppliers else 0
    )
    top_risk_suppliers = sorted(suppliers, key=lambda s: -s.overall_risk_score)[:3]

    # ---------------- Procurement / cost ----------------
    recs = [_build_recommendation(v) for v in vehicles]
    replace_recs = [r for r in recs if r.recommendation == "replace"]
    # annualized savings implied by executing every current "replace" recommendation
    procurement_savings_est = 0.0
    for v in vehicles:
        rec = next((r for r in recs if r.vehicle_id == v.vehicle_id), None)
        if rec and rec.recommendation == "replace":
            health = v.health_score or 70
            procurement_savings_est += (ANNUAL_MAINTENANCE_OLD_INR - ANNUAL_MAINTENANCE_NEW_INR) + (
                (100 - health) * ANNUAL_DOWNTIME_COST_PER_PT_HEALTH_LOSS
            )

    # Month boundaries computed in Python (portable across sqlite/postgres,
    # unlike func.strftime which is sqlite-only).
    month_start = today.replace(day=1)
    next_month_start = (month_start + timedelta(days=32)).replace(day=1)
    # fall back to the most recent month present in the data if "today"
    # falls outside the generated dataset window (static hackathon dataset)
    latest_maint_date = db.query(func.max(MaintenanceEvent.date)).scalar()
    if latest_maint_date and not (month_start <= latest_maint_date < next_month_start):
        month_start = latest_maint_date.replace(day=1)
        next_month_start = (month_start + timedelta(days=32)).replace(day=1)

    month_maint_cost = (
        db.query(func.sum(MaintenanceEvent.cost_inr))
        .filter(MaintenanceEvent.date >= month_start, MaintenanceEvent.date < next_month_start)
        .scalar()
        or 0
    )
    month_energy_kwh = (
        db.query(func.sum(Telemetry.energy_used_kwh))
        .filter(Telemetry.date >= month_start, Telemetry.date < next_month_start)
        .scalar()
        or 0
    )
    month_charging_cost = month_energy_kwh * GRID_ENERGY_COST_INR_PER_KWH
    monthly_operating_cost = round(month_maint_cost + month_charging_cost, 0)

    # ---------------- Downtime trend (monthly, last 6 months of data) ----------------
    all_maint_events = db.query(MaintenanceEvent.date, MaintenanceEvent.downtime_hours).all()
    downtime_by_month: dict = {}
    for d, hrs in all_maint_events:
        key = d.strftime("%Y-%m")
        downtime_by_month[key] = downtime_by_month.get(key, 0) + (hrs or 0)
    downtime_trend = [
        {"month": m, "downtime_hours": round(h, 1)}
        for m, h in sorted(downtime_by_month.items())
    ][-6:]

    # ---------------- Live notifications (most recent real events) ----------------
    recent_events = (
        db.query(MaintenanceEvent)
        .order_by(MaintenanceEvent.date.desc())
        .limit(6)
        .all()
    )
    notifications = []
    for e in recent_events:
        severity = "critical" if e.category == "Battery" and e.cost_inr and e.cost_inr > 15000 else (
            "warning" if e.status == "Scheduled" else "info"
        )
        notifications.append({
            "id": e.id,
            "vehicle_id": e.vehicle_id,
            "message": f"{e.issue_type} ({e.category}) — {e.status.lower()}",
            "date": str(e.date),
            "severity": severity,
            "cost_inr": e.cost_inr,
        })

    # ---------------- Recent incidents (high-cost / high-downtime events) ----------------
    incident_rows = (
        db.query(MaintenanceEvent)
        .order_by(MaintenanceEvent.downtime_hours.desc())
        .limit(5)
        .all()
    )
    recent_incidents = [
        {
            "vehicle_id": e.vehicle_id,
            "issue_type": e.issue_type,
            "category": e.category,
            "date": str(e.date),
            "downtime_hours": round(e.downtime_hours or 0, 1),
            "cost_inr": e.cost_inr,
            "status": e.status,
        }
        for e in incident_rows
    ]

    # ---------------- AI-generated insights (rule-based over live aggregates) ----------------
    insights = []
    highest_risk_vehicle = max(vehicles, key=lambda v: v.failure_probability or 0, default=None)
    if highest_risk_vehicle and (highest_risk_vehicle.failure_probability or 0) > 0.3:
        rul = highest_risk_vehicle.estimated_rul_days
        insights.append(
            f"{highest_risk_vehicle.vehicle_id} ({highest_risk_vehicle.model}) shows a "
            f"{(highest_risk_vehicle.failure_probability * 100):.0f}% modeled failure probability"
            + (f" with an estimated {rul:.0f} days remaining useful life." if rul else ".")
        )
    if top_risk_suppliers:
        top = top_risk_suppliers[0]
        insights.append(
            f"Supplier {top.name} ({top.material}, {top.region}) carries the highest supply-chain "
            f"risk score in the network at {top.overall_risk_score:.2f}, driven by "
            f"{'geopolitical exposure' if top.geopolitical_risk > top.weather_risk else 'weather/logistics exposure'}."
        )
    if replace_recs:
        insights.append(
            f"{len(replace_recs)} vehicle(s) currently meet replacement criteria; executing all of them "
            f"is projected to free up roughly ₹{procurement_savings_est:,.0f}/yr in maintenance & downtime cost."
        )
    high_temp_count = sum(1 for r in latest_rows if (r.ambient_temp_c or 0) > 38)
    if high_temp_count:
        insights.append(
            f"{high_temp_count} vehicle(s) are currently operating in high ambient temperature (>38°C) "
            f"conditions, which accelerates battery degradation — prioritize thermal management checks."
        )
    if emission_trend_pct:
        direction = "increased" if emission_trend_pct > 0 else "decreased"
        insights.append(
            f"Fleet-wide CO₂ savings {direction} {abs(emission_trend_pct):.1f}% month-over-month."
        )
    if not insights:
        insights.append("Fleet is operating within normal parameters — no elevated risks detected.")

    return {
        "generated_at": today.isoformat(),
        "fleet_health_score": round(avg_health, 1),
        "avg_battery_soh_pct": round(avg_soh, 1),
        "vehicles_online": active_count,
        "vehicles_in_maintenance": maintenance_count,
        "vehicles_idle": idle_count,
        "total_vehicles": total_vehicles,
        "charging": {"charging_now": charging_now, "charged_ready": charged_ready},
        "critical_alerts_count": len(critical_alerts),
        "maintenance_due_count": maintenance_due_count,
        "carbon_saved_kg": round(total_co2_saved, 0),
        "emission_trend_pct": emission_trend_pct,
        "supplier_risk_score": round(avg_supplier_risk, 3),
        "top_risk_suppliers": [
            {"name": s.name, "material": s.material, "risk": s.overall_risk_score} for s in top_risk_suppliers
        ],
        "procurement_savings_est_inr": round(procurement_savings_est, 0),
        "replace_recommended_count": len(replace_recs),
        "monthly_operating_cost_inr": monthly_operating_cost,
        "downtime_trend": downtime_trend,
        "live_notifications": notifications,
        "ai_insights": insights,
        "recent_incidents": recent_incidents,
        "maintenance_due_soon": [
            {
                "vehicle_id": e.vehicle_id,
                "issue_type": e.issue_type,
                "category": e.category,
                "date": str(e.date),
            }
            for e in due_soon_events[:8]
        ],
    }
