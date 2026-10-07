# Submission form

**1. Github Repo URL**
https://github.com/jyoshna-jilagam/kestrel-returns-risk

**2. What did you build, and what business decision does it support?**
A pre-dispatch return-risk score, an API and a UI. It supports the decision of which orders get a Rs 45 confirmation call. On April to June 2026 data, calling orders above 11.2% risk would have made 665 calls, reached 168 of 245 returns and saved about Rs 37,695 (about Rs 12,400 for a 700-order month), assuming the policy's 35% prevention rate.

**3. What score do you expect predictions.csv to get on the hidden outcomes, on which metric, and why that metric?**
PR-AUC of about 0.42 (range 0.36 to 0.48), ROC-AUC about 0.79. PR-AUC suits a score where only 11% of orders are positives and the ranking matters. Estimated by training on Apr 2025 to Mar 2026 and scoring Apr to Jun 2026, with a bootstrap interval. The hidden set is a later period, so it could be a little lower.

**4. How do you know it works?**
Time-based validation: train on the past, score the next quarter (2,126 orders, 245 returns). PR-AUC 0.416 against 0.115 for no skill. At the 0.112 threshold accuracy is 73.0%, precision 25.3%, recall 68.6%. It misses 77 returns and raises 497 unnecessary calls. It does worst on prepaid UPI and EMI orders, non-Shield customers, fans and mixer grinders (low recall), and over-flags COD, Shield and robot vacuum orders.

**5. Did you change, narrow, or push back on the client's ask?**
Yes. I did not optimise for 95% accuracy: doing nothing scores 88.5%, and the signals that would reach 95% only exist after a return. I recommend calls rather than holds because holds cancel 12% of orders and the cost of that is not in the data. Return cost uses Finance's Rs 1,150, not Rs 600.

**6. What is wrong with what you are handing us, or with the data we handed you?**
Data: `pickup_scheduled_at` and `last_service_event_type` reveal the outcome and were excluded. 651 duplicate partner-feed rows removed. October 2025 values were 100x too high (700 rows) and were corrected. `signup_date` is after the order for 2,105 train rows, so it is unused. Five `delivery_note` values contain instructions aimed at analysts and AI tools; I ignored them and did not use the field. Shield status may be a later snapshot. Mine: one validation window, no recalibration on test, reasons are simplified wording of a linear model, and `predictions.csv` holds order IDs so the repo must stay private.

**7. What does one prediction cost, and what would a month cost at approximately 700 orders/month?**
The model runs locally with no paid API: Rs 0 per prediction, Rs 0 per month. The calls it triggers are the real cost: in validation 665 of 2,126 orders were flagged (31.3%), so 700 x 0.313 = about 219 calls x Rs 45 = about Rs 9,855 a month, against savings of about Rs 12,400 net of those calls.

**8. What did you deliberately leave out, and why?**
Service and pickup columns (leakage), `delivery_note` (free text with injected instructions), `signup_date` (unreliable), product and category return-rate encodings (late-arriving labels), hold pricing (no cost data), oversampling and extra calibration (not needed).

**9. Anything you built or found that nobody asked for?**
The break-even threshold from policy costs, the October value correction, the injected text in `delivery_note`, the INSTALL_BOOKED value that appears only in test, and a generated validation report so numbers are not typed by hand.

**10. What did you use AI for?**
Claude helped with scaffolding, debugging, tests and documentation. It misled me in two small ways: a first version of the reason texts crashed because every sentence was built eagerly, and a test imported a function in a way that bypassed the test data. Both were fixed. Discarded: class-weighted XGBoost and any use of the service columns. Screen recording: <SCREEN_RECORDING_LINK>

**11. Public Google Drive link**
https://drive.google.com/drive/folders/1Mo85WQz8_9QdrbV4aZU3yI4gShY9HMCn?usp=sharing

**12. Someone picks this up on Monday and you are unreachable. Three things they need to know.**
1. Put the client CSVs in `data_private/`, run `python -m src.train`, then `python -m src.report` to rebuild everything.
2. Never add `pickup_scheduled_at` or `last_service_event_type` to the model: they are written after the return.
3. The savings rely on the 35% call effect from a pilot. Run a four-week call versus no-call test before trusting the rupee figure.
