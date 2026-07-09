"""
SQLAlchemy ORM models for EV Guardian AI.

Covers: vehicles, telemetry, maintenance, suppliers, carbon reports, users.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Date, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="fleet_manager")  # admin, fleet_manager, maintenance_engineer, executive
    created_at = Column(DateTime, default=datetime.utcnow)


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, unique=True, index=True, nullable=False)
    model = Column(String, nullable=False)
    vehicle_type = Column(String, nullable=False)
    battery_capacity_kwh = Column(Float, nullable=False)
    rated_range_km = Column(Float, nullable=False)
    depot = Column(String, nullable=False)
    depot_lat = Column(Float, nullable=False)
    depot_lon = Column(Float, nullable=False)
    commission_date = Column(Date, nullable=False)
    avg_daily_km = Column(Float, nullable=False)
    climate_severity = Column(Float, nullable=False)
    fast_charge_bias = Column(Float, nullable=False)

    # latest known state (denormalized for fast dashboard reads)
    final_soh_pct = Column(Float, nullable=True)
    cumulative_cycles = Column(Float, nullable=True)
    odometer_km = Column(Float, nullable=True)
    days_active = Column(Integer, nullable=True)
    estimated_rul_days = Column(Float, nullable=True)
    failure_probability = Column(Float, nullable=True)
    current_lat = Column(Float, nullable=True)
    current_lon = Column(Float, nullable=True)
    health_score = Column(Float, nullable=True)
    status = Column(String, default="active")  # active, maintenance, idle, retired

    telemetry = relationship("Telemetry", back_populates="vehicle", cascade="all, delete-orphan")
    maintenance_events = relationship("MaintenanceEvent", back_populates="vehicle", cascade="all, delete-orphan")


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.vehicle_id"), index=True, nullable=False)
    date = Column(Date, nullable=False)
    odometer_km = Column(Float)
    soc_pct = Column(Float)
    soh_pct = Column(Float)
    ambient_temp_c = Column(Float)
    motor_temp_c = Column(Float)
    cumulative_cycles = Column(Float)
    brake_wear_pct = Column(Float)
    tyre_wear_pct = Column(Float)
    daily_km = Column(Float)
    energy_used_kwh = Column(Float)
    health_score = Column(Float)

    vehicle = relationship("Vehicle", back_populates="telemetry")


class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.vehicle_id"), index=True, nullable=False)
    date = Column(Date, nullable=False)
    issue_type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    cost_inr = Column(Float)
    downtime_hours = Column(Float)
    status = Column(String, default="Completed")

    vehicle = relationship("Vehicle", back_populates="maintenance_events")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    region = Column(String, nullable=False)
    material = Column(String, nullable=False)
    geopolitical_risk = Column(Float)
    weather_risk = Column(Float)
    quality_score = Column(Float)
    lead_time_days = Column(Integer)
    on_time_delivery_pct = Column(Float)
    overall_risk_score = Column(Float)
    traceable = Column(Boolean, default=False)


class SupplierInspection(Base):
    """
    Incoming-inspection / in-line QC record for a manufacturing batch.

    Includes the process parameters recorded at the time of inspection so
    the quality model can learn a real relationship between process drift
    and defect outcomes, not just threshold a defect_rate in isolation.
    """
    __tablename__ = "supplier_inspections"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(String, ForeignKey("suppliers.supplier_id"), index=True, nullable=False)
    batch_id = Column(String, index=True, nullable=True)
    date = Column(Date, nullable=False)
    defect_rate = Column(Float, nullable=False)  # fraction of inspected units failing

    # Process parameters captured at time of inspection (cell/pack manufacturing)
    weld_temp_c = Column(Float, nullable=True)
    torque_nm = Column(Float, nullable=True)
    cell_voltage_variance_mv = Column(Float, nullable=True)
    moisture_ppm = Column(Float, nullable=True)
    electrode_thickness_um = Column(Float, nullable=True)

    # Ground-truth label used to train/evaluate the defect classifier
    is_defective = Column(Boolean, nullable=True)

    notes = Column(Text, nullable=True)

    supplier = relationship("Supplier")


class CarbonReport(Base):
    __tablename__ = "carbon_reports"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.vehicle_id"), index=True, nullable=False)
    month = Column(String, nullable=False)  # e.g. "2026-04"
    km_driven = Column(Float)
    energy_kwh = Column(Float)
    scope1_kgco2 = Column(Float)
    scope2_kgco2 = Column(Float)
    scope3_kgco2 = Column(Float)
    ice_equivalent_kgco2 = Column(Float)
    co2_saved_kgco2 = Column(Float)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
