from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_predict_ok(order):
    r = client.post("/predict", json=order)
    body = r.json()
    assert r.status_code == 200
    assert 0 <= body["return_probability"] <= 1
    assert body["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert body["decision"] in {"CALL_BEFORE_DISPATCH", "DISPATCH_NORMALLY"}
    assert isinstance(body["reasons"], list) and body["reasons"]
    assert body["order_id"] == "T-1"


def test_missing_field(order):
    del order["sku"]
    r = client.post("/predict", json=order)
    assert r.status_code == 422 and "sku" in r.json()["error"]


def test_invalid_number(order):
    order["order_value_inr"] = -10
    assert client.post("/predict", json=order).status_code == 422


def test_unexpected_category(order):
    order["payment_mode"] = "barter"
    assert client.post("/predict", json=order).status_code == 422


def test_unknown_customer_and_sku(order):
    assert client.post("/predict", json={**order, "customer_id": "ZZZ"}).status_code == 404
    assert client.post("/predict", json={**order, "sku": "ZZZ"}).status_code == 404


def test_malformed_json():
    r = client.post("/predict", content="{bad", headers={"content-type": "application/json"})
    assert r.status_code == 422 and "error" in r.json()


def test_returns_above_orders(order):
    order["customer_prior_returns"] = 9
    assert client.post("/predict", json=order).status_code == 422
