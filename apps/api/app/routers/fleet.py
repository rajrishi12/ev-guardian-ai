from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.models import Vehicle, Telemetry, MaintenanceEvent, CarbonReport
from app.schemas.schemas import VehicleOut, FleetOverview, TelemetryOut, MaintenanceEventOut

router = APIRouter(prefix="/api/fleet", tags=["fleet"])


@router.get("/overview", response_model=FleetOverview)
def fleet_overview(db: Session = Depends(get_db)):
    total = db.query(Vehicle).count()
    active = db.query(Vehicle).filter(Vehicle.status == "active").count()
    maint = db.query(Vehicle).filter(Vehicle.status == "maintenance").count()
    avg_health = db.query(func.avg(Vehicle.health_score)).scalar() or 0
    avg_soh = db.query(func.avg(Vehicle.final_soh_pct)).scalar() or 0
    high_risk = db.query(Vehicle).filter(Vehicle.failure_probability > 0.4).count()
    total_odo = db.query(func.sum(Vehicle.odometer_km)).scalar() or 0
    total_co2 = db.query(func.sum(CarbonReport.co2_saved_kgco2)).scalar() or 0

    return FleetOverview(
        total_vehicles=total,
        active_vehicles=active,
        in_maintenance=maint,
        avg_health_score=round(avg_health, 1),
        avg_soh_pct=round(avg_soh, 1),
        high_risk_count=high_risk,
        total_odometer_km=round(total_odo, 0),
        total_co2_saved_kg=round(total_co2, 0),
    )


@router.get("/vehicles", response_model=list[VehicleOut])
def list_vehicles(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    depot: Optional[str] = None,
    risk: Optional[str] = Query(None, description="low | medium | high"),
    search: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
):
    q = db.query(Vehicle)
    if status:
        q = q.filter(Vehicle.status == status)
    if vehicle_type:
        q = q.filter(Vehicle.vehicle_type == vehicle_type)
    if depot:
        q = q.filter(Vehicle.depot == depot)
    if search:
        q = q.filter(Vehicle.vehicle_id.ilike(f"%{search}%"))
    if risk == "high":
        q = q.filter(Vehicle.failure_probability > 0.4)
    elif risk == "medium":
        q = q.filter(Vehicle.failure_probability.between(0.15, 0.4))
    elif risk == "low":
        q = q.filter(Vehicle.failure_probability <= 0.15)

    return q.order_by(Vehicle.vehicle_id).offset(offset).limit(limit).all()


@router.get("/vehicles/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return v


@router.get("/vehicles/{vehicle_id}/telemetry", response_model=list[TelemetryOut])
def get_vehicle_telemetry(vehicle_id: str, db: Session = Depends(get_db), days: int = 180):
    rows = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(Telemetry.date.desc())
        .limit(days // 3 + 5)
        .all()
    )
    return list(reversed(rows))


@router.get("/vehicles/{vehicle_id}/maintenance", response_model=list[MaintenanceEventOut])
def get_vehicle_maintenance(vehicle_id: str, db: Session = Depends(get_db)):
    return (
        db.query(MaintenanceEvent)
        .filter(MaintenanceEvent.vehicle_id == vehicle_id)
        .order_by(MaintenanceEvent.date.desc())
        .all()
    )


@router.get("/depots")
def list_depots(db: Session = Depends(get_db)):
    rows = (
        db.query(Vehicle.depot, Vehicle.depot_lat, Vehicle.depot_lon, func.count(Vehicle.id))
        .group_by(Vehicle.depot, Vehicle.depot_lat, Vehicle.depot_lon)
        .all()
    )
    return [
        {"depot": r[0], "lat": r[1], "lon": r[2], "vehicle_count": r[3]}
        for r in rows
    ]
