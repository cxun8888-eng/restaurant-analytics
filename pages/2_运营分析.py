"""
页面2：运营分析
展示核心指标卡片、营收趋势、时段热力图、平台对比
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.nav_style import inject_nav_css
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


st.set_page_config(page_title="运营分析 | 餐饮数据分析", page_icon="📊", layout="wide")


# ===== 图表说明文案 =====
CHART_GUIDES = {
    "营收趋势": """
    **怎么看这张图？**

    - **蓝色实线**：每一天的实际营收金额
    - **黄色虚线**：7日移动平均线，平滑了每日波动，能更清晰地看到整体趋势方向
    - **下方柱状图**：每日环比变化百分比。绿色柱表示增长，红色柱表示下降
    - **小技巧**：如果蓝线波动大，看黄线来判断趋势；绿柱持续出现说明业绩在改善
    """,
    "时段热力图": """
    **怎么看这张图？**

    - **每一行**代表一周中的某一天（周一~周日），**每一列**代表一天中的某一个小时（0点~23点）
    - **颜色越深**，说明这个时段的平均订单数越多，生意越忙
    - **典型规律**：工作日的午餐（11-13点）和晚餐（17-20点）颜色最深，是两个高峰
    - **周末特点**：午餐高峰可能延后，晚餐时段拉长，下午时段也比工作日活跃
    - **用途**：帮助安排排班、备货时间，把钱和人力花在刀刃上
    """,
    "平台对比": """
    **怎么看这张图？**

    - **左侧饼图**：各平台（美团/微信/饿了么）贡献的营收占比，看哪个平台是主要收入来源
    - **右侧柱状图**：各平台的客单价对比，看哪个平台的顾客更愿意花钱
    - **表格数据**：还包含了退款率对比——退款率高的平台可能需要关注用户质量或活动类型
    - **用途**：指导在不同平台上的运营策略和活动预算分配
    """,
}


def main():
    inject_nav_css()
    st.title("📊 运营分析")

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
    col_title, col_btn = st.columns([10, 1])
    with col_title:
        st.subheader("📈 营收趋势")
    with col_btn:
        with st.popover("📖 解读"):
            st.markdown(CHART_GUIDES["营收趋势"])

    daily_df = compute_trend_analysis(df)
    fig_trend = revenue_trend_chart(daily_df)
    st.plotly_chart(fig_trend, use_container_width=True)

    # ===== 时段热力图 + 平台对比 =====
    col_left, col_right = st.columns(2)

    with col_left:
        col_t, col_b = st.columns([10, 1])
        with col_t:
            st.subheader("🕐 时段热力图")
        with col_b:
            with st.popover("📖 解读"):
                st.markdown(CHART_GUIDES["时段热力图"])

        heatmap = build_hourly_heatmap(df)
        if not heatmap.empty:
            fig_heat = hourly_heatmap_chart(heatmap)
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("数据缺少小时(hour)字段，无法生成时段热力图")

    with col_right:
        col_t, col_b = st.columns([10, 1])
        with col_t:
            st.subheader("📱 平台对比")
        with col_b:
            with st.popover("📖 解读"):
                st.markdown(CHART_GUIDES["平台对比"])

        platform_df = compute_platform_comparison(df)
        if not platform_df.empty:
            fig_plat = platform_comparison_chart(platform_df)
            st.plotly_chart(fig_plat, use_container_width=True)
            # 卡片式展示各平台指标
            for _, row in platform_df.iterrows():
                st.markdown(f"""
                <div style="
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 10px;
                    padding: 0.8rem 1rem;
                    margin: 0.4rem 0;
                ">
                    <span style="font-weight: 700; font-size: 1rem;">{row.name}</span>
                </div>
                """, unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("营收贡献", f"¥{row['total_revenue']:,.0f}", delta=f"占{row['revenue_share']:.1f}%")
                with c2:
                    st.metric("客单价", f"¥{row['avg_order_value']:.2f}")
                with c3:
                    st.metric("退款率", f"{row['refund_rate']:.1f}%")
                with c4:
                    st.metric("顾客数", f"{int(row['unique_customers'])}")
        else:
            st.info("未识别到平台字段，无法做平台对比")

    # ===== 数据解读 =====
    with st.expander("📝 数据解读", expanded=False):
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
