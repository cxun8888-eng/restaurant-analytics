"""
页面7：可视化大屏
全维度数据看板 — 核心指标 + 图表一览
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.nav_style import inject_nav_css
from src.analysis import (
    compute_overview_metrics,
    compute_trend_analysis,
    compute_platform_comparison,
    compute_product_analysis,
)
from src.features import build_hourly_heatmap, build_rfm_features
from src.visualization import (
    revenue_trend_chart,
    hourly_heatmap_chart,
    platform_comparison_chart,
    product_ranking_chart,
    category_pie_chart,
    rfm_segment_bar,
)


st.set_page_config(page_title="可视化大屏 | 餐饮数据分析", page_icon="📺", layout="wide")

GUIDES = {
    "营收趋势": """
    **怎么看这张图？**
    - **蓝色实线**：每天的实际营收
    - **黄色虚线**：7日移动平均，平滑波动看趋势
    - **下方柱状图**：日环比变化，绿涨红跌
    """,
    "时段热力图": """
    **怎么看这张图？**
    - **行**=星期几，**列**=小时，**颜色越深**=订单越多
    - 11-13点（午餐）和17-20点（晚餐）是两个高峰
    - 周末下午时段比工作日活跃
    """,
    "商品排行": """
    **怎么看这张图？**
    - 横条越长 = 销量越高
    - 蓝色越深 = 销量越大
    - Top 10 快速识别爆款
    """,
    "品类占比": """
    **怎么看这张图？**
    - 扇区越大 = 营收贡献越高
    - 右侧图例显示品类名称
    - 帮助判断核心竞争力
    """,
    "用户分层": """
    **怎么看这张图？**
    - 横条越长 = 该类用户越多
    - 重点关注"重要挽留"和"流失高价值"——人数少但价值高
    - 帮助决定营销资源分配
    """,
    "平台对比": """
    **怎么看这张图？**
    - 左侧饼图：各平台营收占比
    - 右侧柱状图：各平台客单价对比
    - 退款率差异反映平台用户质量
    """,
}


def main():
    inject_nav_css()

    st.title("📺 可视化大屏")

    df = st.session_state.get("df_orders")
    if df is None:
        st.warning("请先在「数据上传与分析报告」页面加载数据")
        return

    # ===== KPI 指标 =====
    metrics = compute_overview_metrics(df)
    stats = metrics["revenue_stats"]

    st.subheader("核心经营指标")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("总营收", f"¥{metrics['total_revenue']:,.0f}")
    with col2:
        st.metric("总订单", f"{metrics['total_orders']:,}")
    with col3:
        st.metric("客单价", f"¥{metrics['avg_order_value']:.2f}")
    with col4:
        st.metric("退款率", f"{metrics['refund_rate']:.1f}%")
    with col5:
        st.metric("顾客数", f"{metrics.get('n_customers', 0):,}")
    with col6:
        dod = metrics["dod_change"]
        st.metric("日环比", f"{dod:+.1f}%")

    st.caption(
        f"统计五数 | 均值 ¥{stats['mean']:,.0f} | "
        f"中位数 ¥{stats['median']:,.0f} | "
        f"标准差 ¥{stats['std']:,.0f} | "
        f"偏度 {stats['skewness']} | 峰度 {stats['kurtosis']}"
    )

    st.divider()
    st.markdown("<br>", unsafe_allow_html=True)

    # ===== 营收趋势 — 全宽大图 =====
    col_t, col_b = st.columns([10, 1])
    with col_t:
        st.subheader("📈 营收趋势")
    with col_b:
        with st.popover("📖 解读"):
            st.markdown(GUIDES["营收趋势"])

    daily_df = compute_trend_analysis(df)
    fig_trend = revenue_trend_chart(daily_df)
    fig_trend.update_layout(height=500)
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== 时段热力图 + 平台对比 =====
    col_left, col_right = st.columns(2)

    with col_left:
        col_t, col_b = st.columns([10, 1])
        with col_t:
            st.subheader("🕐 时段热力图")
        with col_b:
            with st.popover("📖 解读"):
                st.markdown(GUIDES["时段热力图"])

        heatmap = build_hourly_heatmap(df)
        if not heatmap.empty:
            fig_heat = hourly_heatmap_chart(heatmap)
            fig_heat.update_layout(height=450)
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("缺少小时数据")

    with col_right:
        col_t, col_b = st.columns([10, 1])
        with col_t:
            st.subheader("📱 平台对比")
        with col_b:
            with st.popover("📖 解读"):
                st.markdown(GUIDES["平台对比"])

        platform_df = compute_platform_comparison(df)
        if not platform_df.empty:
            fig_plat = platform_comparison_chart(platform_df)
            fig_plat.update_layout(height=450)
            st.plotly_chart(fig_plat, use_container_width=True)
        else:
            st.info("缺少平台数据")

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # ===== 商品排行 — 全宽 =====
    col_t, col_b = st.columns([10, 1])
    with col_t:
        st.subheader("🔥 商品销量排行 Top 10")
    with col_b:
        with st.popover("📖 解读"):
            st.markdown(GUIDES["商品排行"])

    product_data = compute_product_analysis(df)
    ranking = product_data["product_ranking"]
    fig_rank = product_ranking_chart(ranking, top_n=10)
    fig_rank.update_layout(height=450)
    st.plotly_chart(fig_rank, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== 品类占比 + 用户分层 =====
    col_left, col_right = st.columns(2)
    categories = product_data["category_breakdown"]
    rfm_df = build_rfm_features(df)

    with col_left:
        col_t, col_b = st.columns([10, 1])
        with col_t:
            st.subheader("🥧 品类营收占比")
        with col_b:
            with st.popover("📖 解读"):
                st.markdown(GUIDES["品类占比"])

        if not categories.empty:
            fig_pie = category_pie_chart(categories)
            fig_pie.update_layout(height=450)
            st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        col_t, col_b = st.columns([10, 1])
        with col_t:
            st.subheader("👥 用户分层")
        with col_b:
            with st.popover("📖 解读"):
                st.markdown(GUIDES["用户分层"])

        if not rfm_df.empty:
            fig_seg = rfm_segment_bar(rfm_df)
            fig_seg.update_layout(height=450)
            st.plotly_chart(fig_seg, use_container_width=True)

    st.divider()

    # ===== 导出为 PNG 大图 =====
    st.subheader("📥 导出大屏")
    if st.button("生成大屏高清图片 (PNG)", type="primary"):
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO
        import plotly.io as pio

        with st.spinner("正在生成高清大图，请稍候..."):
            # 导出每张图为 PNG
            imgs = []
            for fig in [fig_trend, fig_heat, fig_rank, fig_pie, fig_seg, fig_plat]:
                fig_copy = fig.to_dict()
                fig_copy["layout"]["template"] = None  # 去掉主题让图片更干净
                buf = pio.to_image(fig, format="png", scale=2, width=1200, height=600)
                imgs.append(Image.open(BytesIO(buf)))

            # 统一宽度
            target_w = 1200
            for i in range(len(imgs)):
                w, h = imgs[i].size
                ratio = target_w / w
                imgs[i] = imgs[i].resize((target_w, int(h * ratio)), Image.LANCZOS)

            # 拼成 3行×2列 的网格
            gap = 20  # 图间距
            col_w = (target_w - gap) // 2
            total_w = target_w
            total_h = 0

            # 调整每张小图为统一列宽
            for i in range(len(imgs)):
                w, h = imgs[i].size
                new_h = int(h * col_w / w)
                imgs[i] = imgs[i].resize((col_w, new_h), Image.LANCZOS)

            # 计算总高度
            rows = [(0, 1), (2, 3), (4, 5)]  # 图表索引配对
            row_heights = []
            for left_i, right_i in rows:
                row_heights.append(max(imgs[left_i].size[1], imgs[right_i].size[1]))
            total_h = sum(row_heights) + gap * (len(rows) - 1)

            # 创建画布
            canvas = Image.new("RGB", (target_w, total_h + 80), (255, 255, 255))
            draw = ImageDraw.Draw(canvas)

            # 拼图
            y = 0
            for row_idx, (left_i, right_i) in enumerate(rows):
                row_h = row_heights[row_idx]
                # 左图
                lw, lh = imgs[left_i].size
                canvas.paste(imgs[left_i], (0, y + (row_h - lh) // 2))
                # 右图
                rw, rh = imgs[right_i].size
                canvas.paste(imgs[right_i], (col_w + gap, y + (row_h - rh) // 2))
                y += row_h + gap

            # 另存为字节
            out_buf = BytesIO()
            canvas.save(out_buf, format="PNG", optimize=True)
            img_bytes = out_buf.getvalue()

        st.success(f"高清大图已生成（{canvas.size[0]}×{canvas.size[1]}px）！可用于 PPT、打印或直接分享。")
        st.download_button(
            label="📥 下载大屏图片 (PNG)",
            data=img_bytes,
            file_name="可视化大屏.png",
            mime="image/png",
        )

    st.caption("数据科学与大数据技术 · 可视化大屏")


if __name__ == "__main__":
    main()
