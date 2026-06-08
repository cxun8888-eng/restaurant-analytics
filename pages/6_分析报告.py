"""
页面6：智能分析报告
一键生成完整经营诊断报告
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.style import apply_global_style
from src.analysis import compute_overview_metrics, compute_product_analysis, compute_platform_comparison
from src.report import generate_full_report


st.set_page_config(page_title="分析报告 | 餐饮数据分析", page_icon="📋", layout="wide")


def main():
    apply_global_style()
    st.title("📋 智能分析报告")

    df = st.session_state.get("df_orders")
    if df is None:
        st.warning("请先在「数据上传」页面加载数据")
        return

    # ===== 收集各模块数据 =====
    st.markdown("### 📊 报告数据汇总")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        overview = compute_overview_metrics(df)
        st.metric("总营收", f"¥{overview['total_revenue']:,.0f}")
    with col2:
        product_data = compute_product_analysis(df)
        st.metric("商品种类", len(product_data["product_ranking"]))
    with col3:
        rfm_df = st.session_state.get("rfm_df", pd.DataFrame())
        st.metric("用户分析", f"{len(rfm_df)} 位" if not rfm_df.empty else "未分析")
    with col4:
        anomaly_df = st.session_state.get("anomaly_df", pd.DataFrame())
        n_anom = anomaly_df["is_anomaly"].sum() if not anomaly_df.empty else 0
        st.metric("异常订单", n_anom)

    # ===== 生成报告 =====
    st.divider()

    if st.button("🔍 一键生成完整诊断报告", type="primary", use_container_width=True):
        with st.spinner("正在生成报告..."):
            assoc_rules = st.session_state.get("assoc_rules", pd.DataFrame())
            forecast_result = st.session_state.get("forecast_result", pd.DataFrame())
            platform_df = compute_platform_comparison(df)

            report = generate_full_report(
                overview=overview,
                product_analysis=product_data,
                rfm_df=rfm_df,
                assoc_rules=assoc_rules,
                forecast_result=forecast_result,
                anomaly_orders=anomaly_df,
                platform_df=platform_df,
            )

        st.markdown(report)

        # 下载报告
        st.download_button(
            label="📥 下载报告（Markdown）",
            data=report,
            file_name=f"经营分析报告_{overview.get('date_range', 'report')}.md",
            mime="text/markdown",
        )

    else:
        st.info("👆 点击上方按钮生成完整报告。确保已浏览「商品分析」「用户分析」「智能预测」页面以获取完整数据。")

    # ===== 报告结构说明 =====
    with st.expander("📝 报告结构说明", expanded=False):
        st.markdown("""
        ### 报告包含以下部分：

        1. **经营概览** — 核心指标总览 + 统计特征解读
        2. **异常提醒** — 自动检测的经营异常项
        3. **商品分析** — 畅销/滞销品 + 搭配建议
        4. **用户洞察** — 用户分层分布 + 风险人群
        5. **预测展望** — 未来营收预测 + 趋势判断
        6. **经营建议** — 从数据中自动提取的可执行改进建议

        ### 简历亮点：
        > "我实现了从原始数据到经营建议的完整分析闭环。最后一键生成的分析报告不是简单的数值罗列，
        > 而是数据驱动的自然语言诊断——这体现了数据分析的最终价值：将数据转化为决策。"
        """)


if __name__ == "__main__":
    main()
