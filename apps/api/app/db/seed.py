"""
Seeds the Postgres database from the generated CSVs in apps/ml/data/out/.

Run inside the api container: python -m app.db.seed
"""

import os
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from app.db.session import SessionLocal, engine, Base
from app.models.models import Vehicle, Telemetry, MaintenanceEvent, Supplier, CarbonReport, User
from app.models.models import SupplierInspection
from app.core.security import hash_password

DATA_DIR = os.getenv(
    "ML_DATA_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "data", "out"),
)


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Apply lightweight schema migration for existing SQLite DBs
    if engine.url.drivername.startswith("sqlite"):
        try:
            db.execute(text("ALTER TABLE suppliers ADD COLUMN traceable BOOLEAN DEFAULT 0"))
            db.commit()
            print("Added missing suppliers.traceable column.")
        except Exception:
            db.rollback()

    if db.query(Vehicle).count() > 0:
        print("Database already seeded. Skipping.")
        db.close()
        return

    print(f"Loading CSVs from {DATA_DIR} ...")
    vehicles_df = pd.read_csv(os.path.join(DATA_DIR, "vehicles.csv"))
    telemetry_df = pd.read_csv(os.path.join(DATA_DIR, "telemetry.csv"))
    maintenance_df = pd.read_csv(os.path.join(DATA_DIR, "maintenance.csv"))
    suppliers_df = pd.read_csv(os.path.join(DATA_DIR, "suppliers.csv"))
    carbon_df = pd.read_csv(os.path.join(DATA_DIR, "carbon_reports.csv"))
    inspections_path = os.path.join(DATA_DIR, "manufacturing_inspections.csv")
    inspections_df = pd.read_csv(inspections_path) if os.path.exists(inspections_path) else None

    print(f"Seeding {len(vehicles_df)} vehicles...")
    for _, row in vehicles_df.iterrows():
        v = Vehicle(
            vehicle_id=row["vehicle_id"],
            model=row["model"],
            vehicle_type=row["vehicle_type"],
            battery_capacity_kwh=row["battery_capacity_kwh"],
            rated_range_km=row["rated_range_km"],
            depot=row["depot"],
            depot_lat=row["depot_lat"],
            depot_lon=row["depot_lon"],
            commission_date=parse_date(row["commission_date"]),
            avg_daily_km=row["avg_daily_km"],
            climate_severity=row["climate_severity"],
            fast_charge_bias=row["fast_charge_bias"],
            final_soh_pct=row["final_soh_pct"],
            cumulative_cycles=row["cumulative_cycles"],
            odometer_km=row["odometer_km"],
            days_active=int(row["days_active"]),
            estimated_rul_days=row["estimated_rul_days"],
            failure_probability=row["failure_probability"],
            current_lat=row["depot_lat"],
            current_lon=row["depot_lon"],
            health_score=max(0, min(100,
                0.55 * row["final_soh_pct"] + 0.45 * (100 - min(100, row["cumulative_cycles"] * 0.05))
            )),
            status="maintenance" if row["failure_probability"] > 0.5 else "active",
        )
        db.add(v)
    db.commit()
    print("Vehicles seeded.")

    print(f"Seeding {len(telemetry_df)} telemetry rows...")
    batch = []
    for _, row in telemetry_df.iterrows():
        batch.append(Telemetry(
            vehicle_id=row["vehicle_id"],
            date=parse_date(row["date"]),
            odometer_km=row["odometer_km"],
            soc_pct=row["soc_pct"],
            soh_pct=row["soh_pct"],
            ambient_temp_c=row["ambient_temp_c"],
            motor_temp_c=row["motor_temp_c"],
            cumulative_cycles=row["cumulative_cycles"],
            brake_wear_pct=row["brake_wear_pct"],
            tyre_wear_pct=row["tyre_wear_pct"],
            daily_km=row["daily_km"],
            energy_used_kwh=row["energy_used_kwh"],
            health_score=row["health_score"],
        ))
        if len(batch) >= 2000:
            db.bulk_save_objects(batch)
            db.commit()
            batch = []
    if batch:
        db.bulk_save_objects(batch)
        db.commit()
    print("Telemetry seeded.")

    print(f"Seeding {len(maintenance_df)} maintenance events...")
    batch = []
    for _, row in maintenance_df.iterrows():
        batch.append(MaintenanceEvent(
            vehicle_id=row["vehicle_id"],
            date=parse_date(row["date"]),
            issue_type=row["issue_type"],
            category=row["category"],
            cost_inr=row["cost_inr"],
            downtime_hours=row["downtime_hours"],
            status=row["status"],
        ))
    db.bulk_save_objects(batch)
    db.commit()
    print("Maintenance events seeded.")

    print(f"Seeding {len(suppliers_df)} suppliers...")
    for _, row in suppliers_df.iterrows():
        db.add(Supplier(
            supplier_id=row["supplier_id"],
            name=row["name"],
            region=row["region"],
            material=row["material"],
            geopolitical_risk=row["geopolitical_risk"],
            weather_risk=row["weather_risk"],
            quality_score=row["quality_score"],
            lead_time_days=int(row["lead_time_days"]),
            on_time_delivery_pct=row["on_time_delivery_pct"],
            overall_risk_score=row["overall_risk_score"],
        ))
    db.commit()
    print("Suppliers seeded.")

    # Seed manufacturing QC inspection batches (process parameters + defect
    # labels) generated by apps/ml/data/generate_dataset.py, so the
    # manufacturing quality dashboard reflects real drift events and the
    # trained defect-risk classifier has matching production data to score.
    if inspections_df is not None:
        print(f"Seeding {len(inspections_df)} manufacturing inspection batches...")
        try:
            batch = []
            for _, row in inspections_df.iterrows():
                batch.append(SupplierInspection(
                    supplier_id=row["supplier_id"],
                    batch_id=row["batch_id"],
                    date=parse_date(row["date"]),
                    defect_rate=row["defect_rate"],
                    weld_temp_c=row["weld_temp_c"],
                    torque_nm=row["torque_nm"],
                    cell_voltage_variance_mv=row["cell_voltage_variance_mv"],
                    moisture_ppm=row["moisture_ppm"],
                    electrode_thickness_um=row["electrode_thickness_um"],
                    is_defective=bool(row["is_defective"]),
                    notes=row.get("notes") or None,
                ))
            db.bulk_save_objects(batch)
            db.commit()
            print("Manufacturing inspections seeded.")
        except Exception as e:
            db.rollback()
            print(f"Manufacturing inspections not seeded: {e}")
    else:
        # Fallback if the manufacturing dataset hasn't been generated yet
        try:
            db.add(SupplierInspection(supplier_id=suppliers_df.iloc[0]["supplier_id"], date=parse_date(telemetry_df.iloc[0]["date"]), defect_rate=0.01, notes="initial batch"))
            db.add(SupplierInspection(supplier_id=suppliers_df.iloc[1]["supplier_id"], date=parse_date(telemetry_df.iloc[1]["date"]), defect_rate=0.03, notes="elevated defects"))
            db.commit()
            print("Supplier inspections seeded (fallback, minimal).")
        except Exception:
            db.rollback()
            print("Supplier inspections not seeded (table may not exist yet)")

    print(f"Seeding {len(carbon_df)} carbon reports...")
    batch = []
    for _, row in carbon_df.iterrows():
        batch.append(CarbonReport(
            vehicle_id=row["vehicle_id"],
            month=row["month"],
            km_driven=row["km_driven"],
            energy_kwh=row["energy_kwh"],
            scope1_kgco2=row["scope1_kgco2"],
            scope2_kgco2=row["scope2_kgco2"],
            scope3_kgco2=row["scope3_kgco2"],
            ice_equivalent_kgco2=row["ice_equivalent_kgco2"],
            co2_saved_kgco2=row["co2_saved_kgco2"],
        ))
    db.bulk_save_objects(batch)
    db.commit()
    print("Carbon reports seeded.")

    print("Seeding demo users...")
    demo_users = [
        ("admin@evguardian.ai", "Aarav Mehta", "admin"),
        ("fleet.manager@evguardian.ai", "Priya Nair", "fleet_manager"),
        ("engineer@evguardian.ai", "Rohan Iyer", "maintenance_engineer"),
        ("exec@evguardian.ai", "Sandra Pinto", "executive"),
    ]
    for email, name, role in demo_users:
        db.add(User(
            email=email,
            full_name=name,
            role=role,
            hashed_password=hash_password("Password123!"),
        ))
    db.commit()
    print("Demo users seeded (password for all: Password123!)")

    db.close()
    print("\nSeed complete.")


if __name__ == "__main__":
    seed()
