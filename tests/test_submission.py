import pandas as pd
import pytest
from src import config as C

pred_path = C.ROOT / "predictions.csv"
sample_path = C.DATA / "sample_submission.csv"
pytestmark = pytest.mark.skipif(not (pred_path.exists() and sample_path.exists()), reason="needs predictions and private sample file")


def test_schema_ids_and_scores():
    pred, sample = pd.read_csv(pred_path), pd.read_csv(sample_path)
    assert list(pred.columns) == list(sample.columns)
    assert len(pred) == len(sample)
    assert pred["order_id"].is_unique
    assert list(pred["order_id"]) == list(sample["order_id"])
    assert pred["score"].notna().all()
    assert pred["score"].between(0, 1).all()
