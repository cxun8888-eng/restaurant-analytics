from datetime import datetime

import pandas as pd

from backend.storage import Dataset, DatasetStore


def test_dataset_survives_store_recreation(tmp_path):
    dataset_id = "a" * 32
    expected = Dataset(
        frame=pd.DataFrame({"order_time": [pd.Timestamp("2026-08-26")], "amount": [19.9]}),
        quality={"clean_rows": 1},
        filename="orders.csv",
        created_at=datetime(2026, 8, 26),
    )

    DatasetStore(tmp_path).save(dataset_id, expected)
    restored = DatasetStore(tmp_path).get(dataset_id)

    assert restored is not None
    assert restored.filename == "orders.csv"
    assert restored.quality == {"clean_rows": 1}
    pd.testing.assert_frame_equal(restored.frame, expected.frame)


def test_dataset_store_rejects_invalid_id(tmp_path):
    store = DatasetStore(tmp_path)
    assert store.get("../../outside") is None
