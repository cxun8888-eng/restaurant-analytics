"""
统计分析模块
负责：所有业务指标计算

面试亮点：
- 统计五数（均值、中位数、标准差、偏度、峰度）
- 同比增长算法
- 多维度切分聚合（平台、品类、时间）
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any


def compute_overview_metrics(df_orders: pd.DataFrame) -> Dict[str, Any]:
    """
    计算经营概览核心指标

    Returns
    -------
    Dict 包含:
        - total_revenue: 总营收
        - total_orders: 总订单数
        - avg_order_value: 客单价
        - refund_rate: 退款率
        - avg_discount_rate: 平均折扣率
        - today_revenue: 今日营收
        - today_orders: 今日订单
        - yesterday_revenue: 昨日营收
        - dod_change: 日环比(%)
    """
    if "date" not in df_orders.columns:
        df_orders["date"] = pd.to_datetime(df_orders["order_time"]).dt.strftime("%Y-%m-%d")

    # 按订单聚合（不去重商品行）
    order_level = df_orders.groupby("order_id").agg(
        date=("date", "first"),
        customer_id=("customer_id", "first"),
        platform=("platform", "first"),
        status=("status", "first"),
        total_amount=("total_amount", "sum"),
        actual_amount=("actual_amount", "sum"),
        discount=("discount", "sum"),
        refund_amount=("refund_amount", "sum"),
        item_count=("product_name", "count"),
    ).reset_index()

    unique_dates = sorted(order_level["date"].unique())
    total_revenue = order_level["actual_amount"].sum()
    total_orders = len(order_level)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    refund_rate = (order_level["status"] == "refunded").mean() * 100
    avg_discount_rate = (order_level["discount"].sum() / (order_level["total_amount"].sum() + 0.01)) * 100

    # 今日 vs 昨日
    today = order_level[order_level["date"] == unique_dates[-1]] if unique_dates else order_level
    today_revenue = today["actual_amount"].sum()
    today_orders = len(today)

    if len(unique_dates) >= 2:
        yesterday = order_level[order_level["date"] == unique_dates[-2]]
        yesterday_revenue = yesterday["actual_amount"].sum()
        dod_change = ((today_revenue - yesterday_revenue) / (yesterday_revenue + 0.01)) * 100
    else:
        yesterday_revenue = 0
        dod_change = 0

    # 统计五数（按日营收）
    daily_revenue = order_level.groupby("date")["actual_amount"].sum()
    revenue_stats = {
        "mean": round(daily_revenue.mean(), 2),
        "median": round(daily_revenue.median(), 2),
        "std": round(daily_revenue.std(), 2),
        "skewness": round(float(stats.skew(daily_revenue.dropna())), 2),
        "kurtosis": round(float(stats.kurtosis(daily_revenue.dropna())), 2),
    }

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "avg_order_value": round(avg_order_value, 2),
        "refund_rate": round(refund_rate, 2),
        "avg_discount_rate": round(avg_discount_rate, 2),
        "today_revenue": round(today_revenue, 2),
        "today_orders": today_orders,
        "yesterday_revenue": round(yesterday_revenue, 2),
        "dod_change": round(dod_change, 2),
        "revenue_stats": revenue_stats,
        "date_range": f"{unique_dates[0]} ~ {unique_dates[-1]}" if unique_dates else "N/A",
        "n_customers": order_level["customer_id"].nunique(),
    }


def compute_product_analysis(df_orders: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    产品分析：销量排名、单品贡献、品类占比

    Returns
    -------
    Dict:
        - product_ranking: 商品销量排行
        - category_breakdown: 品类占比
        - slow_movers: 滞销商品
    """
    # 按商品聚合
    product_stats = df_orders.groupby("product_name").agg(
        category=("category", "first"),
        total_sold=("quantity", "sum"),
        total_revenue=("actual_amount", "sum"),
        order_count=("order_id", "nunique"),
        avg_price=("unit_price", "mean"),
        refund_count=("status", lambda x: (x == "refunded").sum()),
    ).sort_values("total_sold", ascending=False).reset_index()

    total_orders = df_orders["order_id"].nunique()
    total_revenue = df_orders["actual_amount"].sum()

    product_stats["order_penetration"] = (product_stats["order_count"] / total_orders * 100).round(2)
    product_stats["revenue_share"] = (product_stats["total_revenue"] / total_revenue * 100).round(2)

    # 品类占比
    if "category" in df_orders.columns:
        category_stats = df_orders.groupby("category").agg(
            total_revenue=("actual_amount", "sum"),
            order_count=("order_id", "nunique"),
            product_count=("product_name", "nunique"),
        ).sort_values("total_revenue", ascending=False)
        category_stats["revenue_share"] = (category_stats["total_revenue"] / total_revenue * 100).round(2)
    else:
        category_stats = pd.DataFrame()

    # 滞销商品（销量在末尾 20%）
    bottom_n = max(1, int(len(product_stats) * 0.2))
    slow_movers = product_stats.tail(bottom_n)

    return {
        "product_ranking": product_stats,
        "category_breakdown": category_stats,
        "slow_movers": slow_movers,
    }


def compute_platform_comparison(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    跨平台对比分析
    """
    if "platform" not in df_orders.columns:
        return pd.DataFrame()

    platform_stats = df_orders.groupby("platform").agg(
        total_orders=("order_id", "nunique"),
        total_revenue=("actual_amount", "sum"),
        avg_order_value=("actual_amount", lambda x: x.groupby(df_orders.loc[x.index, "order_id"]).sum().mean()),
        refund_rate=("status", lambda x: (x == "refunded").mean() * 100),
        unique_customers=("customer_id", "nunique"),
    ).sort_values("total_revenue", ascending=False)

    platform_stats["revenue_share"] = (platform_stats["total_revenue"] / platform_stats["total_revenue"].sum() * 100).round(2)
    platform_stats["avg_order_value"] = platform_stats["avg_order_value"].round(2)
    platform_stats["refund_rate"] = platform_stats["refund_rate"].round(2)

    return platform_stats


def compute_trend_analysis(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    日营收趋势 + 环比
    """
    if "date" not in df_orders.columns:
        df_orders["date"] = pd.to_datetime(df_orders["order_time"]).dt.strftime("%Y-%m-%d")

    daily = df_orders.groupby("date").agg(
        revenue=("actual_amount", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
    ).reset_index()

    daily["prev_revenue"] = daily["revenue"].shift(1)
    daily["dod_pct"] = ((daily["revenue"] - daily["prev_revenue"]) / daily["prev_revenue"] * 100).round(2)
    daily["ma7"] = daily["revenue"].rolling(7, min_periods=1).mean()

    return daily
