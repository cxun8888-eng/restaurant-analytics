import io

import pandas as pd

from src.data_pipeline import DataPipeline
from src.analysis import compute_overview_metrics
from src.features import build_product_time_analysis, build_rfm_features, build_segment_preferences
from src.models import run_isolation_forest


def minimal_orders() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"order_id": "O1", "order_time": "2026-08-01 12:00:00", "product_name": "米饭", "total_amount": 3},
            {"order_id": "O2", "order_time": "2026-08-02 18:00:00", "product_name": "鱼香肉丝", "total_amount": 26},
        ]
    )


def test_pipeline_fills_optional_columns_and_quality_summary():
    frame, quality = DataPipeline().run(
        minimal_orders().to_csv(index=False).encode("utf-8"), "orders.csv"
    )
    assert {"actual_amount", "discount", "refund_amount", "category", "unit_price"}.issubset(frame.columns)
    assert quality["total_orders"] == 2
    assert quality["date_range"] == "2026-08-01 ~ 2026-08-02"


def test_rfm_and_anomaly_detection_work_with_tiny_dataset():
    frame, _ = DataPipeline().run(minimal_orders().to_csv(index=False).encode("utf-8"), "orders.csv")
    rfm = build_rfm_features(frame)
    anomalies = run_isolation_forest(frame)
    assert len(rfm) == 2
    assert {"R_score", "F_score", "M_score", "segment"}.issubset(rfm.columns)
    assert len(anomalies) == 2
    assert {"anomaly_types", "anomaly_reason", "severity"}.issubset(anomalies.columns)


def test_product_time_and_segment_preferences_are_business_readable():
    frame, _ = DataPipeline().run(minimal_orders().to_csv(index=False).encode("utf-8"), "orders.csv")
    rfm = build_rfm_features(frame)
    product_time = build_product_time_analysis(frame)
    preferences = build_segment_preferences(frame, rfm)

    assert {"product_name", "period", "hour", "quantity", "orders", "revenue"}.issubset(product_time.columns)
    assert {"segment", "peak_visit", "favorite_product", "contact_time", "recommendation"}.issubset(preferences.columns)


def test_pipeline_handles_mixed_dates_and_overview_does_not_crash():
    # 典型平台导出表：日期格式混用，并且存在空日期。
    raw = pd.DataFrame(
        [
            {"订单编号": "A-1", "交易日期": "07-03-2022", "商品": "汉堡", "营业额": "20"},
            {"订单编号": "A-2", "交易日期": "8/23/2022", "商品": "可乐", "营业额": "8"},
            {"订单编号": "A-3", "交易日期": None, "商品": "薯条", "营业额": "12"},
        ]
    )
    frame, quality = DataPipeline().run(raw.to_csv(index=False).encode("utf-8"), "orders.csv")

    assert frame["date"].notna().all()
    assert frame["date"].map(type).eq(str).all()
    assert any("日期无法识别" in issue for issue in quality["issues"])
    metrics = compute_overview_metrics(frame)
    assert metrics["total_orders"] == 3


def test_overview_handles_single_day_nullable_amounts():
    # Nullable pandas numeric columns return pd.NA for std() with one value.
    # A one-day report is valid and must still produce JSON-safe statistics.
    raw = pd.DataFrame(
        [
            {"order_id": "A-1", "order_time": "2026-08-28", "product_name": "汉堡", "total_amount": 20},
            {"order_id": "A-2", "order_time": "2026-08-28", "product_name": "可乐", "total_amount": 8},
        ]
    )
    frame, _ = DataPipeline().run(raw.to_csv(index=False).encode("utf-8"), "orders.csv")

    metrics = compute_overview_metrics(frame)

    assert metrics["revenue_stats"]["std"] == 0.0
    assert metrics["revenue_stats"]["skewness"] == 0.0
    assert metrics["revenue_stats"]["kurtosis"] == 0.0


def test_pipeline_preserves_meaningful_auxiliary_report_fields():
    raw = pd.DataFrame(
        [
            {
                "order_id": "A-1", "customer_id": "C-1", "restaurant_name": "Cafe A",
                "cuisine_type": "Japanese", "cost_of_the_order": "20.5",
                "day_of_the_week": "Weekend", "rating": "5",
                "food_preparation_time": 18, "delivery_time": 26,
            }
        ]
    )
    frame, quality = DataPipeline().run(raw.to_csv(index=False).encode("utf-8"), "foodhub.csv")

    assert frame.loc[0, "total_amount"] == 20.5
    assert frame.loc[0, "category"] == "Japanese"
    assert frame.loc[0, "restaurant_name"] == "Cafe A"
    assert frame.loc[0, "weekday_label"] == "Weekend"
    assert frame.loc[0, "rating"] == 5
    assert frame.loc[0, "preparation_time"] == 18
    assert frame.loc[0, "delivery_duration"] == 26
    assert any(item["source"] == "cost_of_the_order" and item["field"] == "total_amount" for item in quality["column_mapping"])
    assert not any(item["source"] == "restaurant_name" and item["field"] == "product_name" for item in quality["column_mapping"])
