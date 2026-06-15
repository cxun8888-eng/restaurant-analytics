"""侧边栏导航样式 + 标题层级 — 统一注入"""

import streamlit as st


def inject_nav_css():
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 340px !important;
    }

    /* 基础样式 */
    [data-testid="stSidebarNavLink"] {
        font-size: 2rem !important;
        font-weight: 600 !important;
        padding: 1rem 1.2rem !important;
        margin: 10px 0 !important;
        border-radius: 10px !important;
        border-left: 5px solid transparent !important;
        transition: all 0.15s !important;
    }
    [data-testid="stSidebarNavLink"]:hover {
        filter: brightness(0.95) !important;
    }

    /* 当前激活页 */
    [data-testid="stSidebarNavLink"][aria-current="page"] {
        font-weight: 700 !important;
        font-size: 2.4rem !important;
        color: #111 !important;
    }

    /* ===== 按位置配色 (nth-child) ===== */
    /* 1 — 首页 — 蓝 */
    [data-testid="stSidebarNavLink"]:nth-child(1) {
        border-left-color: #3b82f6 !important;
        background-color: #eff6ff !important;
    }
    [data-testid="stSidebarNavLink"]:nth-child(1)[aria-current="page"] {
        background-color: #dbeafe !important;
    }

    /* 2 — 数据上传与分析报告 — 绿 */
    [data-testid="stSidebarNavLink"]:nth-child(2) {
        border-left-color: #10b981 !important;
        background-color: #ecfdf5 !important;
    }
    [data-testid="stSidebarNavLink"]:nth-child(2)[aria-current="page"] {
        background-color: #d1fae5 !important;
    }

    /* 3 — 运营分析 — 琥珀 */
    [data-testid="stSidebarNavLink"]:nth-child(3) {
        border-left-color: #f59e0b !important;
        background-color: #fffbeb !important;
    }
    [data-testid="stSidebarNavLink"]:nth-child(3)[aria-current="page"] {
        background-color: #fef3c7 !important;
    }

    /* 4 — 商品分析 — 紫 */
    [data-testid="stSidebarNavLink"]:nth-child(4) {
        border-left-color: #8b5cf6 !important;
        background-color: #f5f3ff !important;
    }
    [data-testid="stSidebarNavLink"]:nth-child(4)[aria-current="page"] {
        background-color: #ede9fe !important;
    }

    /* 5 — 用户分析 — 粉 */
    [data-testid="stSidebarNavLink"]:nth-child(5) {
        border-left-color: #ec4899 !important;
        background-color: #fdf2f8 !important;
    }
    [data-testid="stSidebarNavLink"]:nth-child(5)[aria-current="page"] {
        background-color: #fce7f3 !important;
    }

    /* 6 — 智能预测 — 青 */
    [data-testid="stSidebarNavLink"]:nth-child(6) {
        border-left-color: #06b6d4 !important;
        background-color: #ecfeff !important;
    }
    [data-testid="stSidebarNavLink"]:nth-child(6)[aria-current="page"] {
        background-color: #cffafe !important;
    }

    /* 7 — 可视化大屏 — 橙 */
    [data-testid="stSidebarNavLink"]:nth-child(7) {
        border-left-color: #f97316 !important;
        background-color: #fff7ed !important;
    }
    [data-testid="stSidebarNavLink"]:nth-child(7)[aria-current="page"] {
        background-color: #fed7aa !important;
    }

    /* ===== 标题层级 ===== */
    h1 {
        font-size: 2rem !important;
        font-weight: 300 !important;
        color: #111 !important;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    h2 {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        color: #1a1a2e !important;
        border-left: 4px solid #60a5fa;
        padding-left: 0.6rem;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }
    h3 {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #6b7280 !important;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    h4 {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        color: #9ca3af !important;
    }
    </style>

    <script>
    // "app" → "首页"
    new MutationObserver(() => {
        document.querySelectorAll('[data-testid="stSidebarNavLink"] span').forEach(el => {
            if (el.textContent.trim() === 'app') el.textContent = '首页';
        });
    }).observe(document.body, { childList: true, subtree: true });
    </script>
    """, unsafe_allow_html=True)
