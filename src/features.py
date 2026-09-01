"""
特征工程模块
负责：从订单明细构造分析特征

面试亮点：
- RFM 特征构造（CRM 领域最经典的用户分层模型）
- 时段特征工程
- 品类偏好特征
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional


def build_rfm_features(
    df_orders: pd.DataFrame,
    reference_date: Optional[datetime] = None,
) -> pd.DataFrame:
    """
    构建 RFM 特征

    Recency  (R): 当前日期 - 用户最后消费日期（越小=越近=越好）
    Frequency(F): 用户总订单数
    Monetary (M): 用户总消费金额

    Parameters
    ----------
    df_orders : pd.DataFrame
        清洗后的订单明细数据
    reference_date : datetime, optional
        参考日期（默认为数据中最后一天 + 1 天）

    Returns
    -------
    pd.DataFrame
        每个顾客一行，包含 R/F/M 原始值 + 评分（1-3）+ 分层标签
    """
    if reference_date is None:
        reference_date = df_orders["order_time"].max() + pd.Timedelta(days=1)

    # 按顾客聚合
    rfm = df_orders.groupby("customer_id").agg(
        recency=("order_time", lambda x: (reference_date - x.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("actual_amount", "sum"),
    ).reset_index()

    # -- 打分（按三分位数，1=差, 2=中, 3=好）--
    # 使用排名百分位而不是 qcut，避免小数据集或大量相同值导致分箱失败。
    def tertile_score(series: pd.Series, reverse: bool = False) -> pd.Series:
        ranks = series.rank(method="first", ascending=True, pct=True)
        scores = np.ceil(ranks * 3).clip(1, 3).astype(int)
        return (4 - scores) if reverse else scores

    # Recency 越小越好，所以分数反过来。
    rfm["R_score"] = tertile_score(rfm["recency"], reverse=True)
    rfm["F_score"] = tertile_score(rfm["frequency"])
    rfm["M_score"] = tertile_score(rfm["monetary"])

    # -- 总分 --
    rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

    # -- 分层标签 --
    def rfm_segment(row):
        r, f, m = row["R_score"], row["F_score"], row["M_score"]
        if r == 3 and f == 3 and m >= 2:
            return "重要价值"
        elif r == 3 and f >= 2 and m >= 2:
            return "潜力客户"
        elif r >= 2 and f <= 1 and m >= 2:
            return "重要保持"
        elif r == 3 and f <= 1 and m <= 1:
            return "新客户"
        elif r <= 1 and f >= 2 and m >= 2:
            return "重要挽留"
        elif r <= 1 and f >= 2 and m <= 1:
            return "一般价值"
        elif r <= 1 and f <= 1 and m >= 2:
            return "流失高价值"
        elif r <= 1 and f <= 1 and m <= 1:
            return "流失客户"
        else:
            return "普通客户"

    rfm["segment"] = rfm.apply(rfm_segment, axis=1)

    # -- 每类用户的经营策略 --
    STRATEGY_MAP = {
        "重要价值":   "维护VIP待遇，提供专属折扣和提前体验",
        "潜力客户":   "推荐高客单价新品，搭配满减活动刺激升级",
        "重要保持":   "定向发放回归优惠券，降低复购门槛",
        "新客户":     "引导二次消费，首单后3天内推送新客专享券",
        "重要挽留":   "大力度折扣+人工触达，挽回高价值客户优先",
        "一般价值":   "维持常规运营，低成本触达保持活跃度",
        "流失高价值": "重点挽回对象，电话/短信+大额优惠券组合",
        "流失客户":   "低成本触达（短信/模板消息），顺其自然",
        "普通客户":   "常规营销推送，提升消费频次",
    }
    rfm["strategy"] = rfm["segment"].map(STRATEGY_MAP)

    return rfm


def build_time_features(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    构造时间维度特征（用于聚类和预测模型）

    Returns
    -------
    pd.DataFrame
        按日期聚合的时间特征表
    """
    df = df_orders.copy()

    if "date" not in df.columns:
        df["date"] = pd.to_datetime(df["order_time"]).dt.strftime("%Y-%m-%d")

    daily = df.groupby("date").agg(
        total_revenue=("actual_amount", "sum"),
        total_orders=("order_id", "nunique"),
        avg_order_value=("actual_amount", lambda x: x.groupby(df.loc[x.index, "order_id"]).sum().mean()),
        total_customers=("customer_id", "nunique"),
        refund_rate=("status", lambda x: (x == "refunded").mean()),
        discount_rate=("discount", lambda x: x.sum() / (df.loc[x.index, "total_amount"].sum() + 0.01)),
    ).reset_index()

    # 时间衍生特征
    daily["date"] = pd.to_datetime(daily["date"])
    daily["weekday"] = daily["date"].dt.weekday
    daily["is_weekend"] = daily["weekday"].isin([5, 6]).astype(int)
    daily["month"] = daily["date"].dt.month
    daily["day_of_month"] = daily["date"].dt.day
    daily["week_of_year"] = daily["date"].dt.isocalendar().week.astype(int)

    # 7日移动平均
    daily["revenue_ma7"] = daily["total_revenue"].rolling(window=7, min_periods=1).mean()
    daily["orders_ma7"] = daily["total_orders"].rolling(window=7, min_periods=1).mean()

    return daily


def build_category_features(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    品类维度特征
    """
    if "category" not in df_orders.columns:
        return pd.DataFrame()

    cat_stats = df_orders.groupby("category").agg(
        total_sales=("actual_amount", "sum"),
        sales_pct=("actual_amount", lambda x: x.sum() / df_orders["actual_amount"].sum() * 100),
        total_orders=("order_id", "nunique"),
        avg_price=("unit_price", "mean"),
        avg_discount=("discount", "mean"),
    ).sort_values("total_sales", ascending=False).reset_index()

    cat_stats["sales_pct"] = cat_stats["sales_pct"].round(1)

    return cat_stats


def build_hourly_heatmap(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    构造时段热力图数据（工作日 × 小时 交叉表）
    """
    df = df_orders.copy()
    if "hour" not in df.columns:
        df["hour"] = pd.to_datetime(df["order_time"]).dt.hour
    if "weekday" not in df.columns:
        df["weekday"] = pd.to_datetime(df["order_time"]).dt.weekday

    # 按 日期+小时 聚合订单数（避免把同一个订单的不同行算多次）
    hourly = df.groupby(["date", "weekday", "hour"])["order_id"].nunique().reset_index()
    hourly.rename(columns={"order_id": "order_count"}, inplace=True)

    # 按工作日+小时 求平均
    heatmap = hourly.groupby(["weekday", "hour"])["order_count"].mean().unstack(fill_value=0)

    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    heatmap.index = [weekday_names[int(i)] for i in heatmap.index]

    return heatmap


def build_product_hourly_heatmap(df_orders: pd.DataFrame, top_n: int = 6) -> pd.DataFrame:
    """构造商品 × 时段热力图，返回热门商品每天的平均售出份数。"""
    if df_orders is None or df_orders.empty or "product_name" not in df_orders.columns:
        return pd.DataFrame()

    df = df_orders.copy()
    if "date" not in df.columns:
        df["date"] = pd.to_datetime(df["order_time"], errors="coerce").dt.strftime("%Y-%m-%d")
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    if "hour" not in df.columns:
        df["hour"] = pd.to_datetime(df["order_time"], errors="coerce").dt.hour

    df["product_name"] = df["product_name"].fillna("未命名商品").astype(str)
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
    df = df.dropna(subset=["date", "hour"])
    if df.empty:
        return pd.DataFrame()

    if "quantity" in df.columns:
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).clip(lower=0)
        top_products = df.groupby("product_name")["quantity"].sum().nlargest(top_n).index
        daily = df[df["product_name"].isin(top_products)].groupby(["product_name", "date", "hour"])["quantity"].sum().reset_index(name="units")
    else:
        top_products = df.groupby("product_name")["order_id"].nunique().nlargest(top_n).index
        daily = df[df["product_name"].isin(top_products)].groupby(["product_name", "date", "hour"])["order_id"].nunique().reset_index(name="units")

    if daily.empty:
        return pd.DataFrame()

    day_count = max(int(df["date"].nunique()), 1)
    heatmap = daily.groupby(["product_name", "hour"])["units"].sum().unstack(fill_value=0) / day_count
    heatmap = heatmap.sort_index(axis=1)
    heatmap.index.name = "product_name"
    return heatmap.round(2)


def build_product_time_analysis(df_orders: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    """返回商品 × 时段 × 工作日类型的销量、订单数与营收日均值。"""
    if df_orders is None or df_orders.empty or "product_name" not in df_orders.columns:
        return pd.DataFrame()
    df = df_orders.copy()
    timestamp = pd.to_datetime(df.get("order_time"), errors="coerce")
    df["date"] = timestamp.dt.strftime("%Y-%m-%d")
    df["hour"] = timestamp.dt.hour
    df["is_weekend"] = timestamp.dt.weekday.isin([5, 6])
    df["product_name"] = df["product_name"].fillna("未命名商品").astype(str)
    df["quantity"] = pd.to_numeric(df.get("quantity", 1), errors="coerce").fillna(1).clip(lower=0)
    df["actual_amount"] = pd.to_numeric(df.get("actual_amount", 0), errors="coerce").fillna(0).clip(lower=0)
    df = df.dropna(subset=["date", "hour"])
    if df.empty:
        return pd.DataFrame()

    top_products = df.groupby("product_name")["quantity"].sum().nlargest(top_n).index
    df = df[df["product_name"].isin(top_products)]
    output: list[pd.DataFrame] = []
    for period, mask in (
        ("全部", pd.Series(True, index=df.index)),
        ("工作日", ~df["is_weekend"]),
        ("周末", df["is_weekend"]),
    ):
        subset = df[mask]
        day_count = int(subset["date"].nunique())
        if subset.empty or day_count == 0:
            continue
        grouped = subset.groupby(["product_name", "hour"]).agg(
            quantity=("quantity", "sum"),
            orders=("order_id", "nunique"),
            revenue=("actual_amount", "sum"),
        ).reset_index()
        for metric in ("quantity", "orders", "revenue"):
            grouped[metric] = (grouped[metric] / day_count).round(2)
        grouped["period"] = period
        output.append(grouped)
    return pd.concat(output, ignore_index=True) if output else pd.DataFrame()


def build_segment_preferences(df_orders: pd.DataFrame, rfm: pd.DataFrame) -> pd.DataFrame:
    """把用户分层补充为店主能直接理解的消费时段与触达建议。"""
    if df_orders is None or df_orders.empty or rfm is None or rfm.empty:
        return pd.DataFrame()
    df = df_orders.copy().merge(rfm[["customer_id", "segment", "strategy"]], on="customer_id", how="inner")
    timestamp = pd.to_datetime(df.get("order_time"), errors="coerce")
    df["weekday"] = timestamp.dt.weekday
    df["hour"] = timestamp.dt.hour
    df["quantity"] = pd.to_numeric(df.get("quantity", 1), errors="coerce").fillna(1).clip(lower=0)
    df["actual_amount"] = pd.to_numeric(df.get("actual_amount", 0), errors="coerce").fillna(0).clip(lower=0)
    df = df.dropna(subset=["weekday", "hour"])
    if df.empty:
        return pd.DataFrame()

    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    previous_names = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]

    def period_label(hour: int) -> str:
        if 6 <= hour <= 10:
            return "早餐"
        if 11 <= hour <= 14:
            return "午餐"
        if 15 <= hour <= 17:
            return "下午"
        if 18 <= hour <= 21:
            return "晚餐"
        return "夜间"

    order_rows = df.drop_duplicates(["segment", "order_id"])
    output: list[dict] = []
    for segment, group in df.groupby("segment"):
        segment_orders = order_rows[order_rows["segment"] == segment]
        peak = segment_orders.groupby(["weekday", "hour"])["order_id"].nunique().sort_values(ascending=False)
        peak_weekday, peak_hour = peak.index[0] if not peak.empty else (0, 12)
        product = group.groupby("product_name")["quantity"].sum().sort_values(ascending=False)
        favorite_product = str(product.index[0]) if not product.empty else "常购商品"
        order_spend = group.groupby("order_id")["actual_amount"].sum()
        customer_count = int(group["customer_id"].nunique())
        visit_label = f"{weekday_names[int(peak_weekday)]}{period_label(int(peak_hour))}"
        contact_time = f"{previous_names[int(peak_weekday)]} 15:00"
        strategy = str(group["strategy"].dropna().iloc[0]) if group["strategy"].notna().any() else "提供与消费习惯匹配的优惠"
        output.append({
            "segment": segment,
            "customer_count": customer_count,
            "peak_visit": visit_label,
            "peak_hour": int(peak_hour),
            "favorite_product": favorite_product,
            "avg_order_value": round(float(order_spend.mean()) if not order_spend.empty else 0.0, 2),
            "contact_time": contact_time,
            "offer_strategy": strategy,
            "recommendation": f"{segment}主要在{visit_label}消费，建议{contact_time}推送{favorite_product}相关优惠。",
        })
    return pd.DataFrame(output).sort_values("customer_count", ascending=False).reset_index(drop=True)
