"""
餐饮多平台经营数据分析系统
"""

import streamlit as st
from src.nav_style import inject_nav_css

st.set_page_config(
    page_title="首页",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    inject_nav_css()

    # ===== 侧边栏 — 仅导航 =====
    with st.sidebar:
        pass  # 什么都不要，只保留 Streamlit 自动生成的导航

    # ===== 主页内容 =====
    st.title("🍜 餐饮多平台经营数据分析系统")

    st.markdown("""
    ### 从数据到决策：餐饮经营分析一站式平台
    商家从美团、微信小程序、饿了么导出订单数据 → 上传文件 → 自动完成：
    数据清洗 → 特征建模 → 多维分析 → 可视化图表 → **智能经营建议**
    """)

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 🔬 数据科学方法论
        - **RFM 用户分层**（CRM经典模型）
        - **Apriori 关联规则**（购物篮分析）
        - **K-Means 聚类**（交叉验证）
        - **随机森林回归**（时序预测）
        - **Isolation Forest**（异常检测）
        """)
    with col2:
        st.markdown("""
        ### 📊 全链路数据处理
        - 多平台数据自动识别
        - IQR 异常值检测
        - 缺失值智能处理
        - 特征工程（RFM/时段/品类）
        - 数据质量报告
        """)
    with col3:
        st.markdown("""
        ### 💡 数据驱动决策
        - 自动生成经营诊断报告
        - 套餐搭配智能建议
        - 用户分层运营策略
        - 滞销品优化建议
        - 未来营收预测预警
        """)

    st.divider()
    st.markdown("""
    ### 🚀 快速开始
    👈 从左侧导航选择「数据上传」开始体验，推荐使用模拟数据快速了解系统功能。
    """)

    st.divider()
    st.markdown("### 技术栈")
    st.markdown("Python · Streamlit · Pandas · NumPy · Scikit-learn · Plotly · mlxtend · SciPy")

    with st.expander("项目结构"):
        st.code("""
restaurant-analytics/
├── app.py                  # 主入口
├── pages/
│   ├── 1_数据上传.py        # 数据上传 & ETL
│   ├── 2_经营概览.py        # 经营概览
│   ├── 3_商品分析.py        # 商品 & 关联规则分析
│   ├── 4_用户分析.py        # RFM + K-Means
│   ├── 5_智能预测.py        # 时序预测 & 异常检测
│   └── 6_分析报告.py        # 一键分析报告
├── src/                    # 核心逻辑
│   ├── data_pipeline.py    # ETL 数据管道
│   ├── features.py         # 特征工程
│   ├── models.py           # ML 模型
│   ├── analysis.py         # 统计分析
│   ├── visualization.py    # Plotly 图表
│   └── report.py           # 报告生成
└── sample_data/            # 模拟数据
        """, language="text")


if __name__ == "__main__":
    main()
