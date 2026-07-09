def test_fleet_overview(client):
    r = client.get("/api/fleet/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["total_vehicles"] == 2


def test_fleet_vehicle_detail(client):
    r = client.get("/api/fleet/vehicles/EVG-TEST-01")
    assert r.status_code == 200
    assert r.json()["vehicle_id"] == "EVG-TEST-01"


def test_fleet_vehicle_not_found(client):
    r = client.get("/api/fleet/vehicles/DOES-NOT-EXIST")
    assert r.status_code == 404


def test_battery_predict(client):
    r = client.get("/api/battery/predict/EVG-TEST-02")
    assert r.status_code == 200
    body = r.json()
    assert "failure_probability" in body
    assert 0.0 <= body["failure_probability"] <= 1.0


def test_battery_fleet_risk_summary(client):
    r = client.get("/api/battery/fleet-risk-summary")
    assert r.status_code == 200


def test_procurement_recommendations(client):
    r = client.get("/api/procurement/recommendations")
    assert r.status_code == 200
    recs = r.json()
    assert len(recs) == 2
    # the low-health, high-failure-probability test vehicle should be
    # flagged for replacement, not silently retained
    by_id = {x["vehicle_id"]: x for x in recs}
    assert by_id["EVG-TEST-02"]["recommendation"] == "replace"


def test_procurement_electrification_readiness(client):
    r = client.get("/api/procurement/electrification-readiness")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_readiness_validation_against_baseline(client):
    r = client.get("/api/procurement/readiness-validation")
    assert r.status_code == 200
    body = r.json()
    assert body["vehicles_scored"] == 2
    assert 0.0 <= body["band_agreement_pct"] <= 100.0
    assert len(body["rows"]) == 2


def test_carbon_summary(client):
    r = client.get("/api/carbon/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_co2_saved_kg"] >= 0


def test_supply_chain_suppliers(client):
    r = client.get("/api/supply-chain/suppliers")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_supply_chain_risk_summary(client):
    r = client.get("/api/supply-chain/risk-summary")
    assert r.status_code == 200
