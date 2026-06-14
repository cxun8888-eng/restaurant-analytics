"""侧边栏导航样式 — 统一注入"""

import streamlit as st


def inject_nav_css():
    st.markdown("""
    <style>
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
    </style>
    """, unsafe_allow_html=True)
