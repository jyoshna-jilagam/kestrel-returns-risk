"""Train, validate on a later time period, choose a model, refit on all data, write predictions."""
import json
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import average_precision_score
from xgboost import XGBClassifier
from src import config as C
from src.data import clean_orders, load_raw, load_reference
from src.evaluate import break_even_threshold, cost_table, make_plots, metrics, segment_table
from src.features import FEATURES, build_features

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("train")


def make_pipeline(kind: str) -> Pipeline:
    cat = OneHotEncoder(handle_unknown="ignore")
    if kind == "logreg":
        pre = ColumnTransformer([("num", StandardScaler(), C.NUMERIC), ("cat", cat, C.CATEGORICAL)])
        model = LogisticRegression(max_iter=1000, C=1.0)
    elif kind == "dummy":
        pre = ColumnTransformer([("num", "passthrough", C.NUMERIC)])
        model = DummyClassifier(strategy="prior")
    else:
        pre = ColumnTransformer([("num", "passthrough", C.NUMERIC), ("cat", cat, C.CATEGORICAL)])
        spw = 4.0 if kind == "xgb_weighted" else 1.0
        model = XGBClassifier(n_estimators=250, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                              min_child_weight=5, scale_pos_weight=spw, random_state=C.SEED, n_jobs=2, eval_metric="logloss")
    return Pipeline([("pre", pre), ("model", model)])


def main() -> None:
    customers, products = load_reference()
    train = clean_orders(load_raw("train.csv"), True)
    test = clean_orders(load_raw("test_unlabelled.csv"), False)
    X = build_features(train, customers, products)
    y = train["returned"].to_numpy()
    is_valid = (train["order_placed_at"] >= C.VALID_START).to_numpy()
    log.info("train rows %d, valid rows %d, valid return rate %.3f", (~is_valid).sum(), is_valid.sum(), y[is_valid].mean())

    thr = break_even_threshold()
    results, scores = {}, {}
    for kind in ["dummy", "logreg", "xgb", "xgb_weighted"]:
        pipe = make_pipeline(kind).fit(X[~is_valid], y[~is_valid])
        p = pipe.predict_proba(X[is_valid])[:, 1]
        scores[kind] = p
        results[kind] = metrics(y[is_valid], p, 0.5)
        results[kind]["at_break_even"] = metrics(y[is_valid], p, thr)
        log.info("%-13s PR-AUC %.3f ROC-AUC %.3f Brier %.4f", kind, results[kind]["pr_auc"], results[kind]["roc_auc"], results[kind]["brier"])

    # xgb_weighted distorts probabilities, so only the unweighted models can be priced in rupees
    final_kind = max(["logreg", "xgb"], key=lambda k: results[k]["pr_auc"])
    log.info("final model: %s", final_kind)
    p_val = scores[final_kind]

    grid = np.round(np.arange(0.05, 0.91, 0.05), 2).tolist() + [round(thr, 3)]
    costs = cost_table(y[is_valid], p_val, sorted(set(grid)))
    best_thr = round(thr, 3)
    valid = train[is_valid].copy()
    valid["score"] = p_val
    valid = valid.merge(products[["sku", "family"]], on="sku", how="left")
    make_plots(y[is_valid], p_val, costs, valid, best_thr)

    # error analysis tables
    vf = valid.merge(customers[["customer_id", "shield_member", "state"]], on="customer_id", how="left")
    vf["value_band"] = pd.qcut(vf["order_value_inr"], 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
    vf["month"] = vf["order_placed_at"].dt.to_period("M").astype(str)
    vf["prior_bucket"] = vf["customer_prior_orders"].clip(upper=4).astype(str)
    segs = {c: segment_table(vf, c, best_thr) for c in ["family", "sales_channel", "payment_mode", "shield_member", "value_band", "month", "prior_bucket", "is_gift"]}

    # refit on all labelled data, calibration check on the validation fit is in the report
    final = make_pipeline(final_kind).fit(X, y)
    C.MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"pipeline": final, "features": FEATURES, "threshold": best_thr, "kind": final_kind}, C.MODEL_PATH)

    Xt = build_features(test, customers, products)
    test_scores = final.predict_proba(Xt)[:, 1]
    sub = pd.DataFrame({"order_id": test["order_id"], "score": test_scores})
    order = load_raw("sample_submission.csv")[["order_id"]]
    sub = order.merge(sub, on="order_id", how="left")
    sub.to_csv(C.ROOT / "predictions.csv", index=False)

    # drift: train vs test
    drift = {
        "test_share_flagged_at_threshold": float((test_scores >= best_thr).mean()),
        "valid_share_flagged": float((p_val >= best_thr).mean()),
        "mean_score_test": float(test_scores.mean()), "mean_score_valid": float(p_val.mean()),
        "test_prior_orders_mean": float(test["customer_prior_orders"].mean()),
        "train_prior_orders_mean": float(train["customer_prior_orders"].mean()),
        "test_cod_share": float((test["payment_mode"] == "cod").mean()), "train_cod_share": float((train["payment_mode"] == "cod").mean()),
        "test_pincode_default_share": float((test["delivery_pincode"] == 0).mean()), "train_pincode_default_share": float((train["delivery_pincode"] == 0).mean()),
    }
    rng = np.random.default_rng(C.SEED)
    yv = y[is_valid]
    boots = []
    for _ in range(500):
        idx = rng.integers(0, len(yv), len(yv))
        boots.append(average_precision_score(yv[idx], p_val[idx]))
    ci = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
    out = {"pr_auc_ci": ci, "mean_pred_valid": float(p_val.mean()), "valid_rate": float(yv.mean()),
           "final_kind": final_kind, "threshold": best_thr, "results": results, "valid_n": int(is_valid.sum()),
           "valid_pos": int(y[is_valid].sum()), "train_n": int((~is_valid).sum()), "total_train_rows": len(train),
           "costs": costs.round(3).to_dict("records"), "segments": {k: v.reset_index().to_dict("records") for k, v in segs.items()},
           "drift": drift, "test_rows": len(test)}
    C.REPORTS.mkdir(exist_ok=True)
    (C.REPORTS / "metrics.json").write_text(json.dumps(out, indent=2, default=str))
    log.info("saved model, predictions (%d rows), metrics", len(sub))


if __name__ == "__main__":
    main()
