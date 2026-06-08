"""全局样式注入 — 清爽商务风"""

import streamlit as st


def apply_global_style():
    """注入全局 CSS"""
    st.markdown("""
    <style>
    /* ===== 字体 ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ===== 主容器 ===== */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }

    /* ===== 侧边栏 ===== */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e5e7eb;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    /* ===== 标题样式 ===== */
    h1 {
        font-weight: 700 !important;
        color: #1a1a2e !important;
        letter-spacing: -0.02em;
    }
    h2 {
        font-weight: 600 !important;
        color: #1a1a2e !important;
    }
    h3 {
        font-weight: 600 !important;
        color: #374151 !important;
    }

    /* ===== 度量卡片 ===== */
    [data-testid="stMetric"] {
        background: white;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: box-shadow 0.2s;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    [data-testid="stMetric"] label {
        color: #6b7280 !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1a1a2e !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
    }

    /* ===== 按钮 ===== */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        padding: 0.5rem 1.5rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }

    /* ===== 数据表格 ===== */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
    }

    /* ===== 展开区域 ===== */
    .streamlit-expanderHeader {
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }

    /* ===== 信息/警告框 ===== */
    .stAlert {
        border-radius: 10px;
        border: none;
    }

    /* ===== 分割线 ===== */
    hr {
        border-color: #e5e7eb;
        margin: 1.5rem 0;
    }

    /* ===== 图表容器 ===== */
    .stPlotlyChart {
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        padding: 0.5rem;
        background: white;
    }
    </style>
    """, unsafe_allow_html=True)


def hero_banner():
    """首页 Hero 区域"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 50%, #f8f9fa 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        border: 1px solid #d1fae5;
        text-align: center;
    ">
        <h1 style="
            color: #065f46;
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            letter-spacing: -0.03em;
        ">餐饮多平台经营数据分析系统</h1>
        <p style="
            color: #6b7280;
            font-size: 1.05rem;
            margin-bottom: 0;
        ">上传订单 CSV → 自动清洗分析 → 智能经营建议 · 全链路数据闭环</p>
    </div>
    """, unsafe_allow_html=True)


def section_header(title, icon=""):
    """统一的分区标题"""
    st.markdown(f"""
    <div style="
        border-bottom: 2px solid #10B981;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
    ">
        <h3 style="color: #1a1a2e; font-weight: 600; margin: 0;">{icon} {title}</h3>
    </div>
    """, unsafe_allow_html=True)


def info_card(text):
    """信息提示卡片"""
    st.markdown(f"""
    <div style="
        background: #f0fdf4;
        border-left: 4px solid #10B981;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        color: #065f46;
    ">{text}</div>
    """, unsafe_allow_html=True)


def tip_card(text):
    """提示卡片（灰色）"""
    st.markdown(f"""
    <div style="
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        color: #6b7280;
        font-size: 0.9rem;
    ">{text}</div>
    """, unsafe_allow_html=True)
