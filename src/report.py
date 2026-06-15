"""
智能经营诊断报告
专业排版 · 结构化输出 · 数据驱动决策
"""

from typing import Dict, Any
import pandas as pd


def generate_full_report(
    overview: Dict[str, Any],
    product_analysis: Dict[str, pd.DataFrame],
    rfm_df: pd.DataFrame,
    assoc_rules: pd.DataFrame,
    forecast_result: pd.DataFrame,
    anomaly_orders: pd.DataFrame,
    platform_df: pd.DataFrame,
) -> str:
    """
    生成结构化的专业经营诊断报告
    """
    sections = [
        _report_header(overview),
        _section_summary(overview),
        _section_revenue_trend(overview),
        _section_anomalies(overview, anomaly_orders),
        _section_products(product_analysis),
        _section_association(assoc_rules),
        _section_users(rfm_df),
        _section_forecast(forecast_result),
        _section_recommendations(product_analysis, assoc_rules, rfm_df),
        _report_footer(overview),
    ]
    return "\n\n---\n\n".join(sections)


def _report_header(overview: Dict) -> str:
    dr = overview.get('date_range', '————')
    return f"""
# 餐饮经营数据分析报告

> **分析周期**：{dr}　|　**数据来源**：美团 / 饿了么 / 微信点单
"""


def _section_summary(overview: Dict) -> str:
    o = overview
    stats = o.get("revenue_stats", {})

    return f"""## 一、经营摘要

| 核心指标 | 数值 | 说明 |
|:--------|:-----|:-----|
| 统计周期总营收 | **¥{o['total_revenue']:,.2f}** | 全量订单实付金额合计 |
| 总订单数 | **{o['total_orders']:,} 笔** | 有效订单 + 退款订单 |
| 客单价 | **¥{o['avg_order_value']:.2f}** | 总营收 ÷ 总订单数 |
| 退款率 | {o['refund_rate']:.1f}% | {"⚠ 偏高，需关注" if o['refund_rate'] > 5 else "处于正常水平"} |
| 平均折扣率 | {o['avg_discount_rate']:.1f}% | 优惠金额占总金额比例 |

**昨日经营**：营收 ¥{o['today_revenue']:,.2f} · 订单 {o['today_orders']:,} · 较前日 {'↑' if o['dod_change'] >= 0 else '↓'}{abs(o['dod_change']):.1f}%

**营收统计特征**：
- 日均营收均值 ¥{stats.get('mean', 'N/A'):,.0f}，中位数 ¥{stats.get('median', 'N/A'):,.0f}
- 偏度 {stats.get('skewness', 'N/A')}：{'分布右偏 → 少数高峰日拉高了均值，中位数参考价值更高' if stats.get('skewness', 0) > 0.5 else '分布对称 → 均值与中位数接近' if abs(stats.get('skewness', 0)) <= 0.5 else '分布左偏'}
"""


def _section_revenue_trend(overview: Dict) -> str:
    stats = overview.get("revenue_stats", {})

    return f"""## 二、营收波动分析

| 统计量 | 数值 | 含义 |
|:------|:-----|:-----|
| 标准差 | ¥{stats.get('std', 'N/A'):,.0f} | 日常波动幅度；越大说明营收越不稳定 |
| 偏度系数 | {stats.get('skewness', 'N/A')} | {'营收集中在低值区，偶有爆单日' if stats.get('skewness', 0) > 0.5 else '营收分布均匀' if abs(stats.get('skewness', 0)) <= 0.5 else '营收集中在高值区'} |
| 峰度系数 | {stats.get('kurtosis', 'N/A')} | {'高峰度 → 营收较为稳定，集中在均值附近' if stats.get('kurtosis', 0) > 0 else '低峰度 → 营收波动较频繁'} |
"""


def _section_anomalies(overview: Dict, anomaly_orders: pd.DataFrame) -> str:
    n_anomalies = anomaly_orders["is_anomaly"].sum() if len(anomaly_orders) > 0 else 0

    items = []

    if n_anomalies > 0:
        items.append(f"| 异常订单 | **{n_anomalies} 笔**被算法检测标记 | Isolation Forest 多维异常检测 |")

    dod = abs(overview.get("dod_change", 0))
    if dod > 30:
        items.append(f"| 日环比异常 | 波动 {dod:.1f}% | 请确认是否有活动结束或竞品促销 |")

    if overview["refund_rate"] > 5:
        items.append(f"| 退款率偏高 | {overview['refund_rate']:.1f}% | 建议分析退款原因分布 |")

    if not items:
        return """## 三、异常检测

未发现明显异常，经营状况正常。
"""

    return f"""## 三、异常检测

| 类别 | 详情 | 建议 |
|:----|:-----|:-----|
{chr(10).join(items)}
"""


def _section_products(product_analysis: Dict) -> str:
    ranking = product_analysis.get("product_ranking", pd.DataFrame())
    slow = product_analysis.get("slow_movers", pd.DataFrame())

    lines = ["## 四、商品结构分析"]

    if not ranking.empty:
        top5 = ranking.head(5)
        lines.append("")
        lines.append("### 畅销商品 Top 5")
        for i, (_, row) in enumerate(top5.iterrows(), 1):
            lines.append(f"{i}. **{row['product_name']}** — 售出 {int(row['total_sold'])} 份，贡献营收 ¥{row['total_revenue']:,.2f}（占{row.get('revenue_share', '—')}%）")

    if not slow.empty:
        lines.append("")
        lines.append("### 滞销关注")
        for _, row in slow.iterrows():
            lines.append(f"- {row['product_name']}：仅售 {int(row['total_sold'])} 份，建议评估是否下架或做促销清仓")

    return "\n".join(lines)


def _section_association(assoc_rules: pd.DataFrame) -> str:
    if assoc_rules.empty:
        return ""

    top = assoc_rules.head(3)
    lines = ["## 五、菜品关联分析"]
    lines.append("")
    lines.append("基于 Apriori 关联规则挖掘，以下为提升度最高的搭配组合：")
    lines.append("")

    for _, row in top.iterrows():
        strength = "★★★ 强关联" if row["lift"] >= 3 else "★★☆ 中等关联" if row["lift"] >= 2 else "★☆☆ 弱关联"
        lines.append(f"- **{row['antecedent']} → {row['consequent']}**")
        lines.append(f"  提升度 {row['lift']:.2f}（{strength}）· 支持度 {row['support']:.4f} · 置信度 {row['confidence']:.2%}")
        lines.append(f"  → {row['recommendation']}")
        lines.append("")

    return "\n".join(lines)


def _section_users(rfm_df: pd.DataFrame) -> str:
    if rfm_df.empty:
        return "## 六、用户价值分析\n\n暂无用户数据"

    seg_counts = rfm_df["segment"].value_counts()
    total = len(rfm_df)

    lines = ["## 六、用户价值分析（RFM 模型）"]
    lines.append("")
    lines.append(f"共 {total} 位用户，按消费间隔(R)、频次(F)、金额(M)三维打分后分为以下群体：")
    lines.append("")

    # Table
    lines.append("| 用户分层 | 人数 | 占比 | 运营策略 |")
    lines.append("|:--------|:----|:----|:--------|")
    for seg, cnt in seg_counts.items():
        pct = cnt / total * 100
        strategies = {
            "重要价值": "维护VIP，专属折扣",
            "潜力客户": "推荐高客单价新品",
            "重要保持": "定向发放回归优惠券",
            "新客户": "首单3天内引导复购",
            "重要挽留": "大力度折扣 + 人工触达",
            "一般价值": "常规运营维持活跃",
            "流失高价值": "电话/短信重点挽回",
            "流失客户": "低成本触达",
            "普通客户": "常规营销推送",
        }
        strategy = strategies.get(seg, "—")
        lines.append(f"| {seg} | {cnt} | {pct:.1f}% | {strategy} |")

    at_risk = rfm_df[rfm_df["segment"].isin(["重要挽留", "流失高价值"])]
    if len(at_risk) > 0:
        lines.append(f"\n> ⚠ **重点关注**：{len(at_risk)} 位高价值客户存在流失风险，建议优先安排召回动作。")

    return "\n".join(lines)


def _section_forecast(forecast_result: pd.DataFrame) -> str:
    if forecast_result.empty:
        return "## 七、营收预测\n\n暂无预测数据"

    next_7 = forecast_result.head(7)
    avg_pred = next_7["predicted"].mean()
    total_pred = next_7["predicted"].sum()
    low = next_7["lower_bound"].mean()
    high = next_7["upper_bound"].mean()
    first_pred = next_7["predicted"].iloc[0]
    last_pred = next_7["predicted"].iloc[-1]

    if last_pred > first_pred * 1.05:
        trend = "上升 ↗"
    elif last_pred < first_pred * 0.95:
        trend = "下降 ↘"
    else:
        trend = "平稳 →"

    return f"""## 七、营收预测

| 预测指标 | 数值 |
|:--------|:-----|
| 未来7天预测总营收 | **¥{total_pred:,.0f}** |
| 预测日均营收 | ¥{avg_pred:,.0f} |
| 95% 置信区间 | ¥{low:,.0f} ~ ¥{high:,.0f} |
| 趋势方向 | {trend} |
| 预测方法 | 随机森林回归 + 时间特征工程 |

> 建议：以上界值做安全库存备案，下界值做最坏情况预案。
"""


def _section_recommendations(
    product_analysis: Dict,
    assoc_rules: pd.DataFrame,
    rfm_df: pd.DataFrame,
) -> str:
    recs = []
    n = 1

    if not assoc_rules.empty and len(assoc_rules) > 0:
        best = assoc_rules.iloc[0]
        recs.append(f"{n}. **套餐组合建议**：{best['recommendation']}")
        n += 1

    if not rfm_df.empty:
        at_risk = rfm_df[rfm_df["segment"].isin(["重要挽留", "流失高价值"])]
        if len(at_risk) > 0:
            recs.append(f"{n}. **用户召回建议**：{len(at_risk)} 位高价值客户有流失风险，建议定向推送满减优惠券或人工联系。")
            n += 1

    slow = product_analysis.get("slow_movers", pd.DataFrame())
    if not slow.empty:
        worst = slow.iloc[0]
        recs.append(f"{n}. **菜单优化建议**：「{worst['product_name']}」销量垫底，建议打折清仓或替换为新品。")
        n += 1

    if not recs:
        return "## 八、经营建议\n\n数据量尚不充分，建议积累更多历史数据后再进行分析。"

    return "## 八、经营建议\n\n" + "\n\n".join(recs)


def _report_footer(overview: Dict) -> str:
    dr = overview.get('date_range', '————')
    return f"""
---

> 本报告由「餐饮多平台经营数据分析系统」自动生成
> 分析周期：{dr}
> 数据科学与大数据技术 · 个人项目
"""
