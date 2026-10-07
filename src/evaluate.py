import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss, confusion_matrix,
                             f1_score, precision_recall_curve, precision_score, recall_score,
                             roc_auc_score, roc_curve)
from src import config as C


def metrics(y, p, thr: float) -> dict:
    pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "pr_auc": average_precision_score(y, p), "roc_auc": roc_auc_score(y, p),
        "brier": brier_score_loss(y, p), "accuracy": accuracy_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0), "recall": recall_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred, zero_division=0), "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
    }


def break_even_threshold() -> float:
    """A call is worth it when p * 35% * Rs1150 > Rs45."""
    return C.CALL_COST / (C.CALL_PREVENTS * C.RETURN_COST)


def cost_table(y, p, thresholds) -> pd.DataFrame:
    """Rupee view: call every order with score >= threshold."""
    y = np.asarray(y)
    base = y.sum() * C.RETURN_COST
    rows = []
    for t in thresholds:
        called = p >= t
        tp = int((called & (y == 1)).sum())
        calls = int(called.sum())
        prevented = tp * C.CALL_PREVENTS
        cost = calls * C.CALL_COST + (y.sum() - prevented) * C.RETURN_COST
        rows.append({"threshold": round(float(t), 3), "calls": calls, "tp": tp, "fp": calls - tp,
                     "fn": int(y.sum() - tp), "precision": tp / calls if calls else 0.0, "recall": tp / y.sum(),
                     "total_cost": cost, "saving_vs_no_action": base - cost})
    return pd.DataFrame(rows)


def make_plots(y, p, costs: pd.DataFrame, valid: pd.DataFrame, thr: float) -> None:
    C.FIGURES.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    pr, rc, _ = precision_recall_curve(y, p)
    ax[0].plot(rc, pr); ax[0].axhline(np.mean(y), ls="--", c="grey"); ax[0].set(xlabel="Recall", ylabel="Precision", title="Precision-recall")
    fpr, tpr, _ = roc_curve(y, p)
    ax[1].plot(fpr, tpr); ax[1].plot([0, 1], [0, 1], "--", c="grey"); ax[1].set(xlabel="False positive rate", ylabel="True positive rate", title="ROC")
    fig.tight_layout(); fig.savefig(C.FIGURES / "pr_roc.png", dpi=110); plt.close(fig)

    fig, ax = plt.subplots(figsize=(5, 4))
    fo, mp = calibration_curve(y, p, n_bins=8, strategy="quantile")
    ax.plot(mp, fo, "o-"); ax.plot([0, 1], [0, 1], "--", c="grey"); ax.set(xlabel="Predicted", ylabel="Observed", title="Calibration")
    fig.tight_layout(); fig.savefig(C.FIGURES / "calibration.png", dpi=110); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(costs["threshold"], costs["saving_vs_no_action"]); ax.axvline(thr, ls="--", c="red")
    ax.set(xlabel="Call threshold", ylabel="Saving vs no action (Rs, validation)", title="Threshold vs saving")
    fig.tight_layout(); fig.savefig(C.FIGURES / "threshold_saving.png", dpi=110); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    valid.groupby("family")["returned"].mean().sort_values().plot.barh(ax=ax)
    ax.set(xlabel="Return rate", title="Return rate by product family (validation)")
    fig.tight_layout(); fig.savefig(C.FIGURES / "family_return_rate.png", dpi=110); plt.close(fig)


def segment_table(df: pd.DataFrame, col: str, thr: float) -> pd.DataFrame:
    d = df.assign(flag=df["score"] >= thr)
    g = d.groupby(col, observed=True).apply(
        lambda x: pd.Series({"orders": len(x), "return_rate": x["returned"].mean(), "flagged": x["flag"].mean(),
                             "recall": x.loc[x["returned"] == 1, "flag"].mean() if x["returned"].sum() else np.nan,
                             "precision": x.loc[x["flag"], "returned"].mean() if x["flag"].sum() else np.nan}),
        include_groups=False)
    return g.round(3)
