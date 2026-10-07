import logging
import pandas as pd
from src import config as C

log = logging.getLogger("data")


def load_raw(name: str) -> pd.DataFrame:
    return pd.read_csv(C.DATA / name)


def load_reference() -> tuple[pd.DataFrame, pd.DataFrame]:
    customers = load_raw("customers.csv")
    products = load_raw("products.csv")
    return customers, products


def clean_orders(df: pd.DataFrame, is_train: bool) -> pd.DataFrame:
    """Parse dates, drop re-imported duplicates, fix Oct 2025 gateway values."""
    df = df.copy()
    df["order_placed_at"] = pd.to_datetime(df["order_placed_at"])
    before = len(df)
    # partner feed re-imports repeat an order that already exists in the CRM
    df = df.sort_values("source").drop_duplicates("order_id", keep="first")
    log.info("duplicate order rows removed: %d", before - len(df))
    in_window = (df["order_placed_at"] >= C.GATEWAY_FIX_START) & (df["order_placed_at"] < C.GATEWAY_FIX_END)
    df.loc[in_window, "order_value_inr"] = df.loc[in_window, "order_value_inr"] / 100
    log.info("order values rescaled /100: %d", in_window.sum())
    return df.sort_values("order_placed_at").reset_index(drop=True)
