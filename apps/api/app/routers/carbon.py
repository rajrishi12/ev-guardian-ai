from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.models import CarbonReport
from app.schemas.schemas import CarbonSummary

router = APIRouter(prefix="/api/carbon", tags=["carbon"])

KG_CO2_PER_TREE_PER_YEAR = 21.0  # commonly cited average absorption rate


@router.get("/summary", response_model=CarbonSummary)
def carbon_summary(db: Session = Depends(get_db)):
    total_saved = db.query(func.sum(CarbonReport.co2_saved_kgco2)).scalar() or 0
    total_s1 = db.query(func.sum(CarbonReport.scope1_kgco2)).scalar() or 0
    total_s2 = db.query(func.sum(CarbonReport.scope2_kgco2)).scalar() or 0
    total_s3 = db.query(func.sum(CarbonReport.scope3_kgco2)).scalar() or 0
    total_ice = db.query(func.sum(CarbonReport.ice_equivalent_kgco2)).scalar() or 0

    monthly = (
        db.query(
            CarbonReport.month,
            func.sum(CarbonReport.co2_saved_kgco2).label("saved"),
            func.sum(CarbonReport.scope2_kgco2).label("scope2"),
            func.sum(CarbonReport.scope3_kgco2).label("scope3"),
        )
        .group_by(CarbonReport.month)
        .order_by(CarbonReport.month)
        .all()
    )

    return CarbonSummary(
        total_co2_saved_kg=round(total_saved, 0),
        total_scope1_kg=round(total_s1, 0),
        total_scope2_kg=round(total_s2, 0),
        total_scope3_kg=round(total_s3, 0),
        total_ice_equivalent_kg=round(total_ice, 0),
        trees_equivalent=round(total_saved / KG_CO2_PER_TREE_PER_YEAR, 0),
        months=[
            {"month": m, "co2_saved_kg": round(s, 0), "scope2_kg": round(s2, 0), "scope3_kg": round(s3, 0)}
            for m, s, s2, s3 in monthly
        ],
    )


@router.get("/by-vehicle/{vehicle_id}")
def carbon_by_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(CarbonReport)
        .filter(CarbonReport.vehicle_id == vehicle_id)
        .order_by(CarbonReport.month)
        .all()
    )
    return [
        {
            "month": r.month,
            "co2_saved_kg": r.co2_saved_kgco2,
            "scope2_kg": r.scope2_kgco2,
            "scope3_kg": r.scope3_kgco2,
            "km_driven": r.km_driven,
        }
        for r in rows
    ]
