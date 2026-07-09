def test_qc_summary(client):
    r = client.get("/api/manufacturing/qc/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_inspections"] == 16
    assert "SUP-T02" in body["suppliers_flagged"]
    assert body["ml_high_risk_batches"] >= 1


def test_qc_model_performance_reports_real_metrics(client):
    r = client.get("/api/manufacturing/qc/model-performance")
    assert r.status_code == 200
    body = r.json()
    for key in ("precision", "recall", "f1_score", "accuracy"):
        assert 0.0 <= body[key] <= 1.0
    assert body["trained_on_rows"] > 0
    assert body["confusion_matrix"]["tp"] + body["confusion_matrix"]["fn"] > 0


def test_qc_drift_flags_the_injected_drift_batch(client):
    r = client.get("/api/manufacturing/qc/drift")
    assert r.status_code == 200
    alerts = r.json()
    assert len(alerts) > 0
    drifted_supplier_ids = {a["supplier_id"] for a in alerts}
    assert "SUP-T02" in drifted_supplier_ids
    assert all(a["severity"] in ("watch", "out_of_control") for a in alerts)


def test_qc_predict_flags_out_of_spec_batch_as_high_risk(client):
    r = client.post("/api/manufacturing/qc/predict", json={
        "weld_temp_c": 262.0, "torque_nm": 14.5, "cell_voltage_variance_mv": 19.0,
        "moisture_ppm": 195.0, "electrode_thickness_um": 74.0,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["risk_band"] == "high"
    assert body["defect_risk_probability"] > 0.5
    assert body["spc"]["moisture_ppm"]["out_of_control_3sigma"] is True


def test_qc_predict_scores_in_spec_batch_as_low_risk(client):
    r = client.post("/api/manufacturing/qc/predict", json={
        "weld_temp_c": 245.0, "torque_nm": 12.0, "cell_voltage_variance_mv": 8.0,
        "moisture_ppm": 120.0, "electrode_thickness_um": 68.0,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["risk_band"] == "low"


def test_qc_ingest_rejects_unknown_supplier(client):
    r = client.post("/api/manufacturing/qc/ingest", json=[{
        "supplier_id": "SUP-DOES-NOT-EXIST",
        "date": "2026-01-01",
        "defect_rate": 0.01,
    }])
    assert r.status_code == 400
