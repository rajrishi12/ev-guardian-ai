"""
Loads the trained manufacturing quality/defect classifier and exposes
prediction + SPC (statistical process control) drift-detection functions
used by the manufacturing router.
"""

import os
import joblib
import numpy as np

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

_quality_model = None
_quality_meta = None

FEATURE_COLS = [
    "weld_temp_c",
    "torque_nm",
    "cell_voltage_variance_mv",
    "moisture_ppm",
    "electrode_thickness_um",
]

# Process-control centers + natural (in-control) standard deviations.
# Used for SPC control-chart (z-score) drift detection, independent of the
# ML classifier — this is the same pair of techniques a real manufacturing
# quality team would run side by side (SPC for early warning on a single
# parameter trend, ML classifier for multi-parameter defect risk).
PROCESS_SPECS = {
    "weld_temp_c":              {"center": 245.0, "sd": 4.0,  "usl": 260.0, "lsl": 230.0, "unit": "°C"},
    "torque_nm":                {"center": 12.0,  "sd": 0.6,  "usl": 14.0,  "lsl": 10.0,  "unit": "N·m"},
    "cell_voltage_variance_mv": {"center": 8.0,    "sd": 2.0,  "usl": 18.0,  "lsl": 0.0,   "unit": "mV"},
    "moisture_ppm":             {"center": 120.0, "sd": 15.0, "usl": 180.0, "lsl": 60.0,  "unit": "ppm"},
    "electrode_thickness_um":   {"center": 68.0,  "sd": 1.5,  "usl": 73.0,  "lsl": 63.0,  "unit": "µm"},
}


def _load():
    global _quality_model, _quality_meta
    if _quality_model is None:
        _quality_model = joblib.load(os.path.join(ARTIFACT_DIR, "quality_classifier.joblib"))
    if _quality_meta is None:
        _quality_meta = joblib.load(os.path.join(ARTIFACT_DIR, "quality_model_meta.joblib"))
    return _quality_model, _quality_meta


def predict_defect_risk(features: dict) -> dict:
    """
    features: dict with keys matching FEATURE_COLS (process parameters for
    one inspection batch). Returns the classifier's defect-risk probability
    plus a risk band.
    """
    model, _ = _load()
    x = np.array([[features.get(col, PROCESS_SPECS[col]["center"]) for col in FEATURE_COLS]])
    proba = float(model.predict_proba(x)[0][1])

    if proba >= 0.5:
        band = "high"
    elif proba >= 0.2:
        band = "medium"
    else:
        band = "low"

    return {"defect_risk_probability": round(proba, 4), "risk_band": band}


def spc_z_scores(features: dict) -> dict:
    """
    Classic Western Electric / control-chart style check: how many standard
    deviations each process parameter sits from its in-control center, and
    whether it has breached the spec limit (USL/LSL). This is what lets the
    dashboard say *which* parameter is drifting and by how much, rather than
    only a single opaque risk score.
    """
    out = {}
    for col, spec in PROCESS_SPECS.items():
        val = features.get(col)
        if val is None:
            continue
        z = (val - spec["center"]) / spec["sd"]
        out[col] = {
            "value": round(val, 2),
            "center": spec["center"],
            "z_score": round(z, 2),
            "out_of_spec": bool(val > spec["usl"] or val < spec["lsl"]),
            "out_of_control_3sigma": bool(abs(z) > 3),
            "unit": spec["unit"],
        }
    return out


def get_quality_model_metadata() -> dict:
    _, meta = _load()
    return meta
