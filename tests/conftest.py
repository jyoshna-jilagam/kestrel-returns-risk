import pandas as pd
import pytest
from src import predict as P


@pytest.fixture(autouse=True)
def synthetic_reference(monkeypatch):
    """Tests use made-up customers and products, never client data."""
    customers = pd.DataFrame({"customer_id": ["C1", "C2"], "city": ["A", "B"], "state": ["MH", "KA"],
                              "signup_date": ["2024-01-01", "2024-01-01"], "shield_member": ["Y", "N"]})
    products = pd.DataFrame({"sku": ["S1"], "family": ["Robot Vacuum"], "model_name": ["m"], "list_price_inr": [5000],
                             "warranty_months": [12], "launch_date": ["2023-01-01"]})
    P.load_lookup.cache_clear()
    monkeypatch.setattr(P, "load_lookup", lambda: (customers, products))


@pytest.fixture
def order():
    return {"order_id": "T-1", "order_placed_at": "2026-07-01 10:30", "customer_id": "C1", "sku": "S1",
            "sales_channel": "app", "payment_mode": "cod", "discount_pct": 10, "qty": 1, "order_value_inr": 4500,
            "promised_delivery_days": 5, "delivery_pincode": 0, "is_gift": "N",
            "customer_prior_orders": 4, "customer_prior_returns": 2}
