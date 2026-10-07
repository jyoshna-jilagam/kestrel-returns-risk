# Screen recording script (3 minutes)

## Before recording
1. Start the API: `uvicorn app.api:app --port 8000`
2. Start the UI: `streamlit run app/ui.py`
3. Open three tabs: the UI (http://localhost:8501), the API docs (http://127.0.0.1:8000/docs), and the project in VS Code.
4. Keep `README.md`, `reports/validation_report.md` and `reports/decision_log.md` ready to show.

## Demo orders (values to type in the UI)
Common to all: order time `2026-07-15 11:00`, channel `app`, quantity 1, pincode 440001.

| Field | A: high risk | B: low risk | C: medium risk | D: new customer |
|---|---|---|---|---|
| Customer ID | KC100001 | KC100002 | KC100001 | KC100003 |
| SKU | KH-RV-01 | KH-CF-01 | KH-AF-02 | KH-WP-01 |
| Payment mode | cod | prepaid_upi | prepaid_card | cod |
| Discount % | 15 | 5 | 10 | 10 |
| Order value (Rs) | 14959 | 2659 | 5849 | 10799 |
| Promised delivery days | 6 | 3 | 6 | 6 |
| Gift | N | N | Y | N |
| Customer prior orders | 4 | 1 | 5 | 0 |
| Customer prior returns | 3 | 0 | 1 | 0 |
| Expected result | 90%, HIGH, call before dispatch | 1%, LOW, dispatch normally | 27%, MEDIUM, call before dispatch | 13%, MEDIUM, call before dispatch |

Error cases: customer ID `NOPE` gives "Unknown customer_id NOPE". Order value 0 gives a validation message. Stopping the API gives "prediction service is not reachable".

## 0:00 - 0:30 Problem and what was built
Screen: top of README.

"Kestrel wants to know, before dispatch, which orders will be returned. The client asked for 95 percent accuracy, but only about 11 percent of orders come back, so doing nothing is already 88.5 percent accurate. So I built a return-risk score for every order, priced it in rupees using the ops policy, and wrapped it in an API and a small screen for the operations team."

## 0:30 - 1:15 Data and approach
Screen: `reports/validation_report.md`, model comparison table.

"I cleaned the data first. I removed 651 repeated partner-feed rows and corrected October 2025 order values that were 100 times too high. I trained on April 2025 to March 2026 and tested on April to June 2026, because the real test set is a later period. I compared a no-skill baseline, logistic regression and XGBoost, and ranked them by precision-recall, not accuracy. Logistic regression won with a PR-AUC of 0.416, against 0.115 for no skill, and its probabilities are well calibrated."

## 1:15 - 1:45 What changed after early checks
Screen: `reports/decision_log.md`, leakage paragraph.

"Two columns, the pickup time and the latest service event, are only written after a return is approved or a reverse pickup happens. They look predictive but would not exist at dispatch, so I excluded them. The test data even contains a service value that never appears in training. I also set the call threshold from the policy: a call pays off when probability times 35 percent times Rs 1,150 beats Rs 45, which gives 11.2 percent."

## 1:45 - 2:15 What was discarded
Screen: `reports/validation_report.md`, business cost table.

"I discarded class-weighted XGBoost, because its probabilities were distorted and could not be priced in rupees. I also did not recommend holding orders, because the policy gives a 12 percent cancellation rate but no margin for a cancelled sale. So the recommendation is a confirmation call. At the threshold, on the validation quarter, 665 calls reach 168 of 245 returns and save about Rs 37,695. That is roughly Rs 12,400 a month at 700 orders, if calls prevent 35 percent of returns. Accuracy there is 73 percent, which I report openly."

## 2:15 - 2:50 Live demo
Screen: Streamlit UI. Type order A first.

"Here is the screen. This is a cash-on-delivery robot vacuum for a customer with three returns in four orders. [Click Predict.] 90 percent, high risk, call before dispatch, with reasons in plain language. Now a prepaid ceiling fan for a customer with no returns. [Enter B, click Predict.] 1 percent, dispatch normally. A first-time customer, order D, still gets a sensible score of 13 percent. [Enter D, click Predict.] An unknown customer ID [type NOPE, click Predict] gives a polite error. And here is the API health check and documentation page. [Switch to the docs tab.]"

## 2:50 - 3:00 Limitation and next step

"The biggest limit is that the 35 percent call effect comes from a small pilot, and I validated on one quarter. Next step is a four-week test of calls against no calls. Thank you."

## Delivery notes
- If you run over time, shorten the 1:15 - 1:45 section but keep the leakage point.
- Say "about Rs 12,400 a month, if calls prevent 35 percent of returns" in one sentence so the assumption stays attached to the number.
- Pre-fill order A before recording and change only the fields needed for B and D.
- Upload the video to Google Drive, share with anyone with the link, and paste the link into `submission-form.md`.
