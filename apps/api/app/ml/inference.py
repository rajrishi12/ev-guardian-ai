"""
Loads the trained SOH regressor + failure classifier and exposes
prediction functions used by the battery intelligence router and agents.
"""

import os
import joblib
import numpy as np

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

_soh_model = None
_failure_model = None
_meta = None


def _load():
    global _soh_model, _failure_model, _meta
    if _soh_model is None:
        _soh_model = joblib.load(os.path.join(ARTIFACT_DIR, "soh_regressor.joblib"))
    if _failure_model is None:
        _failure_model = joblib.load(os.path.join(ARTIFACT_DIR, "failure_classifier.joblib"))
    if _meta is None:
        _meta = joblib.load(os.path.join(ARTIFACT_DIR, "model_meta.joblib"))
    return _soh_model, _failure_model, _meta


FEATURE_COLS = [
    "odometer_km",
    "cumulative_cycles",
    "ambient_temp_c",
    "motor_temp_c",
    "brake_wear_pct",
    "tyre_wear_pct",
    "daily_km",
    "days_since_commission",
]


def predict_soh_and_risk(features: dict) -> dict:
    """
    features: dict with keys matching FEATURE_COLS
    Returns predicted SOH, failure risk probability, and a risk band.
    """
    soh_model, failure_model, _ = _load()

    x = np.array([[features.get(col, 0.0) for col in FEATURE_COLS]])

    predicted_soh = float(soh_model.predict(x)[0])
    failure_proba = float(failure_model.predict_proba(x)[0][1])

    if failure_proba >= 0.5 or predicted_soh < 80:
        risk_band = "high"
    elif failure_proba >= 0.15 or predicted_soh < 88:
        risk_band = "medium"
    else:
        risk_band = "low"

    return {
        "predicted_soh_pct": round(predicted_soh, 2),
        "failure_probability": round(failure_proba, 4),
        "risk_band": risk_band,
    }


def estimate_rul_days(current_soh: float, cumulative_cycles: float, days_active: int, eol_threshold: float = 70.0) -> float:
    """
    Simple degradation-rate extrapolation: assumes the average historical
    degradation rate (pts lost per day) continues until SOH hits the
    end-of-life threshold (default 70%, common EV industry convention).
    """
    if days_active <= 0:
        return 9999.0
    degradation_rate_per_day = max(0.0001, (100.0 - current_soh) / days_active)
    remaining_pts = max(0.0, current_soh - eol_threshold)
    return round(remaining_pts / degradation_rate_per_day, 0)


def get_model_metadata() -> dict:
    _, _, meta = _load()
    return meta
