"""Turn logistic-regression contributions into short plain-English reasons."""
import numpy as np
import pandas as pd
from src import config as C
from src.predict import load_model


def _contributions(feats: pd.DataFrame) -> dict[str, float]:
    """Contribution of each original feature to the log-odds, relative to an average order."""
    pipe = load_model()["pipeline"]
    pre, clf = pipe.named_steps["pre"], pipe.named_steps["model"]
    names = pre.get_feature_names_out()
    x = pre.transform(feats)
    x = x.toarray() if hasattr(x, "toarray") else np.asarray(x)
    scaler = pre.named_transformers_["num"]
    mean_x = np.concatenate([(scaler.mean_ - scaler.mean_) / scaler.scale_, np.zeros(len(names) - len(C.NUMERIC))])
    contrib = (x[0] - mean_x) * clf.coef_[0]
    out: dict[str, float] = {}
    for n, c in zip(names, contrib):
        base = n.split("__", 1)[1]
        key = next((f for f in C.NUMERIC + C.CATEGORICAL if base == f or base.startswith(f + "_")), base)
        out[key] = out.get(key, 0.0) + float(c)
    return out


def _text(feature: str, row: pd.Series) -> str:
    v = row[feature]
    texts = {
        "prior_return_rate": lambda: f"Customer returned {v:.0%} of their previous orders.",
        "customer_prior_returns": lambda: f"Customer has {int(v)} earlier return(s).",
        "customer_prior_orders": lambda: f"Customer has {int(v)} earlier orders; repeat buyers returned more often in past data.",
        "payment_mode": lambda: f"Payment mode '{v}' has a higher return rate in past data.",
        "family": lambda: f"Product family '{v}' has a higher return rate in past data.",
        "shield": lambda: "Customer is a Shield member (free returns).",
        "order_value_inr": lambda: f"Order value of Rs {row['order_value_inr']:,.0f} is higher than average.",
        "discount_pct": lambda: f"Discount of {int(v)}% is higher than average.",
        "is_gift": lambda: "Order is marked as a gift.",
        "sales_channel": lambda: f"Channel '{v}' has a higher return rate in past data.",
        "state": lambda: f"Deliveries to state '{v}' returned more often in past data.",
        "promised_delivery_days": lambda: f"Promised delivery of {int(v)} days is longer than average.",
        "pincode_missing": lambda: "No delivery address was captured.",
        "qty": lambda: f"Order has {int(v)} units.",
    }
    return texts[feature]() if feature in texts else f"{feature} contributed to the score."


def top_reasons(feats: pd.DataFrame, n: int = 3) -> list[str]:
    row = feats.iloc[0]
    contrib = _contributions(feats)
    pushing_up = sorted([(k, c) for k, c in contrib.items() if c > 0.05], key=lambda kv: -kv[1])[:n]
    if not pushing_up:
        return ["Nothing in this order stands out; the score is close to the average order."]
    return [_text(k, row) + " (contributed to the model's score)" for k, _ in pushing_up]
