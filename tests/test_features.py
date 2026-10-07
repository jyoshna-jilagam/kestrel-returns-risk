import pandas as pd
from src import config as C
from src.data import clean_orders
from src.features import FEATURES, build_features
from src import predict as P


def test_feature_columns_and_no_leaky_fields(order):
    feats = build_features(pd.DataFrame([order]), *P.load_lookup())
    assert list(feats.columns) == FEATURES
    for col in C.LEAKY:
        assert col not in feats.columns


def test_prior_return_rate_and_flags(order):
    feats = build_features(pd.DataFrame([order]), *P.load_lookup())
    assert feats.loc[0, "prior_return_rate"] == 0.5
    assert feats.loc[0, "pincode_missing"] == 1
    assert feats.loc[0, "shield"] == 1


def test_new_customer_rate_is_zero(order):
    order.update(customer_prior_orders=0, customer_prior_returns=0)
    assert build_features(pd.DataFrame([order]), *P.load_lookup()).loc[0, "prior_return_rate"] == 0.0


def test_clean_orders_dedups_and_fixes_gateway_values(order):
    a = {**order, "source": "crm", "order_placed_at": "2025-10-05 10:00", "order_value_inr": 450000.0}
    b = {**a, "source": "partner_feed"}
    c = {**order, "order_id": "T-2", "source": "crm", "order_placed_at": "2025-11-05 10:00"}
    out = clean_orders(pd.DataFrame([a, b, c]), True)
    assert len(out) == 2
    assert out.loc[out.order_id == "T-1", "order_value_inr"].iloc[0] == 4500.0
    assert out.loc[out.order_id == "T-2", "order_value_inr"].iloc[0] == 4500.0
