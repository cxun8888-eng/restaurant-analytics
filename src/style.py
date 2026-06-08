"""全局样式 — 极简"""

import streamlit as st


def apply_global_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; font-weight: 400; }

    .main .block-container { max-width: 1100px; padding-top: 1rem; }

    /* 侧边栏 */
    [data-testid="stSidebar"] { background-color: #fafafa; }
    [data-testid="stSidebarNavLink"] { font-size: 0.85rem !important; padding: 0.3rem 0.6rem !important; font-weight: 400 !important; }
    [data-testid="stSidebarNavLink"][aria-current="page"] { background-color: #eee !important; font-weight: 500 !important; }

    /* 标题 */
    h1 { font-weight: 200 !important; font-size: 2.4rem !important; color: #111 !important; letter-spacing: -0.02em; }
    h2 { font-weight: 300 !important; font-size: 1.5rem !important; color: #111 !important; }
    h3 { font-weight: 400 !important; font-size: 1.1rem !important; color: #333 !important; }

    /* 度量卡 — 无框 */
    [data-testid="stMetric"] { background: none; padding: 0.3rem 0; }
    [data-testid="stMetric"] label { color: #aaa !important; font-size: 0.7rem !important; font-weight: 400 !important; letter-spacing: 0.08em; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { font-weight: 200 !important; font-size: 2rem !important; color: #111 !important; }

    /* 按钮 */
    .stButton > button { border-radius: 4px; font-weight: 400; border: 1px solid #ddd; background: white; color: #333; }
    .stButton > button:hover { border-color: #111; }

    /* 表格 */
    [data-testid="stDataFrame"] { border: none; }

    /* 分割线 */
    hr { border-color: #f0f0f0; margin: 2rem 0; }

    /* 信息提示 */
    .stAlert { border-radius: 0; border: none; border-left: 2px solid #ddd; background: #fafafa; }
    </style>
    """, unsafe_allow_html=True)
