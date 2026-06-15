"""
页面4：用户分析
RFM 分层 + K-Means 聚类验证
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.nav_style import inject_nav_css
from src.features import build_rfm_features
from src.models import run_kmeans_clustering, find_optimal_k
from src.visualization import (
    rfm_scatter_3d,
    rfm_segment_bar,
    elbow_curve_chart,
)


st.set_page_config(page_title="用户分析 | 餐饮数据分析", page_icon="👤", layout="wide")


def main():
    inject_nav_css()
    st.title("👤 用户分析 — RFM 分层 + K-Means 聚类")

    df = st.session_state.get("df_orders")
    if df is None:
        st.warning("请先在「数据上传」页面加载数据")
        return

    with st.spinner("正在构建 RFM 特征..."):
        rfm_df = build_rfm_features(df)

    if rfm_df.empty:
        st.warning("数据缺少 customer_id 字段，无法进行用户分析")
        return

    st.session_state["rfm_df"] = rfm_df

    # ===== RFM 概览 =====
    st.subheader("📊 RFM 特征分布")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总用户数", f"{len(rfm_df):,}")
    with col2:
        st.metric("平均消费间隔", f"{rfm_df['recency'].mean():.0f} 天")
    with col3:
        st.metric("平均消费频次", f"{rfm_df['frequency'].mean():.1f} 次")
    with col4:
        st.metric("平均消费金额", f"¥{rfm_df['monetary'].mean():.0f}")

    # ===== 用户分层 =====
    st.divider()
    col_t, col_b = st.columns([10, 1])
    with col_t:
        st.subheader("👥 用户分层（RFM 规则分层）")
    with col_b:
        with st.popover("📖 解读"):
            st.markdown("""
            **怎么看这张图？**
            - **每一条**代表一种用户类型，按用户数从多到少排列
            - **横条越长**，这类用户数量越多，是主要的用户群体
            - **重点关注**："重要挽留"和"流失高价值"——人数不多但消费潜力大
            - **用途**：决定营销资源分配，优先召回高价值流失用户
            """)

    st.markdown("""
    > **分层逻辑**：对每个用户从 R（最近消费距今）、F（消费频次）、M（消费金额）三个维度打分（1-3），
    > 根据组合将用户分为 8 类，每类对应不同的运营策略。
    """)

    col_chart, col_table = st.columns([3, 2])

    with col_chart:
        fig_seg = rfm_segment_bar(rfm_df)
        st.plotly_chart(fig_seg, use_container_width=True)

    with col_table:
        seg_summary = rfm_df.groupby("segment").agg(
            用户数=("customer_id", "count"),
            平均消费间隔天=("recency", "mean"),
            平均消费频次=("frequency", "mean"),
            平均消费金额=("monetary", "mean"),
        ).round(1)
        st.caption("表：RFM 分层用户统计")
        st.dataframe(seg_summary, use_container_width=True)

    # ===== 策略展开 =====
    with st.expander("📋 每类用户运营策略", expanded=False):
        strategies = rfm_df[["segment", "strategy"]].drop_duplicates()
        for _, row in strategies.iterrows():
            st.markdown(f"**{row['segment']}** → {row['strategy']}")

    st.divider()

    # ===== K-Means 聚类 =====
    st.subheader("🤖 K-Means 聚类验证")

    st.markdown("""
    > **为什么做聚类？** RFM 规则分层是人工定义的（有主观性），用 K-Means 无监督聚类
    > 来交叉验证——如果两种方法的分组结果高度吻合，说明分层是合理的。
    """)

    # 肘部法则
    col_t, col_b = st.columns([10, 1])
    with col_t:
        st.subheader("📐 肘部法则 — 选择最优 K 值")
    with col_b:
        with st.popover("📖 解读"):
            st.markdown("""
            **怎么看这张图？**
            - **横轴**是不同的 K 值（聚类数），**纵轴**是 SSE（簇内误差平方和）
            - **曲线越陡**，增加 K 值带来的改善越大
            - **拐点（"肘部"）**所在位置就是最佳 K 值——之后再增加 K 收益递减
            - 上图中拐点约在 K=4 处，说明分成 4 类最合适
            """)

    elbow_df = find_optimal_k(rfm_df)
    fig_elbow = elbow_curve_chart(elbow_df)
    st.plotly_chart(fig_elbow, use_container_width=True)

    k = st.slider("选择聚类数 K", 2, 8, 4, key="k_slider")

    with st.spinner(f"正在执行 K-Means (k={k})..."):
        rfm_clustered, cluster_info = run_kmeans_clustering(rfm_df, n_clusters=k)

    st.subheader(f"聚类结果（K={k}）")
    st.caption(f"聚类误差平方和(SSE): {cluster_info['inertia']} | 越小表示聚类越紧凑")

    col1, col2 = st.columns(2)

    with col1:
        st.caption("表：K-Means 聚类中心与画像")
        st.dataframe(
            cluster_info["centers"],
            use_container_width=True,
            column_config={
                "recency": "平均消费间隔(天)",
                "frequency": "平均消费频次(次)",
                "monetary": "平均消费金额(¥)",
                "profile": "聚类画像",
                "count": "用户数",
            },
        )

    with col2:
        cross = pd.crosstab(
            rfm_clustered["segment"],
            rfm_clustered["cluster"],
            values=rfm_clustered["customer_id"],
            aggfunc="count",
        ).fillna(0)
        st.caption("表：RFM分层 × K-Means 交叉验证")
        st.dataframe(cross, use_container_width=True)

    # 3D 散点图
    col_t, col_b = st.columns([10, 1])
    with col_t:
        st.subheader("🎯 用户 3D 分布")
    with col_b:
        with st.popover("📖 解读"):
            st.markdown("""
            **怎么看这张图？**
            - **每个点**代表一个用户
            - **X轴（消费间隔）**：越靠前说明用户最近来过，越靠后说明很久没来了
            - **Y轴（消费频次）**：越靠右说明来得越勤
            - **Z轴（消费金额）**：越靠上说明花钱越多
            - **不同颜色**代表不同聚类分组
            - **右上角靠前的点** = 高频高消费的黄金客户
            - **用途**：直观看到用户分布，验证分层是否合理
            """)

    fig_3d = rfm_scatter_3d(rfm_clustered, color_col="cluster")
    st.plotly_chart(fig_3d, use_container_width=True)

    # ===== 讲解要点 =====
    with st.expander("📝 RFM + K-Means 算法讲解要点", expanded=False):
        st.markdown(f"""
        ### 如何讲清楚这个模块？

        **1. 什么是 RFM？**
        > "RFM 是 CRM 领域最经典的用户分层模型，诞生于 1990 年代，至今仍被 Amazon、美团等使用。它的核心洞察是：用户价值可以从三个维度刻画——最近一次消费时间、消费频率、消费金额。"

        **2. 特征工程**
        > "我构造了 R/F/M 三个特征，然后用分位数法各打 1-3 分。分位数比等距切割更好，因为它自动适应数据分布，不会被极端值影响。打分后手写 8 类分层规则。"

        **3. 为什么加 K-Means？**
        > "RFM 的规则分层是主观的——为什么是 3 等分？为什么这样组合？我用 K-Means 聚类来做交叉验证。先用肘部法则确定最优 K 值（看 inertia 曲线的拐点），然后聚类。如果交叉表显示两种方法的结果高度一致，就说明分层是客观可靠的。"

        **4. 业务落地**
        > "分层之后，每一类用户有对应的运营策略。比如「重要挽留」类客户（R低F高M高），说明他们曾经是忠实客户但很久没来了——这是最高优先级的召回对象。"

        **当前数据洞察：**
        - 用户总数：{len(rfm_df)}
        - 平均消费间隔：{rfm_df['recency'].mean():.0f} 天
        - 平均消费频次：{rfm_df['frequency'].mean():.1f} 次
        """)
        at_risk = rfm_df[rfm_df["segment"].isin(["重要挽留", "流失高价值"])]
        if len(at_risk) > 0:
            st.info(f"当前有 **{len(at_risk)} 位**高价值客户有流失风险，建议优先召回")


if __name__ == "__main__":
    main()
