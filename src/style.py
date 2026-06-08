"""全局样式 — 极简白"""

import streamlit as st


def apply_global_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
        font-weight: 400;
    }

    /* ===== 去掉所有默认装饰 ===== */
    .main .block-container {
        padding-top: 1.5rem;
        max-width: 1100px;
    }

    /* ===== 侧边栏 — 干净 ===== */
    [data-testid="stSidebar"] {
        background-color: #fafafa;
    }
    [data-testid="stSidebarNavLink"] {
        font-size: 0.95rem !important;
        font-weight: 400 !important;
        padding: 0.45rem 0.8rem !important;
        border-radius: 6px !important;
    }
    [data-testid="stSidebarNavLink"][aria-current="page"] {
        background-color: #f0f0f0 !important;
        font-weight: 500 !important;
    }

    /* ===== 标题 ===== */
    h1 {
        font-weight: 300 !important;
        font-size: 2.2rem !important;
        letter-spacing: -0.03em;
        color: #111 !important;
    }
    h2 {
        font-weight: 400 !important;
        font-size: 1.4rem !important;
        color: #111 !important;
    }
    h3 {
        font-weight: 500 !important;
        font-size: 1.1rem !important;
        color: #333 !important;
    }

    /* ===== 度量卡 — 无边框大数字 ===== */
    [data-testid="stMetric"] {
        background: none;
        padding: 0.5rem 0;
    }
    [data-testid="stMetric"] label {
        color: #999 !important;
        font-size: 0.75rem !important;
        font-weight: 400 !important;
        letter-spacing: 0.06em;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-weight: 300 !important;
        font-size: 2.2rem !important;
        color: #111 !important;
    }

    /* ===== 按钮 ===== */
    .stButton > button {
        border-radius: 6px;
        font-weight: 400;
        padding: 0.4rem 1.2rem;
        border: 1px solid #ddd;
        background: white;
        color: #333;
    }
    .stButton > button:hover {
        border-color: #111;
        color: #111;
    }

    /* ===== 表格 — 极简线条 ===== */
    [data-testid="stDataFrame"] {
        border: none;
    }

    /* ===== 展开区域 ===== */
    .streamlit-expanderHeader {
        border: none;
        background: #fafafa;
        border-radius: 0;
        font-weight: 400;
    }

    /* ===== 信息提示 ===== */
    .stAlert {
        border-radius: 0;
        border: none;
        border-left: 2px solid #ddd;
    }

    /* ===== 分割线 — 淡 ===== */
    hr {
        border-color: #eee;
        margin: 2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


def page_title(text):
    """大标题"""
    st.markdown(f"""
    <div style="margin: 1.5rem 0 2rem 0;">
        <h1 style="font-weight: 300; font-size: 2rem; margin: 0; color: #111;">{text}</h1>
    </div>
    """, unsafe_allow_html=True)


def section(text):
    """章节标题"""
    st.markdown(f"""
    <div style="margin: 2rem 0 1rem 0;">
        <span style="font-size: 0.75rem; font-weight: 500; letter-spacing: 0.08em; color: #999; text-transform: uppercase;">{text}</span>
    </div>
    """, unsafe_allow_html=True)


def quiet(text):
    """灰色小字"""
    st.markdown(f"""
    <p style="color: #999; font-size: 0.85rem; font-weight: 300;">{text}</p>
    """, unsafe_allow_html=True)


def spacer(height=2):
    """留白"""
    st.markdown(f'<div style="height: {height}rem;"></div>', unsafe_allow_html=True)
