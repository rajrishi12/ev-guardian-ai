from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Supplier, Vehicle
from app.schemas.schemas import SupplierOut
from app.models.models import SupplierInspection
from app.schemas.schemas import (
    SupplierInspectionOut,
    SupplyChainRiskDashboard,
    TraceabilityNode,
    VehicleGenealogy,
)

router = APIRouter(prefix="/api/supply-chain", tags=["supply-chain"])


def _supplier_traceable(supplier: Supplier) -> bool:
    if getattr(supplier, "traceable", False):
        return True
    return (supplier.quality_score or 0) >= 0.88 and (supplier.on_time_delivery_pct or 0) >= 88


def _pick_supplier(material_suppliers: list[Supplier], seed: int, offset: int = 0) -> Supplier | None:
    if not material_suppliers:
        return None
    return material_suppliers[(seed + offset) % len(material_suppliers)]


def _trace_node(stage: str, node_id: str, supplier: Supplier | None = None) -> TraceabilityNode:
    if supplier is None:
        return TraceabilityNode(stage=stage, id=node_id, traceable=True)
    return TraceabilityNode(
        stage=stage,
        id=node_id,
        supplier_id=supplier.supplier_id,
        supplier_name=supplier.name,
        material=supplier.material,
        region=supplier.region,
        risk_score=round(supplier.overall_risk_score or 0, 3),
        traceable=_supplier_traceable(supplier),
    )


@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).order_by(Supplier.overall_risk_score.desc()).all()


@router.get("/risk-summary")
def supply_chain_risk_summary(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).all()
    high = [s for s in suppliers if s.overall_risk_score > 0.5]
    medium = [s for s in suppliers if 0.25 < s.overall_risk_score <= 0.5]
    low = [s for s in suppliers if s.overall_risk_score <= 0.25]

    avg_risk = sum(s.overall_risk_score for s in suppliers) / len(suppliers) if suppliers else 0

    return {
        "total_suppliers": len(suppliers),
        "high_risk": len(high),
        "medium_risk": len(medium),
        "low_risk": len(low),
        "avg_risk_score": round(avg_risk, 3),
        "highest_risk_suppliers": [
            {"name": s.name, "material": s.material, "region": s.region, "risk": s.overall_risk_score}
            for s in sorted(suppliers, key=lambda x: -x.overall_risk_score)[:5]
        ],
    }


@router.get("/by-material")
def risk_by_material(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).all()
    materials = {}
    for s in suppliers:
        materials.setdefault(s.material, []).append(s.overall_risk_score)
    return [
        {"material": m, "avg_risk": round(sum(v) / len(v), 3), "supplier_count": len(v)}
        for m, v in materials.items()
    ]


@router.get("/risk-dashboard", response_model=SupplyChainRiskDashboard)
def risk_dashboard(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).all()
    # Geopolitical exposure: percentage share of suppliers by region
    region_counts = {}
    material_market = {}
    for s in suppliers:
        region_counts[s.region] = region_counts.get(s.region, 0) + 1
        material_market.setdefault(s.material, []).append(s)

    total = len(suppliers) or 1
    geopolitical_exposure = {r: int((c / total) * 100) for r, c in region_counts.items()}

    # Supplier concentration by material (top 3 share)
    supplier_concentration = {}
    for m, sl in material_market.items():
        # naive: count suppliers; if there are weights available use them
        counts = len(sl)
        top3 = sl[:3]
        top3_share = round((len(top3) / counts) * 100, 1) if counts else 0
        supplier_concentration[m] = {"top_3_share_pct": top3_share, "supplier_count": counts}

    # Quality incidents from inspections table (recent 90 days)
    try:
        inspections = (
            db.query(SupplierInspection)
            .order_by(SupplierInspection.date.desc())
            .limit(50)
            .all()
        )
        quality_incidents = [
            SupplierInspectionOut(
                supplier_id=i.supplier_id, date=i.date, defect_rate=i.defect_rate, notes=i.notes
            )
            for i in inspections
        ]
    except Exception:
        # If the inspections table is not present or another DB error occurs, return empty list
        quality_incidents = []

    # Traceability gaps
    traceability_gaps = [
        {"supplier_id": s.supplier_id, "name": s.name, "material": s.material}
        for s in suppliers
        if not getattr(s, "traceable", False)
    ]

    return {
        "geopolitical_exposure": geopolitical_exposure,
        "supplier_concentration": supplier_concentration,
        "quality_incidents": quality_incidents,
        "traceability_gaps": traceability_gaps,
    }


@router.get("/traceability/genealogy", response_model=list[VehicleGenealogy])
def vehicle_genealogy(db: Session = Depends(get_db), limit: int = 25):
    vehicles = db.query(Vehicle).order_by(Vehicle.failure_probability.desc()).limit(limit).all()
    suppliers = db.query(Supplier).order_by(Supplier.overall_risk_score.desc()).all()
    by_material: dict[str, list[Supplier]] = {}
    for supplier in suppliers:
        by_material.setdefault(supplier.material.lower(), []).append(supplier)

    cell_suppliers = (
        by_material.get("nmc cells")
        or by_material.get("lfp cells")
        or [s for s in suppliers if "cell" in s.material.lower()]
    )
    lithium_suppliers = [s for s in suppliers if "lithium" in s.material.lower()]
    cobalt_suppliers = [s for s in suppliers if "cobalt" in s.material.lower()]
    nickel_suppliers = [s for s in suppliers if "nickel" in s.material.lower()]

    results = []
    for vehicle in vehicles:
        seed = sum(ord(ch) for ch in vehicle.vehicle_id)
        pack_id = f"PACK-{vehicle.vehicle_id[-4:]}-{int(vehicle.battery_capacity_kwh or 0)}KWH"
        cell_lot = f"CELL-LOT-{seed % 97:02d}-{vehicle.commission_date.year}"

        lithium = _pick_supplier(lithium_suppliers, seed)
        cobalt = _pick_supplier(cobalt_suppliers, seed, 1)
        nickel = _pick_supplier(nickel_suppliers, seed, 2)
        cell_supplier = _pick_supplier(cell_suppliers, seed, 3)

        nodes = [
            _trace_node("lithium carbonate", f"LI-{seed % 9000:04d}", lithium),
            _trace_node("cathode material", f"CAM-{seed % 7000:04d}", cobalt or nickel),
            _trace_node("cell lot", cell_lot, cell_supplier),
            _trace_node("battery pack", pack_id),
            _trace_node("vehicle", vehicle.vehicle_id),
        ]
        untraceable = [n for n in nodes if not n.traceable]
        high_risk = [n for n in nodes if (n.risk_score or 0) > 0.5]
        open_gaps = []
        for node in untraceable:
            open_gaps.append(f"{node.stage} lacks complete supplier certificate chain")
        for node in high_risk:
            open_gaps.append(f"{node.stage} supplier risk above 0.50")
        traceability_score = max(0, 100 - len(untraceable) * 18 - len(high_risk) * 10)

        results.append(VehicleGenealogy(
            vehicle_id=vehicle.vehicle_id,
            pack_id=pack_id,
            cell_lot=cell_lot,
            traceability_score=round(traceability_score, 1),
            open_gaps=open_gaps[:5],
            genealogy=nodes,
        ))

    return results
