"""侧边栏导航样式 + 标题层级 — 统一注入"""

import streamlit as st
import streamlit.components.v1 as components


def inject_nav_css():
    # ===== CSS 部分 =====
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 340px !important;
    }

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
    [data-testid="stSidebarNavLink"][aria-current="page"] {
        font-weight: 700 !important;
        font-size: 2.4rem !important;
        color: #111 !important;
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
    """, unsafe_allow_html=True)

    # ===== JS 部分（用 components.html 注入，不会被过滤） =====
    components.html("""
    <script>
    (function() {
        const COLORS = {
            'app':        { border: '#3b82f6', bg: '#eff6ff' },
            '首页':        { border: '#3b82f6', bg: '#eff6ff' },
            '数据上传与分析报告': { border: '#10b981', bg: '#ecfdf5' },
            '运营分析':     { border: '#f59e0b', bg: '#fffbeb' },
            '商品分析':     { border: '#8b5cf6', bg: '#f5f3ff' },
            '用户分析':     { border: '#ec4899', bg: '#fdf2f8' },
            '智能预测':     { border: '#06b6d4', bg: '#ecfeff' },
            '可视化大屏':   { border: '#f97316', bg: '#fff7ed' },
        };

        function colorize() {
            document.querySelectorAll('[data-testid="stSidebarNavLink"]').forEach(el => {
                const text = el.textContent.trim();
                const c = COLORS[text];
                if (!c) return;

                if (text === 'app') {
                    const span = el.querySelector('span');
                    if (span) span.textContent = '首页';
                }

                el.style.borderLeftColor = c.border;

                if (el.getAttribute('aria-current') === 'page') {
                    el.style.backgroundColor = c.border + '22';
                } else {
                    el.style.backgroundColor = c.bg;
                }
            });
        }

        colorize();
        setInterval(colorize, 500);
    })();
    </script>
    """, height=0, scrolling=False)
