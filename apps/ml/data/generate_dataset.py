"""
EV Guardian AI — Synthetic Fleet Data Generator
=================================================

Generates a physically-plausible dataset for 100 EVs across a 24-month
operating window: vehicle profiles, daily telemetry, battery degradation
trajectories, charging logs, maintenance events, supplier network, weather,
and resulting carbon/fuel-displacement figures.

This is NOT random noise — degradation follows real-world battery aging
curves (calendar aging + cycle aging, Arrhenius temperature acceleration),
so the downstream ML model is learning a genuine (if simplified) physical
relationship rather than memorizing noise. That's what makes the
predictions in the dashboard meaningful rather than decorative.

Output: CSVs in apps/ml/data/out/
"""

import os
import math
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT_DIR, exist_ok=True)

N_VEHICLES = 100
N_SUPPLIERS = 20
SIM_DAYS = 730  # 24 months of operating history
START_DATE = datetime.utcnow() - timedelta(days=SIM_DAYS)

VEHICLE_MODELS = [
    ("Tata Ace EV", "LCV", 21.3, 154),
    ("Mahindra eVerito", "Sedan", 23.0, 181),
    ("Ashok Leyland Circuit-S", "Bus", 188.0, 250),
    ("Tata Ultra T7 EV", "Truck", 50.5, 170),
    ("Switch EiV 22", "Bus", 130.0, 220),
    ("Mahindra Treo Zor", "3-Wheeler Cargo", 7.4, 80),
    ("BharatBenz eCanter", "Truck", 83.0, 200),
    ("Olectra C9", "Bus", 300.0, 300),
]

DEPOTS = [
    ("Bengaluru Depot", 12.9716, 77.5946),
    ("Hyderabad Depot", 17.3850, 78.4867),
    ("Pune Depot", 18.5204, 73.8567),
    ("Chennai Depot", 13.0827, 80.2707),
    ("Delhi-NCR Depot", 28.7041, 77.1025),
    ("Ahmedabad Depot", 23.0225, 72.5714),
]

SUPPLIER_REGIONS = [
    ("CATL", "China", "Lithium-ion Cells", 0.18),
    ("BYD Battery", "China", "Lithium-ion Cells", 0.16),
    ("LG Energy Solution", "South Korea", "Lithium-ion Cells", 0.14),
    ("Samsung SDI", "South Korea", "Lithium-ion Cells", 0.12),
    ("Panasonic Energy", "Japan", "Lithium-ion Cells", 0.10),
    ("Exide Industries", "India", "Lead-acid / Li-ion Pack Assembly", 0.45),
    ("Amara Raja Batteries", "India", "Battery Pack Assembly", 0.40),
    ("Tata Chemicals", "India", "Cathode Materials", 0.35),
    ("SQM", "Chile", "Lithium Carbonate", 0.55),
    ("Albemarle Corp", "USA", "Lithium Hydroxide", 0.30),
    ("Ganfeng Lithium", "China", "Lithium Compounds", 0.22),
    ("Glencore", "DR Congo / Switzerland", "Cobalt", 0.70),
    ("Vale S.A.", "Brazil/Canada", "Nickel", 0.38),
    ("Umicore", "Belgium", "Cathode Recycling", 0.20),
    ("Posco Future M", "South Korea", "Cathode/Anode Materials", 0.25),
    ("Hyundai Mobis", "South Korea", "Motor & Drivetrain", 0.15),
    ("Bosch India", "India", "Power Electronics", 0.20),
    ("Sona BLW Precision", "India", "EV Drivetrain Components", 0.18),
    ("Delta Electronics", "Taiwan", "Charging Infrastructure", 0.28),
    ("ABB E-mobility", "Switzerland", "DC Fast Charging Systems", 0.24),
]


def arrhenius_factor(temp_c, ref_temp=25.0, activation_k=0.045):
    """Higher temps accelerate calendar aging (simplified Arrhenius-style)."""
    return math.exp(activation_k * (temp_c - ref_temp))


def generate_vehicles():
    rows = []
    for i in range(1, N_VEHICLES + 1):
        model_name, vtype, batt_kwh, range_km = random.choice(VEHICLE_MODELS)
        depot_name, lat, lon = random.choice(DEPOTS)
        lat_j = lat + random.uniform(-0.15, 0.15)
        lon_j = lon + random.uniform(-0.15, 0.15)
        commission_offset = random.randint(0, SIM_DAYS - 60)
        commission_date = START_DATE + timedelta(days=commission_offset)
        avg_daily_km = {
            "LCV": random.uniform(60, 140),
            "Sedan": random.uniform(40, 110),
            "Bus": random.uniform(120, 260),
            "Truck": random.uniform(90, 220),
            "3-Wheeler Cargo": random.uniform(50, 100),
        }[vtype]
        climate_severity = random.uniform(0.85, 1.35)  # depot-level temp/humidity stress
        fast_charge_bias = random.uniform(0.1, 0.85)   # fraction of charges that are DC fast

        rows.append({
            "vehicle_id": f"EVG-{i:04d}",
            "model": model_name,
            "vehicle_type": vtype,
            "battery_capacity_kwh": batt_kwh,
            "rated_range_km": range_km,
            "depot": depot_name,
            "depot_lat": round(lat_j, 5),
            "depot_lon": round(lon_j, 5),
            "commission_date": commission_date.date().isoformat(),
            "avg_daily_km": round(avg_daily_km, 1),
            "climate_severity": round(climate_severity, 3),
            "fast_charge_bias": round(fast_charge_bias, 3),
        })
    return pd.DataFrame(rows)


def generate_telemetry_and_battery_history(vehicles_df):
    """
    Day-by-day simulation per vehicle:
      - cumulative cycles & calendar age drive SOH degradation
      - SOH drives RUL and failure probability
      - daily telemetry snapshot (SOC, temp, odometer, health score)
    """
    telemetry_rows = []
    daily_summary_rows = []

    for _, v in vehicles_df.iterrows():
        commission_date = datetime.fromisoformat(v["commission_date"])
        days_active = (datetime.utcnow() - commission_date).days
        days_active = max(days_active, 1)

        batt_kwh = v["battery_capacity_kwh"]
        avg_daily_km = v["avg_daily_km"]
        climate_severity = v["climate_severity"]
        fast_charge_bias = v["fast_charge_bias"]

        # Energy consumption ~ kWh/km varies by vehicle type
        kwh_per_km = batt_kwh / v["rated_range_km"] * random.uniform(0.95, 1.15)

        soh = 100.0
        cum_cycles = 0.0
        odometer = 0.0

        # sample every 3 days to keep dataset size reasonable, but iterate daily for physics
        for day in range(days_active):
            current_date = commission_date + timedelta(days=day)

            # ambient temp seasonal model (India-like): warmer overall, summer peak
            day_of_year = current_date.timetuple().tm_yday
            seasonal = 28 + 9 * math.sin((day_of_year - 80) / 365 * 2 * math.pi)
            ambient_temp = seasonal * climate_severity / 1.0 + np.random.normal(0, 2.0)

            # daily distance with weekday/weekend + random variation
            is_weekend = current_date.weekday() >= 5
            daily_km = max(0, np.random.normal(
                avg_daily_km * (0.6 if is_weekend else 1.05), avg_daily_km * 0.18
            ))
            odometer += daily_km

            # charging cycles: full-equivalent cycles based on energy drawn
            energy_used = daily_km * kwh_per_km
            equivalent_cycles = energy_used / batt_kwh
            cum_cycles += equivalent_cycles

            # degradation: calendar aging (temperature-accelerated) + cycle aging
            calendar_age_years = (day + 1) / 365.0
            temp_factor = arrhenius_factor(ambient_temp)
            calendar_loss = 1.5 * calendar_age_years * temp_factor  # % loss
            cycle_loss = cum_cycles * (0.018 if fast_charge_bias < 0.5 else 0.026)  # fast charging accelerates wear
            soh = max(58.0, 100.0 - calendar_loss - cycle_loss + np.random.normal(0, 0.05))

            # only persist every 3rd day to keep row count manageable (~240 rows/vehicle)
            if day % 3 == 0:
                soc = np.random.uniform(20, 95)
                motor_temp = ambient_temp + np.random.uniform(15, 45)
                brake_wear_pct = min(100, (cum_cycles * 0.04) + np.random.uniform(0, 3))
                tyre_wear_pct = min(100, (odometer / 1000) * 1.8 + np.random.uniform(0, 2))

                health_score = max(0, min(100,
                    0.55 * soh
                    + 0.20 * (100 - brake_wear_pct)
                    + 0.15 * (100 - tyre_wear_pct)
                    + 0.10 * max(0, 100 - abs(motor_temp - 70))
                ))

                telemetry_rows.append({
                    "vehicle_id": v["vehicle_id"],
                    "date": current_date.date().isoformat(),
                    "odometer_km": round(odometer, 1),
                    "soc_pct": round(soc, 1),
                    "soh_pct": round(soh, 2),
                    "ambient_temp_c": round(ambient_temp, 1),
                    "motor_temp_c": round(motor_temp, 1),
                    "cumulative_cycles": round(cum_cycles, 2),
                    "brake_wear_pct": round(brake_wear_pct, 2),
                    "tyre_wear_pct": round(tyre_wear_pct, 2),
                    "daily_km": round(daily_km, 1),
                    "energy_used_kwh": round(energy_used, 2),
                    "health_score": round(health_score, 1),
                })

        # failure probability heuristic for labeling (used as ML training target)
        rul_cycles_est = max(0, (100 - 70) / max(0.0001, (100 - soh) / max(cum_cycles, 1)) - cum_cycles)
        rul_days_est = rul_cycles_est * (days_active / max(cum_cycles, 1))
        failure_risk = 1 / (1 + math.exp(-(0.12 * (100 - soh) - 2.2)))  # logistic risk curve

        daily_summary_rows.append({
            "vehicle_id": v["vehicle_id"],
            "final_soh_pct": round(soh, 2),
            "cumulative_cycles": round(cum_cycles, 2),
            "odometer_km": round(odometer, 1),
            "days_active": days_active,
            "estimated_rul_days": round(max(0, rul_days_est), 0),
            "failure_probability": round(min(0.99, max(0.005, failure_risk)), 4),
        })

    telemetry_df = pd.DataFrame(telemetry_rows)
    summary_df = pd.DataFrame(daily_summary_rows)
    return telemetry_df, summary_df


def generate_maintenance_logs(vehicles_df, summary_df):
    rows = []
    merged = vehicles_df.merge(summary_df, on="vehicle_id")
    issue_types = [
        ("Brake Pad Replacement", "Mechanical", 1200, 2),
        ("Tyre Rotation/Replacement", "Mechanical", 3500, 1),
        ("Battery Coolant Service", "Battery", 2200, 3),
        ("Motor Bearing Inspection", "Motor", 1800, 2),
        ("Charging Port Repair", "Electrical", 900, 1),
        ("Software/Firmware Update", "Electrical", 0, 0),
        ("BMS Recalibration", "Battery", 1500, 1),
        ("Suspension Check", "Mechanical", 2800, 2),
    ]
    for _, v in merged.iterrows():
        n_events = max(1, int(v["cumulative_cycles"] / 150) + random.randint(0, 3))
        commission = datetime.fromisoformat(v["commission_date"])
        for _ in range(n_events):
            issue, category, cost, downtime = random.choice(issue_types)
            event_date = commission + timedelta(days=random.randint(0, v["days_active"]))
            rows.append({
                "vehicle_id": v["vehicle_id"],
                "date": event_date.date().isoformat(),
                "issue_type": issue,
                "category": category,
                "cost_inr": cost + random.randint(-200, 500),
                "downtime_hours": downtime * random.uniform(0.7, 1.6),
                "status": random.choice(["Completed", "Completed", "Completed", "Scheduled"]),
            })
    return pd.DataFrame(rows)


def generate_suppliers():
    rows = []
    for i, (name, region, material, base_risk) in enumerate(SUPPLIER_REGIONS, start=1):
        geopolitical_risk = round(min(0.95, max(0.05, base_risk + np.random.normal(0, 0.08))), 3)
        weather_risk = round(random.uniform(0.05, 0.6), 3)
        quality_score = round(random.uniform(78, 99), 1)
        lead_time_days = random.randint(7, 75)
        on_time_pct = round(random.uniform(72, 99), 1)
        overall_risk = round(min(0.99, 0.45 * geopolitical_risk + 0.25 * weather_risk +
                                  0.20 * (1 - quality_score / 100) + 0.10 * (1 - on_time_pct / 100)), 3)
        rows.append({
            "supplier_id": f"SUP-{i:03d}",
            "name": name,
            "region": region,
            "material": material,
            "geopolitical_risk": geopolitical_risk,
            "weather_risk": weather_risk,
            "quality_score": quality_score,
            "lead_time_days": lead_time_days,
            "on_time_delivery_pct": on_time_pct,
            "overall_risk_score": overall_risk,
        })
    return pd.DataFrame(rows)


def generate_carbon_reports(vehicles_df, telemetry_df):
    """
    Monthly carbon report per vehicle, scope1/2/3 approximation.

    The diesel-equivalent comparison must scale with vehicle class — a diesel
    bus or truck emits far more CO2/km than a diesel sedan, so a single flat
    ICE factor would (incorrectly) make heavy-EV operation look worse than
    diesel once grid emissions are counted. Real-world diesel emission
    factors by class (kg CO2/km, well-to-wheel approx):
    """
    ICE_EMISSION_FACTOR_BY_TYPE = {
        "3-Wheeler Cargo": 0.12,
        "Sedan": 0.18,
        "LCV": 0.28,
        "Truck": 0.95,
        "Bus": 1.15,
    }
    GRID_EMISSION_FACTOR_KG_PER_KWH = 0.71  # India grid avg (approx, illustrative)

    telemetry_df = telemetry_df.copy()
    telemetry_df["date"] = pd.to_datetime(telemetry_df["date"])
    telemetry_df["month"] = telemetry_df["date"].dt.to_period("M").astype(str)

    monthly = telemetry_df.groupby(["vehicle_id", "month"]).agg(
        km_driven=("daily_km", "sum"),
        energy_kwh=("energy_used_kwh", "sum"),
    ).reset_index()

    type_map = vehicles_df.set_index("vehicle_id")["vehicle_type"].to_dict()
    monthly["ice_factor"] = monthly["vehicle_id"].map(type_map).map(ICE_EMISSION_FACTOR_BY_TYPE).fillna(0.18)

    monthly["scope1_kgco2"] = 0.0  # EVs: no direct tailpipe emissions
    monthly["scope2_kgco2"] = round(monthly["energy_kwh"] * GRID_EMISSION_FACTOR_KG_PER_KWH, 2)
    monthly["scope3_kgco2"] = round(monthly["energy_kwh"] * 0.08, 2)  # upstream battery/material footprint approx
    monthly["ice_equivalent_kgco2"] = round(monthly["km_driven"] * monthly["ice_factor"], 2)
    monthly["co2_saved_kgco2"] = round(
        monthly["ice_equivalent_kgco2"] - (monthly["scope2_kgco2"] + monthly["scope3_kgco2"]), 2
    )
    monthly = monthly.drop(columns=["ice_factor"])
    return monthly


def generate_manufacturing_inspections(suppliers_df):
    """
    Cell/pack manufacturing incoming + in-line inspection records.

    Each row is one inspection batch for a supplier on a given date, with the
    process parameters recorded at that moment (weld temperature, torque,
    cell voltage variance, moisture, electrode thickness) plus the resulting
    defect rate and a ground-truth is_defective label for the batch.

    The defect probability is NOT independent of the process parameters —
    it is generated as a function of how far each parameter has drifted from
    its process-control center, with a sustained "drift event" injected for
    a subset of supplier/parameter combinations (simulating a tool wearing
    out or a calibration slipping). This gives the quality classifier and
    the SPC drift detector a genuine signal to learn/detect, rather than
    being a threshold on a single unexplained number.
    """
    rng = np.random.default_rng(SEED)

    SPECS = {
        "weld_temp_c":              {"center": 245.0, "sd": 4.0,  "usl": 260.0, "lsl": 230.0},
        "torque_nm":                {"center": 12.0,  "sd": 0.6,  "usl": 14.0,  "lsl": 10.0},
        "cell_voltage_variance_mv": {"center": 8.0,    "sd": 2.0,  "usl": 18.0,  "lsl": 0.0},
        "moisture_ppm":             {"center": 120.0, "sd": 15.0, "usl": 180.0, "lsl": 60.0},
        "electrode_thickness_um":   {"center": 68.0,  "sd": 1.5,  "usl": 73.0,  "lsl": 63.0},
    }

    BATCHES_PER_SUPPLIER = 90  # roughly one every ~3 days over the sim window
    supplier_ids = suppliers_df["supplier_id"].tolist()

    drift_events = []
    for sup in rng.choice(supplier_ids, size=max(1, len(supplier_ids) // 3), replace=False):
        param = rng.choice(list(SPECS.keys()))
        drift_events.append({
            "supplier_id": sup,
            "param": param,
            "start_batch_frac": rng.uniform(0.45, 0.7),
            "direction": int(rng.choice([-1, 1])),
            "magnitude_sd": float(rng.uniform(1.8, 3.2)),
        })
    drift_lookup = {(d["supplier_id"], d["param"]): d for d in drift_events}

    rows = []
    dates = pd.date_range(START_DATE, periods=SIM_DAYS, freq="D")

    for sup in supplier_ids:
        for b in range(BATCHES_PER_SUPPLIER):
            batch_frac = b / BATCHES_PER_SUPPLIER
            date = dates[int(batch_frac * (SIM_DAYS - 1))]
            batch_id = f"BATCH-{sup}-{b+1:04d}"

            values = {}
            oos_flags = 0
            drift_severity = 0.0
            drifted = False

            for param, spec in SPECS.items():
                center, sd = spec["center"], spec["sd"]
                key = (sup, param)
                if key in drift_lookup and batch_frac >= drift_lookup[key]["start_batch_frac"]:
                    d = drift_lookup[key]
                    center = center + d["direction"] * d["magnitude_sd"] * sd
                    drift_severity = max(drift_severity, d["magnitude_sd"])
                    drifted = True

                val = max(0.0, float(rng.normal(center, sd)))
                values[param] = round(val, 2)
                if val > spec["usl"] or val < spec["lsl"]:
                    oos_flags += 1

            base_defect_p = 0.015
            defect_p = base_defect_p + oos_flags * 0.09 + (0.04 * drift_severity if drift_severity else 0.0)
            defect_p = min(0.85, defect_p)

            n_units = int(rng.integers(150, 400))
            n_defective = int(rng.binomial(n_units, defect_p))
            defect_rate = round(n_defective / n_units, 4)
            # Ground-truth label reflects whether the *underlying process*
            # was out of control (defect_p above the control threshold),
            # not the small-sample realized defect_rate — this mirrors real
            # SPC practice where a batch is judged defective based on process
            # capability, with the observed defect_rate as noisy supporting
            # evidence rather than the label itself.
            is_defective_batch = bool(defect_p > 0.045)

            rows.append({
                "supplier_id": sup,
                "batch_id": batch_id,
                "date": date.strftime("%Y-%m-%d"),
                "units_inspected": n_units,
                "units_defective": n_defective,
                "defect_rate": defect_rate,
                "weld_temp_c": values["weld_temp_c"],
                "torque_nm": values["torque_nm"],
                "cell_voltage_variance_mv": values["cell_voltage_variance_mv"],
                "moisture_ppm": values["moisture_ppm"],
                "electrode_thickness_um": values["electrode_thickness_um"],
                "out_of_spec_param_count": oos_flags,
                "is_defective": is_defective_batch,
                "notes": "process drift event" if drifted else "",
            })

    df = pd.DataFrame(rows)
    drift_summary = [
        {"supplier_id": d["supplier_id"], "parameter": d["param"],
         "starts_at_batch_fraction": round(d["start_batch_frac"], 2),
         "direction": "increase" if d["direction"] > 0 else "decrease",
         "magnitude_sd": round(d["magnitude_sd"], 2)}
        for d in drift_events
    ]
    return df, drift_summary


def main():
    print("Generating vehicles...")
    vehicles_df = generate_vehicles()

    print("Simulating telemetry & battery degradation (this models real physics, takes a moment)...")
    telemetry_df, summary_df = generate_telemetry_and_battery_history(vehicles_df)

    print("Generating maintenance logs...")
    maintenance_df = generate_maintenance_logs(vehicles_df, summary_df)

    print("Generating supplier network...")
    suppliers_df = generate_suppliers()

    print("Generating carbon reports...")
    carbon_df = generate_carbon_reports(vehicles_df, telemetry_df)

    print("Generating manufacturing QC inspections (with process-parameter drift events)...")
    inspections_df, drift_summary = generate_manufacturing_inspections(suppliers_df)

    vehicles_df = vehicles_df.merge(summary_df, on="vehicle_id")

    vehicles_df.to_csv(os.path.join(OUT_DIR, "vehicles.csv"), index=False)
    telemetry_df.to_csv(os.path.join(OUT_DIR, "telemetry.csv"), index=False)
    maintenance_df.to_csv(os.path.join(OUT_DIR, "maintenance.csv"), index=False)
    suppliers_df.to_csv(os.path.join(OUT_DIR, "suppliers.csv"), index=False)
    carbon_df.to_csv(os.path.join(OUT_DIR, "carbon_reports.csv"), index=False)
    inspections_df.to_csv(os.path.join(OUT_DIR, "manufacturing_inspections.csv"), index=False)
    pd.DataFrame(drift_summary).to_csv(os.path.join(OUT_DIR, "manufacturing_drift_events.csv"), index=False)

    print(f"""
Done. Files written to {OUT_DIR}:
  vehicles.csv                     {len(vehicles_df)} rows
  telemetry.csv                    {len(telemetry_df)} rows
  maintenance.csv                  {len(maintenance_df)} rows
  suppliers.csv                    {len(suppliers_df)} rows
  carbon_reports.csv                {len(carbon_df)} rows
  manufacturing_inspections.csv    {len(inspections_df)} rows
  manufacturing_drift_events.csv   {len(drift_summary)} injected drift events
""")


if __name__ == "__main__":
    main()
