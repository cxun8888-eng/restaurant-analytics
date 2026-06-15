"""
页面1：数据上传 & 数据管道
展示数据质量报告、清洗前后对比、数据预览
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.nav_style import inject_nav_css
from src.data_pipeline import DataPipeline, load_sample_data, summarize_dataframe


st.set_page_config(page_title="数据上传与分析报告 | 餐饮数据分析", page_icon="📤", layout="wide")


def main():
    inject_nav_css()
    st.title("📤 数据上传 & 分析报告")
    st.markdown("支持美团、微信点单、饿了么等平台导出的 CSV/Excel 文件。系统将自动识别表头、清洗异常值、输出数据质量报告。")

    # ---- 数据来源选择 ----
    col_left, col_right = st.columns([2, 1])
    with col_left:
        data_source = st.radio(
            "选择数据来源",
            ["使用模拟数据（演示）", "上传我的数据"],
            index=0,
            horizontal=True,
        )
    with col_right:
        with st.expander("模拟数据说明"):
            st.caption("90天 × 日均约120单")
            st.caption("3个平台（美团/微信/饿了么）")
            st.caption("500位顾客、30+种商品")
            st.caption("内置关联购买规律和异常点")

    # ---- 根据选择加载数据 ----
    if data_source == "使用模拟数据（演示）":
        sample_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_orders.csv")

        if os.path.exists(sample_path):
            df = pd.read_csv(sample_path, parse_dates=["order_time"])
            st.success(f"✅ 已加载模拟数据：{len(df)} 行，{df['order_id'].nunique()} 笔订单")

            # 模拟质量报告
            quality_report = {
                "raw_rows": len(df),
                "clean_rows": len(df),
                "total_orders": df["order_id"].nunique(),
                "date_range": f"{df['date'].min()} ~ {df['date'].max()}",
                "issues": ["使用模拟数据，跳过数据校验（数据已预清洗）"],
                "anomalies": {},
                "duplicates_removed": 0,
            }
        else:
            st.error("模拟数据文件未找到，请先运行 `python sample_data/generate_mock_data.py`")
            return

    else:
        uploaded_file = st.file_uploader(
            "上传订单数据",
            type=["csv", "xlsx"],
            help="支持 CSV（UTF-8/GBK编码）或 Excel 文件",
        )

        if uploaded_file is None:
            st.info("👆 请上传文件，或切换到左侧的「使用模拟数据」体验系统")
            return

        # 执行数据管道
        with st.spinner("正在执行数据清洗与校验..."):
            pipeline = DataPipeline()
            df, quality_report = pipeline.run(uploaded_file.getvalue(), uploaded_file.name)

        st.success("✅ 数据管道执行完成！")

    # ---- 将数据存入 session_state ----
    st.session_state["df_orders"] = df

    # ---- 数据质量报告 ----
    st.header("📋 数据质量报告")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("原始行数", f"{quality_report.get('raw_rows', len(df)):,}")
    with col2:
        st.metric("清洗后行数", f"{quality_report.get('clean_rows', len(df)):,}")
    with col3:
        st.metric("订单总数", f"{quality_report.get('total_orders', df['order_id'].nunique()):,}")
    with col4:
        st.metric("日期范围", quality_report.get("date_range", "N/A"))

    # 问题清单
    issues = quality_report.get("issues", [])
    if issues:
        st.subheader("⚠️ 数据质量问题")
        for issue in issues:
            st.warning(issue)
    else:
        st.info("✅ 数据质量良好，未发现明显问题")

    # 异常检测结果
    anomalies = quality_report.get("anomalies", {})
    if anomalies.get("amount_outliers"):
        ao = anomalies["amount_outliers"]
        st.warning(
            f"🔍 检测到 **{ao['n_outliers']}** 笔异常金额订单 "
            f"（四分位距(IQR)法，正常范围：¥{ao['lower_bound']} ~ ¥{ao['upper_bound']}）"
        )

    # ---- 数据预览 ----
    st.header("📊 数据预览")

    tab1, tab2, tab3 = st.tabs(["数据样例", "统计摘要", "字段说明"])

    with tab1:
        st.caption("表：清洗后的订单数据样例（前50行）")
        st.dataframe(df.head(50), use_container_width=True, height=300)

    with tab2:
        st.caption("表：各字段统计摘要（数据类型、缺失值、唯一值）")
        st.dataframe(summarize_dataframe(df), use_container_width=True)

    with tab3:
        st.markdown("""
        | 字段 | 说明 | 示例 |
        |------|------|------|
        | order_id | 订单编号 | ORD00000001 |
        | order_time | 下单时间 | 2026-06-04 12:30:00 |
        | customer_id | 顾客ID | CUST00001 |
        | platform | 平台来源 | 美团外卖 / 微信小程序 / 饿了么 |
        | product_name | 商品名称 | 宫保鸡丁 |
        | category | 品类 | 热菜 / 凉菜 / 汤类 / 主食 / 饮品 / 小吃 |
        | quantity | 数量 | 1 |
        | unit_price | 单价 | 28.00 |
        | total_amount | 原价合计 | 28.00 |
        | discount | 优惠金额 | 2.00 |
        | actual_amount | 实付金额 | 26.00 |
        | status | 订单状态 | completed / refunded |
        """)


    # ===== 一键分析报告 =====
    st.divider()
    st.subheader("📋 一键生成经营诊断报告")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        gen_report = st.button("🔍 生成完整诊断报告", type="primary", use_container_width=True)
    with col_info:
        st.caption("基于当前加载的数据，自动运行用户分析、商品分析、异常检测、营收预测等全部模块，生成专业经营诊断报告。")

    if gen_report:
        from src.analysis import compute_overview_metrics, compute_product_analysis, compute_platform_comparison
        from src.features import build_rfm_features
        from src.models import run_apriori, run_isolation_forest
        from src.report import generate_full_report

        overview = compute_overview_metrics(df)
        product_data = compute_product_analysis(df)
        platform_df = compute_platform_comparison(df)
        rfm_df = build_rfm_features(df)
        assoc_rules = run_apriori(df)
        anomaly_df = run_isolation_forest(df)

        # 构造预测结果（简化版）
        from src.analysis import compute_trend_analysis
        daily_df = compute_trend_analysis(df)
        rev_col = "revenue"
        avg_val = daily_df[rev_col].tail(7).mean()
        forecast_simple = pd.DataFrame({
            "date": pd.date_range(pd.Timestamp.now(), periods=7).strftime("%Y-%m-%d").tolist(),
            "predicted": [round(avg_val, 2)] * 7,
            "lower_bound": [round(avg_val * 0.85, 2)] * 7,
            "upper_bound": [round(avg_val * 1.15, 2)] * 7,
        })

        with st.spinner("正在生成完整诊断报告..."):
            report = generate_full_report(
                overview=overview,
                product_analysis=product_data,
                rfm_df=rfm_df,
                assoc_rules=assoc_rules,
                forecast_result=forecast_simple,
                anomaly_orders=anomaly_df,
                platform_df=platform_df,
            )

        st.divider()
        st.markdown(report)

        # 下载按钮
        st.download_button(
            label="📥 下载报告（Markdown）",
            data=report,
            file_name=f"经营诊断报告_{overview.get('date_range', 'report')}.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
