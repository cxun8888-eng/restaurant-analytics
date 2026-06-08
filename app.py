"""
餐饮多平台经营数据分析系统
"""

import streamlit as st
from src.style import apply_global_style, page_title, section, quiet, spacer

st.set_page_config(
    page_title="餐饮经营数据分析",
    page_icon="·",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    apply_global_style()

    # ===== 侧边栏 =====
    with st.sidebar:
        spacer(1)
        st.markdown("### 餐饮分析")

        st.markdown("""
        <div style="font-size: 0.82rem; color: #999; line-height: 2;">
        数据上传<br>
        经营概览<br>
        商品分析<br>
        用户分析<br>
        智能预测<br>
        分析报告
        </div>
        """, unsafe_allow_html=True)

        spacer(2)
        st.markdown("""
        <div style="font-size: 0.75rem; color: #bbb; line-height: 1.6;">
        Python · Streamlit<br>
        Pandas · Scikit-learn<br>
        Plotly
        </div>
        """, unsafe_allow_html=True)

    # ===== 主页 =====
    page_title("餐饮经营数据分析")

    quiet("上传美团、饿了么、微信点单的订单数据，自动完成清洗、分析与经营建议。")

    spacer(3)

    # ---- 三步 ----
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="font-size: 2rem; font-weight: 200; color: #ccc;">01</div>
        <div style="font-weight: 500; margin: 0.3rem 0;">上传数据</div>
        <div style="font-size: 0.82rem; color: #999;">支持 CSV / Excel 文件</div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="font-size: 2rem; font-weight: 200; color: #ccc;">02</div>
        <div style="font-weight: 500; margin: 0.3rem 0;">自动分析</div>
        <div style="font-size: 0.82rem; color: #999;">清洗 · 建模 · 可视化</div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="font-size: 2rem; font-weight: 200; color: #ccc;">03</div>
        <div style="font-weight: 500; margin: 0.3rem 0;">经营建议</div>
        <div style="font-size: 0.82rem; color: #999;">一键生成诊断报告</div>
        """, unsafe_allow_html=True)

    spacer(3)
    st.divider()

    # ---- 能力 ----
    section("核心能力")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <p style="font-weight: 500;">数据科学方法</p>
        <p style="font-size: 0.85rem; color: #666; line-height: 1.8;">
        RFM 用户分层<br>
        Apriori 关联规则<br>
        K-Means 聚类<br>
        随机森林回归<br>
        Isolation Forest
        </p>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <p style="font-weight: 500;">数据处理链路</p>
        <p style="font-size: 0.85rem; color: #666; line-height: 1.8;">
        多平台数据识别<br>
        IQR 异常检测<br>
        缺失值智能处理<br>
        特征工程<br>
        数据质量报告
        </p>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <p style="font-weight: 500;">业务决策输出</p>
        <p style="font-size: 0.85rem; color: #666; line-height: 1.8;">
        经营诊断报告<br>
        套餐搭配建议<br>
        用户运营策略<br>
        滞销品优化<br>
        营收预测预警
        </p>
        """, unsafe_allow_html=True)

    spacer(2)
    st.divider()
    quiet("数据科学与大数据技术 · 个人项目")


if __name__ == "__main__":
    main()
