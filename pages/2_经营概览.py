"""
页面2：经营概览
展示核心指标卡片、营收趋势、时段热力图、平台对比
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.style import apply_global_style, page_title, section, quiet, spacer
from src.analysis import (
    compute_overview_metrics,
    compute_trend_analysis,
    compute_platform_comparison,
)
from src.features import build_hourly_heatmap
from src.visualization import (
    revenue_trend_chart,
    hourly_heatmap_chart,
    platform_comparison_chart,
)


st.set_page_config(page_title="经营概览 | 餐饮数据分析", page_icon="📊", layout="wide")


def main():
    apply_global_style()
    st.title("📊 经营概览")

    df = st.session_state.get("df_orders")
    if df is None:
        st.warning("请先在「数据上传」页面加载数据")
        return

    # ===== 核心指标卡片 =====
    metrics = compute_overview_metrics(df)
    stats = metrics["revenue_stats"]

    st.subheader("📌 核心指标")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "总营收",
            f"¥{metrics['total_revenue']:,.0f}",
            delta=f"日营收 ¥{metrics['today_revenue']:,.0f}",
        )
    with col2:
        st.metric(
            "总订单数",
            f"{metrics['total_orders']:,}",
            delta=f"今日 {metrics['today_orders']} 单",
        )
    with col3:
        st.metric(
            "客单价",
            f"¥{metrics['avg_order_value']:.2f}",
        )
    with col4:
        dod = metrics["dod_change"]
        st.metric(
            "日环比",
            f"{dod:+.1f}%",
            delta=f"退款率 {metrics['refund_rate']:.1f}%",
            delta_color="off",
        )

    # 统计五数
    st.caption(
        f"📐 统计五数 | 均值：¥{stats['mean']:,.0f} | "
        f"中位数：¥{stats['median']:,.0f} | "
        f"标准差：¥{stats['std']:,.0f} | "
        f"偏度：{stats['skewness']} | "
        f"峰度：{stats['kurtosis']}"
    )

    st.divider()

    # ===== 营收趋势图 =====
    st.subheader("📈 营收趋势")
    daily_df = compute_trend_analysis(df)
    fig_trend = revenue_trend_chart(daily_df)
    st.plotly_chart(fig_trend, use_container_width=True)

    # ===== 时段热力图 + 平台对比 =====
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🕐 时段热力图")
        heatmap = build_hourly_heatmap(df)
        if not heatmap.empty:
            fig_heat = hourly_heatmap_chart(heatmap)
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("数据缺少小时(hour)字段，无法生成时段热力图")

    with col_right:
        st.subheader("📱 平台对比")
        platform_df = compute_platform_comparison(df)
        if not platform_df.empty:
            fig_plat = platform_comparison_chart(platform_df)
            st.plotly_chart(fig_plat, use_container_width=True)
            st.dataframe(platform_df.style.format({
                "total_revenue": "¥{:,.0f}",
                "avg_order_value": "¥{:.2f}",
                "refund_rate": "{:.1f}%",
                "revenue_share": "{:.1f}%",
            }), use_container_width=True)
        else:
            st.info("未识别到平台字段，无法做平台对比")

    # ===== 数据解读 =====
    with st.expander("📝 数据解读（面试讲解要点）", expanded=False):
        st.markdown(f"""
        ### 如何解读这些数据？

        **1. 营收趋势**
        - 移动平均线平滑了日波动，能更清晰地看到趋势方向
        - 注意周末和工作日的营收差异（通常周末更高）
        - 环比的剧烈波动通常对应节假日或促销活动

        **2. 统计五数解读**
        - 偏度 `{stats['skewness']}`：{"正偏（右偏）→ 少数高营收日拉高了均值，中位数比均值更有参考价值" if stats['skewness'] > 0.5 else "分布较对称，均值和中位数接近" if abs(stats['skewness']) <= 0.5 else "负偏（左偏）→ 少数低营收日拉低了均值"}
        - 峰度 `{stats['kurtosis']}`：{"高峰度 → 营收分布更集中，波动较小" if stats['kurtosis'] > 0 else "低峰度 → 营收分布较分散，波动较大"}

        **3. 时段热力图**
        - 颜色越深代表订单越密集
        - 典型规律：工作日午餐（11-13点）和晚餐（17-20点）两个高峰
        - 周末午餐高峰可能延后，晚餐时段拉长

        **4. 平台对比**
        - 客单价差异反映了不同平台的用户画像差异
        - 退款率差异反映各平台的用户质量或活动类型差异
        """)


if __name__ == "__main__":
    main()
