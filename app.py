"""
餐饮多平台经营数据分析系统
技术栈：Python + Streamlit + Pandas + Scikit-learn + Plotly
"""

import streamlit as st
from src.style import apply_global_style, hero_banner, section_header, info_card

st.set_page_config(
    page_title="餐饮多平台经营数据分析系统",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    apply_global_style()

    # ===== 侧边栏 =====
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 2.5rem;">🍜</div>
            <div style="font-weight: 700; font-size: 1.1rem; color: #1a1a2e;">餐饮分析系统</div>
            <div style="font-size: 0.75rem; color: #9ca3af;">Restaurant Analytics</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("""
        ### 分析模块
        """)
        st.markdown("""
        <div style="font-size: 0.88rem; line-height: 2.2;">
        1.  &nbsp; 数据上传 — 数据管道与质量检查<br>
        2.  &nbsp; 经营概览 — 核心指标与营收趋势<br>
        3.  &nbsp; 商品分析 — 销量排行与关联规则<br>
        4.  &nbsp; 用户分析 — RFM分层与聚类<br>
        5.  &nbsp; 智能预测 — 营收预测与异常检测<br>
        6.  &nbsp; 分析报告 — 一键诊断报告
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("""
        ### 技术栈
        <div style="font-size: 0.82rem; color: #6b7280;">
        Streamlit · Pandas · NumPy · Scikit-learn<br>
        Plotly · mlxtend · SciPy
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.caption("数据科学与大数据技术 · 个人项目")

    # ===== 主页内容 =====
    hero_banner()

    # ---- 三步流程 ----
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 2rem;">📤</div>
            <div style="font-weight: 600; margin: 0.5rem 0;">上传数据</div>
            <div style="font-size: 0.85rem; color: #6b7280;">支持美团、饿了么、微信点单<br>导出的 CSV / Excel 文件</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 2rem;">🔍</div>
            <div style="font-weight: 600; margin: 0.5rem 0;">智能分析</div>
            <div style="font-size: 0.85rem; color: #6b7280;">自动清洗 · 多维分析 · 算法建模<br>RFM分层 · 关联规则 · 营收预测</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 2rem;">📋</div>
            <div style="font-weight: 600; margin: 0.5rem 0;">经营建议</div>
            <div style="font-size: 0.85rem; color: #6b7280;">一键生成诊断报告<br>可执行的运营决策建议</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- 三大亮点卡片 ----
    section_header("核心能力", "")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1.5rem;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🔬</div>
            <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 0.75rem;">数据科学方法论</div>
            <div style="font-size: 0.85rem; color: #6b7280; line-height: 1.8;">
            RFM 用户分层 · Apriori 关联规则<br>
            K-Means 聚类 · 随机森林回归<br>
            Isolation Forest 异常检测
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1.5rem;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📊</div>
            <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 0.75rem;">全链路数据处理</div>
            <div style="font-size: 0.85rem; color: #6b7280; line-height: 1.8;">
            多平台数据自动识别 · IQR 异常检测<br>
            缺失值智能处理 · 数据质量报告<br>
            特征工程（时段/品类/用户）
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1.5rem;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">💡</div>
            <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 0.75rem;">数据驱动决策</div>
            <div style="font-size: 0.85rem; color: #6b7280; line-height: 1.8;">
            自动经营诊断报告 · 套餐搭配建议<br>
            用户分层运营策略 · 滞销品优化<br>
            未来营收预测预警
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # ---- 快速开始 ----
    info_card("👈 从左侧导航选择「数据上传」开始体验，推荐使用模拟数据快速了解系统功能。")

    # ---- 底部 ----
    st.divider()
    st.markdown("""
    <div style="text-align: center; font-size: 0.8rem; color: #9ca3af; padding: 1rem 0;">
    数据科学与大数据技术 · 个人项目 · 已部署至 Hugging Face Spaces
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
