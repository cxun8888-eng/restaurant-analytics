"""
餐饮多平台经营数据分析系统
Restaurant Multi-Platform Analytics

作者：数据科学与大数据技术专业
技术栈：Python + Streamlit + Pandas + Scikit-learn + Prophet + Plotly

启动方式：streamlit run app.py
"""

import streamlit as st


st.set_page_config(
    page_title="餐饮多平台经营数据分析系统",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    # ===== 侧边栏：系统信息 =====
    with st.sidebar:
        st.title("🍜 餐饮分析系统")
        st.markdown("---")
        st.markdown("""
        ### 关于本项目

        支持美团、微信点单、饿了么等多平台订单数据的自动清洗、多维度分析和智能决策建议。

        ### 分析模块
        1. **数据上传** — 数据管道与质量检查
        2. **经营概览** — 核心指标与营收趋势
        3. **商品分析** — 销量排行与关联规则
        4. **用户分析** — RFM分层与聚类
        5. **智能预测** — 营收预测与异常检测
        6. **分析报告** — 一键诊断报告

        ### 技术栈
        - Python 网页框架 Streamlit
        - Pandas + NumPy 数据处理
        - Scikit-learn 机器学习
        - Prophet 时序预测
        - Plotly 交互式可视化
        - mlxtend 关联规则挖掘

        ### 使用流程
        1. 上传 CSV/Excel 数据（或用模拟数据体验）
        2. 依次浏览各分析页面
        3. 在「分析报告」页生成完整报告
        """)

        st.divider()
        st.caption("数据科学与大数据技术 · 个人项目")
        st.caption("展示从数据清洗到智能决策的全链路分析能力")

    # ===== 主页内容 =====
    st.title("🍜 餐饮多平台经营数据分析系统")

    st.markdown("""
    ### 从数据到决策：餐饮经营分析一站式平台

    商家从美团、微信小程序、饿了么导出订单数据 → 上传文件 → 自动完成：
    数据清洗 → 特征建模 → 多维分析 → 可视化图表 → **智能经营建议**
    """)

    st.divider()

    # 三大亮点卡片
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 🔬 数据科学方法论

        - **RFM 用户分层**（CRM经典模型）
        - **Apriori 关联规则**（购物篮分析）
        - **K-Means 聚类**（交叉验证）
        - **Prophet 时序预测**（Meta 开源）
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

    # 快速开始
    st.markdown("""
    ### 🚀 快速开始

    👈 从左侧导航选择「**数据上传**」开始体验，推荐使用模拟数据快速了解系统功能。

    ---

    ### 💼 简历亮点

    本项目展示了数据分析师/数据科学家的核心能力：

    | 能力维度 | 具体体现 |
    |---------|---------|
    | **数据工程** | ETL管道设计、多源数据标准化、数据质量监控 |
    | **特征工程** | RFM特征构造、时段特征衍生、one-hot编码 |
    | **统计分析** | 描述统计五数、分布形态分析、偏差/峰度 |
    | **数据挖掘** | Apriori关联规则（Support/Confidence/Lift） |
    | **机器学习** | K-Means聚类、Isolation Forest异常检测 |
    | **时序预测** | Prophet模型（趋势+周期+节假日分解） |
    | **业务洞察** | RFM分层策略、关联套餐建议、自然语言报告生成 |
    | **工程能力** | Streamlit全栈部署、模块化架构、可维护代码 |

    ---

    ### 📁 项目结构

    ```
    restaurant-analytics/
    ├── app.py                     # 主入口
    ├── pages/                     # Streamlit 页面
    │   ├── 1_data_upload.py       # 数据上传 & ETL
    │   ├── 2_overview.py          # 经营概览
    │   ├── 3_product_analysis.py  # 商品分析
    │   ├── 4_user_analysis.py     # 用户分析
    │   ├── 5_prediction.py        # 智能预测
    │   └── 6_report.py            # 分析报告
    ├── src/                       # 核心逻辑（与页面解耦）
    │   ├── data_pipeline.py       # ETL 数据管道
    │   ├── features.py            # 特征工程
    │   ├── models.py              # ML 模型
    │   ├── analysis.py            # 统计分析
    │   ├── visualization.py       # Plotly 图表工厂
    │   └── report.py              # 报告生成
    ├── sample_data/               # 模拟数据
    └── notebooks/                 # 方法论文档
    ```
    """)


if __name__ == "__main__":
    main()
