"""
Shared pytest fixtures.

Tests run against a throwaway SQLite database (never the dev/demo
evguardian.db) seeded with a small, deterministic set of fixture rows —
enough to exercise every router's query logic without depending on the
full generated dataset being present.
"""

import os
import tempfile
from datetime import date, timedelta

import pytest

TEST_DB_FD, TEST_DB_PATH = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("GEMINI_API_KEY", "")

from fastapi.testclient import TestClient  # noqa: E402
from app.db.session import Base, engine, SessionLocal  # noqa: E402
from app.models.models import Vehicle, Supplier, SupplierInspection, CarbonReport, Telemetry  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    today = date.today()

    vehicles = [
        Vehicle(
            vehicle_id="EVG-TEST-01", model="Tata Ace EV", vehicle_type="LCV",
            battery_capacity_kwh=21.3, rated_range_km=154, depot="Bengaluru Plant",
            depot_lat=12.97, depot_lon=77.59, commission_date=today - timedelta(days=400),
            avg_daily_km=90, climate_severity=0.4, fast_charge_bias=0.3,
            final_soh_pct=91.0, cumulative_cycles=500, odometer_km=36000,
            days_active=400, estimated_rul_days=900, failure_probability=0.05,
            health_score=88, status="active",
        ),
        Vehicle(
            vehicle_id="EVG-TEST-02", model="Ashok Leyland Circuit-S", vehicle_type="Bus",
            battery_capacity_kwh=188, rated_range_km=250, depot="Mumbai Depot",
            depot_lat=19.07, depot_lon=72.87, commission_date=today - timedelta(days=1200),
            avg_daily_km=240, climate_severity=0.7, fast_charge_bias=0.6,
            final_soh_pct=78.0, cumulative_cycles=2200, odometer_km=210000,
            days_active=1200, estimated_rul_days=90, failure_probability=0.55,
            health_score=58, status="active",
        ),
    ]
    db.add_all(vehicles)

    suppliers = [
        Supplier(
            supplier_id="SUP-T01", name="Test Cells Inc", region="India",
            material="Lithium-ion Cells", geopolitical_risk=0.2, weather_risk=0.15,
            quality_score=92.0, lead_time_days=30, on_time_delivery_pct=95.0,
            overall_risk_score=0.2, traceable=True,
        ),
        Supplier(
            supplier_id="SUP-T02", name="Test Materials Co", region="China",
            material="Cobalt", geopolitical_risk=0.6, weather_risk=0.3,
            quality_score=80.0, lead_time_days=60, on_time_delivery_pct=85.0,
            overall_risk_score=0.5, traceable=False,
        ),
    ]
    db.add_all(suppliers)
    db.commit()

    telemetry_rows = [
        Telemetry(
            vehicle_id="EVG-TEST-01", date=today, odometer_km=36000, soc_pct=72.0,
            soh_pct=91.0, ambient_temp_c=29.0, motor_temp_c=48.0, cumulative_cycles=500,
            brake_wear_pct=22.0, tyre_wear_pct=30.0, daily_km=90, energy_used_kwh=18.5,
            health_score=88.0,
        ),
        Telemetry(
            vehicle_id="EVG-TEST-02", date=today, odometer_km=210000, soc_pct=55.0,
            soh_pct=78.0, ambient_temp_c=34.0, motor_temp_c=61.0, cumulative_cycles=2200,
            brake_wear_pct=68.0, tyre_wear_pct=71.0, daily_km=240, energy_used_kwh=95.0,
            health_score=58.0,
        ),
    ]
    db.add_all(telemetry_rows)
    db.commit()

    # In-control batches + one clearly out-of-spec batch per supplier so both
    # the SPC drift detector and the ML classifier have something to find.
    inspections = []
    for i in range(15):
        inspections.append(SupplierInspection(
            supplier_id="SUP-T01", batch_id=f"T01-{i:03d}", date=today - timedelta(days=i),
            defect_rate=0.01, weld_temp_c=245.0, torque_nm=12.0,
            cell_voltage_variance_mv=8.0, moisture_ppm=120.0, electrode_thickness_um=68.0,
            is_defective=False,
        ))
    inspections.append(SupplierInspection(
        supplier_id="SUP-T02", batch_id="T02-DRIFT", date=today,
        defect_rate=0.09, weld_temp_c=262.0, torque_nm=14.5,
        cell_voltage_variance_mv=19.0, moisture_ppm=195.0, electrode_thickness_um=74.0,
        is_defective=True,
    ))
    db.add_all(inspections)

    db.add(CarbonReport(
        vehicle_id="EVG-TEST-01", month=today.strftime("%Y-%m"), km_driven=2700,
        energy_kwh=550, scope1_kgco2=0, scope2_kgco2=390.5, scope3_kgco2=44.0,
        ice_equivalent_kgco2=756.0, co2_saved_kgco2=321.5,
    ))
    db.commit()
    db.close()

    yield

    try:
        os.close(TEST_DB_FD)
        os.remove(TEST_DB_PATH)
    except OSError:
        pass


@pytest.fixture()
def client():
    return TestClient(app)
