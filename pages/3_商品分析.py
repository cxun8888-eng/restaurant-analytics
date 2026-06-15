"""
页面3：商品分析
销量排名、品类占比、关联规则挖掘（Apriori）
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.nav_style import inject_nav_css
from src.analysis import compute_product_analysis
from src.models import run_apriori
from src.visualization import (
    product_ranking_chart,
    category_pie_chart,
    association_chart,
)


st.set_page_config(page_title="商品分析 | 餐饮数据分析", page_icon="🍳", layout="wide")


def main():
    inject_nav_css()
    st.title("🍳 商品分析")

    df = st.session_state.get("df_orders")
    if df is None:
        st.warning("请先在「数据上传」页面加载数据")
        return

    # ===== 商品分析 =====
    product_data = compute_product_analysis(df)
    ranking = product_data["product_ranking"]
    categories = product_data["category_breakdown"]
    slow_movers = product_data["slow_movers"]

    # ===== 销量排行 =====
    col_t, col_b = st.columns([10, 1])
    with col_t:
        st.subheader("🔥 商品销量排行")
    with col_b:
        with st.popover("📖 解读"):
            st.markdown("""
            **怎么看这张图？**
            - **横条越长**，说明销量越高
            - **颜色越深**，说明销量越大（蓝色渐变）
            - 只看 Top N 就能快速识别爆款和滞销品
            - **用途**：决定菜单调整、备货优先级、促销选品
            """)

    top_n = st.slider("显示 Top N", 5, 30, 15, key="top_n_slider")
    fig_rank = product_ranking_chart(ranking, top_n=top_n)
    st.plotly_chart(fig_rank, use_container_width=True)

    # ===== 品类营收占比 =====
    col_t, col_b = st.columns([10, 1])
    with col_t:
        st.subheader("🥧 品类营收占比")
    with col_b:
        with st.popover("📖 解读"):
            st.markdown("""
            **怎么看这张图？**
            - **每个扇区**代表一个品类的营收占比
            - **扇区越大**，这个品类对营收的贡献越大
            - **右侧图例**显示了每个品类名称
            - **用途**：判断"靠什么赚钱"，指导菜单定价和品类扩张方向
            """)

    if not categories.empty:
        fig_pie = category_pie_chart(categories)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("数据中未包含品类(category)字段")

    st.divider()

    # ===== 关联规则挖掘 =====
    st.subheader("🔗 购物篮分析 — 关联规则挖掘（Apriori）")

    st.markdown("""
    > **算法原理**：扫描所有订单，找出「买了A的顾客往往也买了B」的模式。
    > - **支持度（Support）**：A+B 同时出现的订单占总订单的比例
    > - **置信度（Confidence）**：买了A的订单中，同时也买了B的比例
    > - **提升度（Lift）**：置信度 / P(B)，大于 1 表示正相关，越大关联越强
    """)

    with st.expander("⚙️ Apriori 参数设置", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            min_support = st.slider(
                "最小支持度", 0.005, 0.1, 0.01, 0.005,
                help="值越小，发现的规则越多",
            )
        with col2:
            min_lift = st.slider(
                "最小提升度", 0.5, 5.0, 1.0, 0.1,
                help="大于1表示正相关",
            )

    with st.spinner("正在运行 Apriori 算法..."):
        assoc_rules = run_apriori(df, min_support=min_support, min_lift=min_lift)

    st.session_state["assoc_rules"] = assoc_rules

    if not assoc_rules.empty:
        n_rules = len(assoc_rules)
        high_lift = (assoc_rules["lift"] >= 2).sum()
        st.success(f"发现 {n_rules} 条关联规则，其中 {high_lift} 条提升度 >= 2（强关联）")

        # 规则表
        st.caption("表：Apriori 关联规则明细")
        st.dataframe(
            assoc_rules.style.background_gradient(subset=["lift"], cmap="YlOrRd"),
            use_container_width=True,
            height=350,
            column_config={
                "support": st.column_config.NumberColumn("支持度", format="%.4f"),
                "confidence": st.column_config.NumberColumn("置信度", format="%.2f"),
                "lift": st.column_config.NumberColumn("提升度", format="%.2f"),
                "recommendation": "自动建议",
            },
        )

        # 气泡图
        col_t, col_b = st.columns([10, 1])
        with col_t:
            st.subheader("关联规则可视化")
        with col_b:
            with st.popover("📖 解读"):
                st.markdown("""
                **怎么看这张图？**
                - **每个气泡**代表一条关联规则（如"酸辣土豆丝 → 可乐"）
                - **横轴（支持度）**：越靠右，这个组合出现得越频繁
                - **纵轴（置信度）**：越靠上，买了A再买B的概率越高
                - **气泡大小**：代表提升度（Lift），越大说明关联越强
                - 关注**右上角的大气泡**，那是最佳套餐候选
                """)

        fig_assoc = association_chart(assoc_rules)
        st.plotly_chart(fig_assoc, use_container_width=True)
    else:
        st.info("未发现满足条件的关联规则。尝试降低最小支持度或最小提升度。")

    st.divider()

    # ===== 滞销品 =====
    st.subheader("📉 滞销品关注")
    st.caption("表：销量末尾 20% 的滞销商品")
    if not slow_movers.empty:
        cols = st.columns(len(slow_movers))
        for i, (_, row) in enumerate(slow_movers.iterrows()):
            with cols[i % len(cols)]:
                st.metric(
                    row["product_name"],
                    f"售 {int(row['total_sold'])} 份",
                    delta=f"¥{row['total_revenue']:,.0f}",
                )
    else:
        st.info("商品数量过少，无法划分滞销品")

    # ===== 面试要点 =====
    with st.expander("📝 Apriori 算法讲解要点", expanded=False):
        st.markdown("""
        ### 如何讲清楚这个模块？

        **1. 问题背景**
        > "在餐饮场景中，我们想知道哪些菜品经常被一起点。这个信息可以用来设计套餐、优化菜单排版、做交叉销售推荐。"

        **2. 为什么选 Apriori**
        > "Apriori 是购物篮分析的经典算法，核心思想是用先验性质剪枝——如果一个项集不频繁，它的超集也一定不频繁。这样不需要穷举所有组合。"

        **3. 核心指标解释**
        - **支持度(Support)** = P(A ∩ B)，衡量「普遍性」
        - **置信度(Confidence)** = P(B|A)，衡量「可靠性」
        - **提升度(Lift)** = P(B|A)/P(B)，衡量「相关性强度」，这才是关键指标

        **4. 业务价值**
        > "比如发现提升度=3.2 的搭配后，商家可以将其打包为套餐，定价略低于单点总价，既提高客单价又让顾客觉得划算。这是数据直接驱动收入增长的例子。"
        """)


if __name__ == "__main__":
    main()
