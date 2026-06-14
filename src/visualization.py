"""
可视化工厂模块
基于 Plotly 封装常用图表，统一风格，减少页面代码冗余
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, List


# ===== 主题色 =====
COLORS = {
    "primary": "#4F46E5",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "palette": ["#4F46E5", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#06B6D4", "#F97316"],
}

# ===== 布局 =====
CHART_HEIGHT = 400


def revenue_trend_chart(daily_df: pd.DataFrame) -> go.Figure:
    """营收趋势折线图（含移动平均 + 日环比柱状图）"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3],
        subplot_titles=("日营收趋势", "日环比变化(%)"),
    )

    # 折线图 + 移动平均
    fig.add_trace(
        go.Scatter(
            x=daily_df["date"], y=daily_df["revenue"],
            mode="lines+markers", name="日营收",
            line=dict(color=COLORS["primary"], width=2),
            marker=dict(size=4),
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=daily_df["date"], y=daily_df["ma7"],
            mode="lines", name="7日移动平均",
            line=dict(color=COLORS["warning"], width=2, dash="dash"),
        ),
        row=1, col=1,
    )

    # 日环比柱状图
    colors = [COLORS["success"] if v >= 0 else COLORS["danger"] for v in daily_df["dod_pct"].fillna(0)]
    fig.add_trace(
        go.Bar(x=daily_df["date"], y=daily_df["dod_pct"], name="日环比",
               marker_color=colors, opacity=0.7),
        row=2, col=1,
    )

    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)

    fig.update_layout(
        height=500, hovermode="x unified",
        showlegend=True, margin=dict(l=20, r=20, t=40, b=20),
    )
    fig.update_yaxes(title_text="营收 (¥)", row=1, col=1)
    fig.update_yaxes(title_text="环比 (%)", row=2, col=1)

    return fig


def product_ranking_chart(product_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """商品销量排名水平柱状图"""
    df = product_df.head(top_n).sort_values("total_sold", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["product_name"],
        x=df["total_sold"],
        orientation="h",
        marker=dict(
            color=df["total_sold"],
            colorscale="blues",
            showscale=False,
        ),
        text=df["total_sold"].apply(lambda x: f"{x}份"),
        textposition="outside",
    ))

    fig.update_layout(
        title=f"商品销量排行 Top {top_n}",
        height=CHART_HEIGHT + 100,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(autorange="reversed"),
        xaxis_title="销量（份）",
    )
    return fig


def category_pie_chart(category_df: pd.DataFrame) -> go.Figure:
    """品类营收占比饼图"""
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=category_df.index,
        values=category_df["revenue_share"],
        hole=0.4,
        marker=dict(colors=COLORS["palette"]),
        textinfo="label+percent",
        textposition="outside",
    ))

    fig.update_layout(
        title="品类营收占比",
        height=450,
        margin=dict(l=20, r=120, t=40, b=20),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
        ),
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
    )
    return fig


def hourly_heatmap_chart(heatmap_df: pd.DataFrame) -> go.Figure:
    """时段 × 工作日 热力图"""
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_df.values,
        x=[f"{h}:00" for h in heatmap_df.columns],
        y=heatmap_df.index.tolist(),
        colorscale="YlOrRd",
        text=np.round(heatmap_df.values, 1),
        texttemplate="%{text}",
        textfont={"size": 10},
        colorbar=dict(title="平均订单数"),
    ))

    fig.update_layout(
        title="时段热力图（工作日×小时）",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="时段",
        yaxis_title="",
    )
    return fig


def rfm_scatter_3d(rfm_df: pd.DataFrame, color_col: str = "segment") -> go.Figure:
    """RFM 3D 散点图"""
    fig = px.scatter_3d(
        rfm_df,
        x="recency",
        y="frequency",
        z="monetary",
        color=color_col,
        size="RFM_score",
        opacity=0.7,
        color_discrete_sequence=COLORS["palette"],
        hover_data=["customer_id"],
    )

    fig.update_layout(
        title="用户 RFM 三维分布",
        height=500,
        margin=dict(l=0, r=0, t=40, b=0),
        scene=dict(
            xaxis_title="消费间隔 (天)",
            yaxis_title="消费频次 (次)",
            zaxis_title="消费金额 (¥)",
        ),
    )
    return fig


def rfm_segment_bar(rfm_df: pd.DataFrame) -> go.Figure:
    """RFM 分层用户数量柱状图"""
    seg_counts = rfm_df["segment"].value_counts()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=seg_counts.values,
        y=seg_counts.index,
        orientation="h",
        marker_color=COLORS["primary"],
        text=seg_counts.values,
        textposition="outside",
    ))

    fig.update_layout(
        title="用户分层分布",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(autorange="reversed"),
        xaxis_title="用户数",
    )
    return fig


def forecast_chart(forecast_df: pd.DataFrame, historical_df: Optional[pd.DataFrame] = None) -> go.Figure:
    """预测结果图"""
    fig = go.Figure()

    # 预测值
    fig.add_trace(go.Scatter(
        x=forecast_df["date"],
        y=forecast_df["predicted"],
        mode="lines+markers",
        name="预测值",
        line=dict(color=COLORS["primary"], width=3),
    ))

    # 置信区间
    fig.add_trace(go.Scatter(
        x=forecast_df["date"].tolist() + forecast_df["date"].tolist()[::-1],
        y=forecast_df["upper_bound"].tolist() + forecast_df["lower_bound"].tolist()[::-1],
        fill="toself",
        fillcolor="rgba(79,70,229,0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        name="置信区间",
    ))

    # 历史数据（如果有）
    if historical_df is not None:
        fig.add_trace(go.Scatter(
            x=historical_df["date"],
            y=historical_df["revenue"],
            mode="lines",
            name="历史营收",
            line=dict(color="gray", width=1, dash="dot"),
        ))

    fig.update_layout(
        title="未来营收预测",
        height=CHART_HEIGHT,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="日期",
        yaxis_title="预测营收 (¥)",
    )
    return fig


def platform_comparison_chart(platform_df: pd.DataFrame) -> go.Figure:
    """平台对比雷达图 + 柱状图"""
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "xy"}]],
        subplot_titles=("平台营收占比", "平台客单价对比"),
    )

    # 饼图
    fig.add_trace(
        go.Pie(
            labels=platform_df.index,
            values=platform_df["total_revenue"],
            hole=0.4,
            marker=dict(colors=COLORS["palette"]),
        ),
        row=1, col=1,
    )

    # 柱状图
    fig.add_trace(
        go.Bar(
            x=platform_df.index,
            y=platform_df["avg_order_value"],
            marker_color=COLORS["palette"],
            text=platform_df["avg_order_value"].apply(lambda x: f"¥{x}"),
            textposition="outside",
        ),
        row=1, col=2,
    )

    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def association_chart(assoc_df: pd.DataFrame) -> go.Figure:
    """关联规则气泡图"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=assoc_df["support"],
        y=assoc_df["confidence"],
        mode="markers+text",
        marker=dict(
            size=assoc_df["lift"] * 10,
            color=assoc_df["lift"],
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="提升度"),
        ),
        text=[f"{a} → {c}" for a, c in zip(assoc_df["antecedent"], assoc_df["consequent"])],
        textposition="top center",
    ))

    fig.update_layout(
        title="关联规则分布（气泡大小=提升度）",
        height=CHART_HEIGHT,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="支持度",
        yaxis_title="置信度",
    )
    return fig


def elbow_curve_chart(elbow_df: pd.DataFrame) -> go.Figure:
    """K-Means 肘部法则图"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=elbow_df["k"],
        y=elbow_df["inertia"],
        mode="lines+markers",
        line=dict(color=COLORS["primary"], width=2),
        marker=dict(size=10),
    ))
    fig.update_layout(
        title="K-Means 肘部法则（选择最优K值）",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(dtick=1),
        xaxis_title="聚类数 K",
        yaxis_title="误差平方和(SSE)",
    )
    return fig
