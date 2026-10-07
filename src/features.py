import numpy as np
import pandas as pd
from src import config as C

FEATURES = C.NUMERIC + C.CATEGORICAL


def build_features(orders: pd.DataFrame, customers: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Join reference tables and derive features. Uses only pre-dispatch columns.

    customer_prior_orders / customer_prior_returns come from the export and are
    counts "before this order", so no extra history needs to be computed.
    """
    df = orders.merge(customers[["customer_id", "state", "shield_member"]], on="customer_id", how="left")
    df = df.merge(products[["sku", "family", "list_price_inr", "warranty_months"]], on="sku", how="left")
    ts = pd.to_datetime(df["order_placed_at"])
    df["hour"] = ts.dt.hour
    df["dayofweek"] = ts.dt.dayofweek
    df["is_gift"] = (df["is_gift"] == "Y").astype(int)
    df["shield"] = (df["shield_member"] == "Y").astype(int)
    df["pincode_missing"] = (df["delivery_pincode"].astype(str).str.lstrip("0") == "").astype(int)
    orders_n = df["customer_prior_orders"].replace(0, np.nan)
    df["prior_return_rate"] = (df["customer_prior_returns"] / orders_n).fillna(0.0)
    for col in C.CATEGORICAL:
        df[col] = df[col].fillna("unknown").astype(str)
    return df[FEATURES]
