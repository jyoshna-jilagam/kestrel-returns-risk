import logging
from functools import lru_cache
import joblib
import numpy as np
import pandas as pd
from src import config as C
from src.data import load_reference
from src.features import build_features

log = logging.getLogger("predict")
HIGH_CUTOFF = 0.30   # about 45% precision on the validation period


class ModelUnavailable(Exception):
    pass


class UnknownReference(Exception):
    pass


@lru_cache(maxsize=1)
def load_model() -> dict:
    if not C.MODEL_PATH.exists():
        raise ModelUnavailable("Model file not found. Run: python -m src.train")
    return joblib.load(C.MODEL_PATH)


@lru_cache(maxsize=1)
def load_lookup() -> tuple[pd.DataFrame, pd.DataFrame]:
    try:
        return load_reference()
    except FileNotFoundError as exc:
        raise ModelUnavailable("Reference files customers.csv and products.csv not found in data_private/") from exc


def check_references(order: dict) -> None:
    customers, products = load_lookup()
    if order["customer_id"] not in set(customers["customer_id"]):
        raise UnknownReference(f"Unknown customer_id {order['customer_id']}")
    if order["sku"] not in set(products["sku"]):
        raise UnknownReference(f"Unknown sku {order['sku']}")


def score_frame(orders: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    """Same feature code as training. Returns probabilities and the feature table."""
    customers, products = load_lookup()
    feats = build_features(orders, customers, products)
    return load_model()["pipeline"].predict_proba(feats)[:, 1], feats


def risk_level(p: float) -> str:
    thr = load_model()["threshold"]
    return "LOW" if p < thr else ("MEDIUM" if p < HIGH_CUTOFF else "HIGH")


def decision(p: float) -> str:
    return "CALL_BEFORE_DISPATCH" if p >= load_model()["threshold"] else "DISPATCH_NORMALLY"
