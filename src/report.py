"""
智能报告生成模块
将分析结果转化为自然语言，输出商家可读的经营诊断报告

面试亮点：
- 数据分析闭环：图表 → 文字 → 可执行建议
- 模板化 + 数据驱动的自然语言生成
"""

from typing import Dict, Any, List
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
    生成完整的经营诊断报告（Markdown 格式）
    """
    sections = []

    # ===== 1. 总体概览 =====
    sections.append(_section_overview(overview))

    # ===== 2. 异常提醒 =====
    sections.append(_section_anomalies(overview, anomaly_orders))

    # ===== 3. 商品分析 =====
    sections.append(_section_products(product_analysis, assoc_rules))

    # ===== 4. 用户洞察 =====
    sections.append(_section_users(rfm_df))

    # ===== 5. 预测展望 =====
    sections.append(_section_forecast(forecast_result))

    # ===== 6. 经营建议 =====
    sections.append(_section_recommendations(product_analysis, assoc_rules, rfm_df))

    return "\n\n".join(sections)


def _section_overview(overview: Dict) -> str:
    o = overview
    stats = o.get("revenue_stats", {})

    return f"""## 📊 经营概览

| 指标 | 数值 |
|------|------|
| 总营收 | ¥{o['total_revenue']:,.2f} |
| 总订单数 | {o['total_orders']:,} |
| 客单价 | ¥{o['avg_order_value']:,.2f} |
| 退款率 | {o['refund_rate']:.1f}% |
| 平均折扣率 | {o['avg_discount_rate']:.1f}% |
| 分析周期 | {o.get('date_range', 'N/A')} |
| 顾客总数 | {o.get('n_customers', 'N/A'):,} |

**今日经营：**
- 今日营收：¥{o['today_revenue']:,.2f}
- 今日订单：{o['today_orders']:,}
- 较昨日{'增长' if o['dod_change'] >= 0 else '下降'}：{abs(o['dod_change']):.1f}%

**营收分布特征：**
- 日均营收均值：¥{stats.get('mean', 'N/A'):,.2f}，中位数：¥{stats.get('median', 'N/A'):,.2f}
- 偏度：{stats.get('skewness', 'N/A')}（{'右偏，说明少数高峰日拉高了均值' if stats.get('skewness', 0) > 0.5 else '分布较对称' if abs(stats.get('skewness', 0)) <= 0.5 else '左偏'}）
"""


def _section_anomalies(overview: Dict, anomaly_orders: pd.DataFrame) -> str:
    n_anomalies = anomaly_orders["is_anomaly"].sum() if len(anomaly_orders) > 0 else 0

    lines = [f"## ⚠️ 异常提醒\n"]

    if n_anomalies > 0:
        lines.append(f"- **{n_anomalies} 笔订单**被孤立森林算法检测为异常，建议核查是否存在刷单或数据录入错误")

    # 退款率检查
    if overview["refund_rate"] > 5:
        lines.append(f"- 退款率 {overview['refund_rate']:.1f}%，偏高，建议分析退款原因分布")
    else:
        lines.append(f"- 退款率 {overview['refund_rate']:.1f}%，在正常范围")

    # 日环比大幅波动
    dod = abs(overview.get("dod_change", 0))
    if dod > 30:
        lines.append(f"- 日环比波动 {dod:.1f}%，属异常波动，请关注是否有活动结束或竞品促销")

    return "\n".join(lines)


def _section_products(product_analysis: Dict, assoc_rules: pd.DataFrame) -> str:
    ranking = product_analysis.get("product_ranking", pd.DataFrame())
    slow = product_analysis.get("slow_movers", pd.DataFrame())

    lines = [f"## 🍳 商品分析\n"]

    if not ranking.empty:
        top5 = ranking.head(5)
        lines.append("**畅销 Top 5：**")
        for _, row in top5.iterrows():
            lines.append(f"- {row['product_name']}：售出 {int(row['total_sold'])} 份，营收 ¥{row['total_revenue']:,.2f}")

    if not slow.empty:
        lines.append(f"\n**滞销关注（销量末尾20%）：**")
        for _, row in slow.iterrows():
            lines.append(f"- {row['product_name']}：仅售 {int(row['total_sold'])} 份，建议评估是否下架或促销清库存")

    if not assoc_rules.empty:
        top_assoc = assoc_rules.head(3)
        lines.append(f"\n**最佳搭配建议：**")
        for _, row in top_assoc.iterrows():
            lines.append(f"- {row['recommendation']}")

    return "\n".join(lines)


def _section_users(rfm_df: pd.DataFrame) -> str:
    if rfm_df.empty:
        return "## 👤 用户分析\n\n暂无用户数据"

    seg_counts = rfm_df["segment"].value_counts()

    lines = [f"## 👤 用户洞察\n"]

    lines.append("**用户分层分布：**")
    for seg, count in seg_counts.items():
        lines.append(f"- {seg}：{count} 人")

    # 重点关注群体
    at_risk_keywords = ["重要挽留", "流失高价值", "重要保持"]
    at_risk = rfm_df[rfm_df["segment"].isin(at_risk_keywords)]
    if len(at_risk) > 0:
        lines.append(f"\n- 需关注用户：{len(at_risk)} 位（重要挽留/流失高价值/重要保持），建议定向召回")

    new_customers = rfm_df[rfm_df["segment"] == "新客户"]
    if len(new_customers) > 0:
        lines.append(f"- 新客户：{len(new_customers)} 位，建议在首单后 3 天内触达引导复购")

    return "\n".join(lines)


def _section_forecast(forecast_result: pd.DataFrame) -> str:
    if forecast_result.empty:
        return ""

    next_7 = forecast_result.head(7)
    avg_pred = next_7["predicted"].mean()
    low = next_7["lower_bound"].mean()
    high = next_7["upper_bound"].mean()

    lines = [f"## 🔮 预测展望\n"]

    lines.append(f"- 未来 7 天预计日均营收：¥{avg_pred:,.2f}")
    lines.append(f"- 预测区间（95% 置信）：¥{low:,.2f} ~ ¥{high:,.2f}")

    # 趋势判断
    first_pred = next_7["predicted"].iloc[0]
    last_pred = next_7["predicted"].iloc[-1]
    if last_pred > first_pred * 1.05:
        lines.append("- 趋势判断：**上升**趋势，可适当增加备货 ⬆️")
    elif last_pred < first_pred * 0.95:
        lines.append("- 趋势判断：**下降**趋势，建议关注竞品或准备促销活动 ⬇️")
    else:
        lines.append("- 趋势判断：**平稳**，维持常规运营节奏 ➡️")

    return "\n".join(lines)


def _section_recommendations(
    product_analysis: Dict,
    assoc_rules: pd.DataFrame,
    rfm_df: pd.DataFrame,
) -> str:
    lines = ["## 💡 经营建议\n"]

    rec_id = 1

    # 1. 关联规则建议
    if not assoc_rules.empty:
        best = assoc_rules.iloc[0]
        lines.append(f"{rec_id}. **套餐组合**：{best['recommendation']}")
        rec_id += 1

    # 2. 用户召回建议
    if not rfm_df.empty:
        at_risk = rfm_df[rfm_df["segment"].isin(["重要挽留", "流失高价值"])]
        if len(at_risk) > 0:
            lines.append(f"{rec_id}. **用户召回**：{len(at_risk)} 位高价值客户有流失风险，建议定向推送满减优惠券")
            rec_id += 1

    # 3. 滞销品处理
    slow = product_analysis.get("slow_movers", pd.DataFrame())
    if not slow.empty:
        worst = slow.iloc[0]
        pname = worst['product_name']
        lines.append(f"{rec_id}. **清库存**: 「{pname}」销量垫底，建议打折清仓或替换为新品")
        rec_id += 1

    # 4. 退款处理
    ranking = product_analysis.get("product_ranking", pd.DataFrame())
    if not ranking.empty:
        high_refund = ranking[ranking["refund_count"] > ranking["refund_count"].median() * 2]
        if len(high_refund) > 0:
            pname2 = high_refund.iloc[0]["product_name"]
            lines.append(f"{rec_id}. **品质改进**: 「{pname2}」退款率偏高，建议检查菜品品质或出餐流程")
            rec_id += 1

    if rec_id == 1:
        lines.append("数据量不足，尚无法生成具体建议。请上传更多历史数据。")

    return "\n".join(lines)
