"""
餐饮多平台经营数据分析系统
"""

import streamlit as st

st.set_page_config(
    page_title="餐饮经营数据分析",
    page_icon="·",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    # ===== 全局样式 =====
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main .block-container { padding-top: 0; max-width: 100%; }

    /* 侧边栏 — 轻量化 */
    [data-testid="stSidebar"] { background-color: #fafafa; }
    [data-testid="stSidebarNavLink"] { font-size: 0.85rem !important; padding: 0.3rem 0.6rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # ===== 主体 Hero =====
    st.markdown("""
    <div style="padding: 6rem 3rem 4rem 3rem;">
        <div style="max-width: 800px;">
            <div style="font-size: 0.75rem; letter-spacing: 0.15em; color: #999; margin-bottom: 1.5rem;">
                餐饮经营数据分析系统
            </div>
            <div style="font-size: 3.5rem; font-weight: 300; color: #111; line-height: 1.2; margin-bottom: 1.5rem;">
                让每一份订单数据<br>产生真正的价值
            </div>
            <div style="font-size: 1.1rem; color: #888; font-weight: 300; max-width: 500px; line-height: 1.6;">
                上传美团、饿了么、微信点单的 CSV 文件，自动完成清洗、分析、预测，输出经营建议。
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ===== 功能 — 横向大块 =====
    features = [
        ("01", "数据管道", "自动识别多平台表头，校验字段，处理缺失值，检测异常数据。"),
        ("02", "多维分析", "营收趋势、时段分布、平台对比、商品排行、品类占比。"),
        ("03", "算法建模", "RFM 用户分层、Apriori 关联规则、K-Means 聚类、随机森林预测。"),
        ("04", "智能报告", "一键生成自然语言诊断报告，把数据变成可执行的经营建议。"),
    ]

    for num, title, desc in features:
        st.markdown(f"""
        <div style="padding: 2rem 3rem; border-top: 1px solid #f0f0f0;">
            <div style="display: flex; align-items: flex-start; gap: 3rem; max-width: 1000px;">
                <div style="font-size: 2rem; font-weight: 200; color: #ddd; min-width: 60px;">{num}</div>
                <div>
                    <div style="font-weight: 500; font-size: 1.2rem; color: #111; margin-bottom: 0.3rem;">{title}</div>
                    <div style="color: #999; font-weight: 300;">{desc}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ===== 底部 =====
    st.markdown("""
    <div style="padding: 4rem 3rem; border-top: 1px solid #f0f0f0; margin-top: 3rem;">
        <div style="font-size: 0.8rem; color: #ccc;">
            数据科学与大数据技术 · 个人项目
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
