from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_private"
MODEL_PATH = ROOT / "models" / "final_model.joblib"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"

SEED = 42

# Policy v4.1 numbers
RETURN_COST = 1150.0     # cost of one returned order (s4)
CALL_COST = 45.0         # one pre-dispatch confirmation call (s4)
CALL_PREVENTS = 0.35     # share of returns a call prevents (s7 pilot)
HOLD_CANCEL_RATE = 0.12  # held orders cancelled by customer (s7)

# Order value from the new payment gateway is stored 100x too high for Oct 2025
GATEWAY_FIX_START = "2025-10-01"
GATEWAY_FIX_END = "2025-11-01"

# Validation: train up to this date, validate on the last 3 months of train
VALID_START = "2026-04-01"

# Columns known before dispatch and used by the model
NUMERIC = [
    "discount_pct", "qty", "order_value_inr", "list_price_inr", "promised_delivery_days",
    "customer_prior_orders", "customer_prior_returns", "prior_return_rate",
    "warranty_months", "hour", "dayofweek", "is_gift", "shield", "pincode_missing",
]
CATEGORICAL = ["sales_channel", "payment_mode", "family", "state"]

# Dropped on purpose, see reports/decision_log.md
LEAKY = ["last_service_event_type", "pickup_scheduled_at", "returned"]
