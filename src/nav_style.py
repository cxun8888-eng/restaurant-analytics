"""侧边栏导航样式 + 标题层级 — 统一注入"""

import streamlit as st


def inject_nav_css():
    st.markdown("""
    <style>
    /* ===== 侧边栏 ===== */
    [data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 340px !important;
    }

    /* 所有导航项 */
    [data-testid="stSidebarNavLink"] {
        font-size: 2rem !important;
        font-weight: 600 !important;
        padding: 1rem 1.2rem !important;
        margin: 10px 0 !important;
        border-radius: 10px !important;
        transition: all 0.15s !important;
    }
    [data-testid="stSidebarNavLink"]:hover {
        background-color: #e8e8e8 !important;
    }

    /* 当前激活页 */
    [data-testid="stSidebarNavLink"][aria-current="page"] {
        background-color: #dceefb !important;
        font-weight: 700 !important;
        font-size: 2.4rem !important;
        color: #111 !important;
    }

    /* ===== 标题层级 ===== */
    /* h1 — 页面主标题：大 · 细 · 深 */
    h1 {
        font-size: 2rem !important;
        font-weight: 300 !important;
        color: #111 !important;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }

    /* h2 — 区块标题：中 · 半粗 · 带左色条 */
    h2 {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        color: #1a1a2e !important;
        border-left: 4px solid #60a5fa;
        padding-left: 0.6rem;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }

    /* h3 — 子区块：小 · 粗 · 灰 */
    h3 {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #6b7280 !important;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }

    /* h4 — 更小标注 */
    h4 {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        color: #9ca3af !important;
    }
    </style>
    """, unsafe_allow_html=True)
