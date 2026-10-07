# Decision log

**Validation split.** Train Apr 2025 to Mar 2026, validate Apr to Jun 2026. Test is Jul to Sep 2026, so a later quarter is the honest simulation. A random split would mix months and flatter the score. The final model is refit on all labelled orders.

**Leakage.** `pickup_scheduled_at` is written when a return is approved (policy s7). `last_service_event_type` includes REVERSE_PICKUP (100% returned) and DEMO_DONE or INSTALL_DONE (0% returned), which are post-dispatch events. Both are pulled "as of export day" per the IT email, so they are not what the warehouse sees at dispatch. Both dropped. Test has INSTALL_BOOKED, unseen in train.

**Why not compute history features.** The export already gives `customer_prior_orders` and `customer_prior_returns` as counts before each order. Product and category return-rate encodings were skipped: returns arrive up to 30 days late, so a naive version would leak, and `family` as a category captures most of it.

**Cleaning.** 651 duplicate partner-feed rows removed (identical except `source`). October 2025 order values divided by 100 (700 rows after de-duplication; ratio to list price x qty x discount was exactly 100 for every row in that month, 1 elsewhere). Default pincode kept as a flag.

**Columns not trusted.** `signup_date` (after order date for 2,105 train rows), `delivery_note` (free text; 5 train rows contain instructions aimed at analysts and AI tools, ignored), `shield_member` (current snapshot, possibly after the order; kept but flagged).

**Model.** Logistic regression, PR-AUC 0.416 against XGBoost 0.398 and class-weighted XGBoost 0.396. The simpler model won, is calibrated (Brier 0.085 against 0.102 for no-skill) and is explainable. No SMOTE, no extra calibration.

**Threshold.** 0.112 = 45 / (0.35 x 1150), from policy. Saving is flat between 0.10 and 0.15.

**Call, not hold.** Holds cancel 12% of the time and the lost margin per cancellation is not given, so a hold cannot be priced. A call costs Rs 45 and has a pilot-based effect. Shield members are 57.7% flagged in validation, so calls are suggested for them rather than holds.

**Discarded.** Using the service and pickup columns (accuracy near perfect, useless in practice); class-weighted XGBoost (bad probabilities); SHAP (not needed for a linear model); oversampling.

**Remaining limits.** One validation window; 35% call effect from a pilot; Shield timing; late-arriving return labels.
