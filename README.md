# Kestrel Home Returns Risk

A pre-dispatch model that scores each order for return risk, with an API and a small web UI for the operations team.

## Problem
Kestrel loses about Rs 1,150 on every returned order. Operations want to know before dispatch which orders are likely to come back.

## Business objective
Reduce the cost of returns without annoying customers. The client asked for "95% accuracy". About 11% of orders are returned, so a model that flags nothing is already 88.5% accurate. Accuracy is therefore reported but not used to choose the model. The model is ranked by PR-AUC and priced in rupees using the ops policy.

## Approach
1. Inspect and clean the data.
2. Remove columns that are only known after the return happens.
3. Train on the past, validate on a later quarter.
4. Compare a dummy baseline, logistic regression and XGBoost.
5. Turn the score into a decision using the policy costs.

## Data
Five files from the client, kept in `data_private/` (not in Git): `train.csv`, `test_unlabelled.csv`, `customers.csv`, `products.csv`, `sample_submission.csv`. Train has 11,155 rows (10,504 after removing duplicates), test has 2,096.

| Issue found | Rows | Action |
|---|---|---|
| Orders repeated by the partner-feed re-import | 651 | Keep the CRM copy, drop the repeat |
| Oct 2025 order values stored 100x too high (new payment gateway) | 700 after de-duplication | Divide by 100. Checked against list price x qty x (1 - discount) |
| Default pincode 000000 for walk-in orders | 889 train, 176 test | Kept, flagged with `pincode_missing` |
| Signup date after the order date | 2,105 train rows | `signup_date` not used |
| Instruction-like text inside `delivery_note` | 5 train rows | `delivery_note` not used, text ignored |

## Leakage prevention
- `pickup_scheduled_at`: written only after a return is approved. 92% of orders with a value are returned.
- `last_service_event_type`: REVERSE_PICKUP means returned (100%), DEMO_DONE and INSTALL_DONE mean never returned (0%). These happen after dispatch. Test also contains INSTALL_BOOKED, which never appears in train.
- `returned` is the target.
- `customer_prior_orders` and `customer_prior_returns` are counts "before this order" per the data pack, so they are safe to use as given.

## Feature engineering
Defined in `src/features.py`: discount, quantity, cleaned order value, list price, promised days, prior orders, prior returns, prior return rate, warranty, hour, weekday, gift flag, Shield flag, missing-pincode flag, channel, payment mode, product family and customer state.

## Validation
Train on Apr 2025 to Mar 2026, validate on Apr to Jun 2026. The hidden test is Jul to Sep 2026, so this mirrors the real use.

## Model
Logistic regression. It had the best PR-AUC, its probabilities are well calibrated, and it is easy to explain. XGBoost was tested and was not better.

## Results
Validation period, 2,126 orders, 245 returns.

| Model | PR-AUC | ROC-AUC | Brier |
|---|---|---|---|
| No-skill baseline | 0.115 | 0.500 | 0.102 |
| Logistic regression (final) | 0.416 | 0.788 | 0.085 |
| XGBoost | 0.398 | 0.771 | 0.086 |

PR-AUC 95% bootstrap interval for the final model: 0.359 to 0.476. At the 0.112 threshold: precision 0.253, recall 0.686, accuracy 0.730. **95% accuracy is not reachable with this data.** Full tables are in `reports/validation_report.md`.

## Business threshold
From policy v4.1: a call costs Rs 45, prevents 35% of returns, and a return costs Rs 1,150. A call is worth making when probability x 0.35 x 1,150 > 45, which gives a threshold of **0.112**. On the validation period this saves Rs 37,695 against doing nothing (665 calls). Holding orders is not recommended: 12% of held orders are cancelled and the cost of a lost sale is not in the data.

## Explainability
The API returns up to three plain-English reasons per order, taken from the largest positive contributions of the logistic regression. They are worded as "contributed to the model's score", not as causes.

## API
```
GET  /health
POST /predict
```
Example request (synthetic values):
```json
{"order_id": "DEMO-1", "order_placed_at": "2026-07-01 10:30", "customer_id": "KC100001",
 "sku": "KH-RH-01", "sales_channel": "app", "payment_mode": "cod", "discount_pct": 15, "qty": 1,
 "order_value_inr": 9000, "promised_delivery_days": 6, "delivery_pincode": 440001,
 "is_gift": "N", "customer_prior_orders": 4, "customer_prior_returns": 3}
```
Response: `order_id`, `return_probability`, `risk_level` (LOW, MEDIUM, HIGH), `decision` (CALL_BEFORE_DISPATCH or DISPATCH_NORMALLY) and `reasons`. Bad input returns a JSON `{"error": "..."}` with status 404, 422 or 503.

## Streamlit UI
Calls the API only. It holds no model logic.

## Installation
```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
Place the client CSV files in `data_private/` with these names: `train.csv`, `test_unlabelled.csv`, `customers.csv`, `products.csv`, `sample_submission.csv`.

## Running the project
```
python -m src.train        # trains, validates, saves model, writes predictions.csv
python -m src.report       # writes reports/validation_report.md
uvicorn app.api:app --port 8000
streamlit run app/ui.py    # in a second terminal
```
API docs open at http://127.0.0.1:8000/docs and the UI at http://localhost:8501. Set `API_URL` if the API runs elsewhere.

## Running tests
```
python -m pytest -q
```
Tests use made-up customers and products, so they run without client data.

## Generating predictions
`python -m src.train` writes `predictions.csv` with columns `order_id,score`, in the order of `sample_submission.csv`. Higher score means higher return risk.

## Project structure
```
app/        api.py, ui.py, explanation.py
src/        config.py, data.py, features.py, train.py, evaluate.py, predict.py, report.py
tests/      test_api.py, test_features.py, test_submission.py
models/     final_model.joblib
reports/    validation_report.md, decision_log.md, metrics.json, figures/
data_private/   client files, ignored by Git
```

## Limitations
- One 3-month validation window; the PR-AUC interval is wide.
- The 35% effect of a call comes from a spring pilot, not from this data.
- Shield status is read from the current customer file and may have changed after the order.
- Late returns may be missing from the most recent training orders.

## Privacy
Client data is in `data_private/` and ignored by Git. Only `predictions.csv` (order IDs and scores) is committed, so keep the repository private. No customer data appears in logs, tests or examples.

## AI disclosure
Claude was used to write and debug the code and documentation. See `submission-form.md`.
