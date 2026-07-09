"""
EV Guardian AI — Battery Intelligence Model Training
======================================================

Trains two real models on the synthetic-but-physically-grounded dataset:

1. SOH Regressor (XGBoost) — predicts current State of Health from
   telemetry features (cycles, age, temp exposure, wear indicators).
2. Failure Risk Classifier (XGBoost) — predicts probability that a
   vehicle's battery falls into a "high risk" band (label derived from
   the failure_probability the simulator computed from degradation curves).

These are genuinely fit/validated models (train/test split + metrics
printed), not hardcoded formulas — so predictions served by the API
reflect a real learned relationship between telemetry and battery health.

Run from /apps/ml: python training/train_battery_model.py
Outputs artifacts to apps/api/app/ml/artifacts/
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, roc_auc_score, accuracy_score
from xgboost import XGBRegressor, XGBClassifier

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "out")
ARTIFACT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "api", "app", "ml", "artifacts"
)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

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


def build_training_frame():
    telemetry = pd.read_csv(os.path.join(DATA_DIR, "telemetry.csv"))
    vehicles = pd.read_csv(os.path.join(DATA_DIR, "vehicles.csv"))

    telemetry["date"] = pd.to_datetime(telemetry["date"])
    vehicles_small = vehicles[["vehicle_id", "commission_date", "battery_capacity_kwh"]].copy()
    vehicles_small["commission_date"] = pd.to_datetime(vehicles_small["commission_date"])

    df = telemetry.merge(vehicles_small, on="vehicle_id")
    df["days_since_commission"] = (df["date"] - df["commission_date"]).dt.days

    # Failure risk label: high risk if SOH has dropped below a degradation
    # trajectory threshold consistent with the simulator's failure curve.
    df["high_risk_label"] = (df["soh_pct"] < 84.0).astype(int)

    return df


def train_soh_regressor(df):
    X = df[FEATURE_COLS]
    y = df["soh_pct"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = XGBRegressor(
        n_estimators=250,
        max_depth=5,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_lambda=1.0,
        random_state=42,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"[SOH Regressor]  MAE: {mae:.3f} pts   R²: {r2:.4f}")

    importances = dict(zip(FEATURE_COLS, model.feature_importances_.round(4).tolist()))
    print(f"[SOH Regressor]  Feature importances: {importances}")

    joblib.dump(model, os.path.join(ARTIFACT_DIR, "soh_regressor.joblib"))
    return model, {"mae": round(mae, 3), "r2": round(r2, 4), "feature_importances": importances}


def train_failure_classifier(df):
    X = df[FEATURE_COLS]
    y = df["high_risk_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    preds = model.predict(X_test)
    auc = roc_auc_score(y_test, proba) if len(set(y_test)) > 1 else float("nan")
    acc = accuracy_score(y_test, preds)
    print(f"[Failure Classifier]  Accuracy: {acc:.4f}   ROC-AUC: {auc:.4f}")
    print(f"[Failure Classifier]  Positive rate in test set: {y_test.mean():.4f}")

    joblib.dump(model, os.path.join(ARTIFACT_DIR, "failure_classifier.joblib"))
    return model, {"accuracy": round(acc, 4), "roc_auc": round(float(auc), 4) if auc == auc else None}


def main():
    print("Loading & engineering features...")
    df = build_training_frame()
    print(f"Training frame: {len(df)} rows, {df['vehicle_id'].nunique()} vehicles\n")

    print("Training SOH regressor...")
    _, soh_metrics = train_soh_regressor(df)

    print("\nTraining failure-risk classifier...")
    _, clf_metrics = train_failure_classifier(df)

    # Persist the feature column order + metrics so the API can load consistently
    meta = {
        "feature_cols": FEATURE_COLS,
        "soh_regressor_metrics": soh_metrics,
        "failure_classifier_metrics": clf_metrics,
        "trained_on_rows": len(df),
        "trained_on_vehicles": int(df["vehicle_id"].nunique()),
    }
    joblib.dump(meta, os.path.join(ARTIFACT_DIR, "model_meta.joblib"))

    print(f"\nArtifacts saved to {ARTIFACT_DIR}")
    print("  - soh_regressor.joblib")
    print("  - failure_classifier.joblib")
    print("  - model_meta.joblib")


if __name__ == "__main__":
    main()
