"""
页面7：可视化大屏
全维度数据看板 — 核心指标 + 图表一览
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.nav_style import inject_nav_css
from src.analysis import (
    compute_overview_metrics,
    compute_trend_analysis,
    compute_platform_comparison,
    compute_product_analysis,
)
from src.features import build_hourly_heatmap, build_rfm_features
from src.visualization import (
    revenue_trend_chart,
    hourly_heatmap_chart,
    platform_comparison_chart,
    product_ranking_chart,
    category_pie_chart,
    rfm_segment_bar,
)


st.set_page_config(page_title="可视化大屏 | 餐饮数据分析", page_icon="📺", layout="wide")


def main():
    inject_nav_css()
    st.title("📺 可视化大屏")

    df = st.session_state.get("df_orders")
    if df is None:
        st.warning("请先在「数据上传与分析报告」页面加载数据")
        return

    # ===== 第一行：核心KPI =====
    metrics = compute_overview_metrics(df)
    stats = metrics["revenue_stats"]

    st.subheader("核心经营指标")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("总营收", f"¥{metrics['total_revenue']:,.0f}")
    with col2:
        st.metric("总订单", f"{metrics['total_orders']:,}")
    with col3:
        st.metric("客单价", f"¥{metrics['avg_order_value']:.2f}")
    with col4:
        st.metric("退款率", f"{metrics['refund_rate']:.1f}%")
    with col5:
        st.metric("顾客数", f"{metrics.get('n_customers', 0):,}")
    with col6:
        dod = metrics["dod_change"]
        st.metric("日环比", f"{dod:+.1f}%")

    st.caption(
        f"统计五数 | 均值 ¥{stats['mean']:,.0f} | "
        f"中位数 ¥{stats['median']:,.0f} | "
        f"标准差 ¥{stats['std']:,.0f} | "
        f"偏度 {stats['skewness']} | 峰度 {stats['kurtosis']}"
    )
    st.divider()

    # ===== 第二行：营收趋势 + 时段热力图 =====
    st.subheader("营收趋势与时段分布")
    daily_df = compute_trend_analysis(df)

    col_left, col_right = st.columns([3, 2])
    with col_left:
        fig_trend = revenue_trend_chart(daily_df)
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_right:
        heatmap = build_hourly_heatmap(df)
        if not heatmap.empty:
            fig_heat = hourly_heatmap_chart(heatmap)
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("缺少小时数据")

    st.divider()

    # ===== 第三行：商品排行 + 品类占比 =====
    st.subheader("商品与品类分析")
    product_data = compute_product_analysis(df)
    ranking = product_data["product_ranking"]
    categories = product_data["category_breakdown"]

    col_left, col_right = st.columns(2)
    with col_left:
        fig_rank = product_ranking_chart(ranking, top_n=10)
        st.plotly_chart(fig_rank, use_container_width=True)
    with col_right:
        if not categories.empty:
            fig_pie = category_pie_chart(categories)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("缺少品类数据")

    st.divider()

    # ===== 第四行：用户分层 + 平台对比 =====
    st.subheader("用户与平台分析")
    rfm_df = build_rfm_features(df)
    platform_df = compute_platform_comparison(df)

    col_left, col_right = st.columns(2)
    with col_left:
        if not rfm_df.empty:
            fig_seg = rfm_segment_bar(rfm_df)
            st.plotly_chart(fig_seg, use_container_width=True)
        else:
            st.info("缺少用户数据")
    with col_right:
        if not platform_df.empty:
            fig_plat = platform_comparison_chart(platform_df)
            st.plotly_chart(fig_plat, use_container_width=True)
        else:
            st.info("缺少平台数据")

    st.divider()
    st.caption("数据科学与大数据技术 · 可视化大屏 · 自动刷新")


if __name__ == "__main__":
    main()
