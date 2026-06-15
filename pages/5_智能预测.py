"""
页面5：智能预测
时间序列预测 + 异常检测（Isolation Forest）
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.nav_style import inject_nav_css
from src.models import run_isolation_forest
from src.analysis import compute_trend_analysis
from src.visualization import forecast_chart


st.set_page_config(page_title="智能预测 | 餐饮数据分析", page_icon="🔮", layout="wide")


# ===== 预测函数：自包含在本页面，不走 models.py =====
def _forecast_revenue(daily_df: pd.DataFrame, forecast_days: int = 14):
    """
    随机森林回归 + 时间特征工程

    将时间序列转为监督学习：
    1. 构造特征：趋势、星期、月份、周末标记、滞后值、滚动统计
    2. 训练随机森林回归器
    3. 对未来逐日递归预测
    """
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from datetime import timedelta

    df = daily_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    rev_col = "total_revenue" if "total_revenue" in df.columns else "revenue"
    y = df[rev_col].values
    n = len(df)

    # ---- 特征工程 ----
    df["day_num"] = np.arange(n)
    df["weekday"] = df["date"].dt.weekday
    df["month"] = df["date"].dt.month
    df["is_weekend"] = df["weekday"].isin([5, 6]).astype(int)
    df["day_of_month"] = df["date"].dt.day

    for lag in [1, 2, 3, 7]:
        df[f"lag_{lag}"] = df[rev_col].shift(lag)

    df["rolling_mean_7"] = df[rev_col].rolling(7, min_periods=1).mean()
    df["rolling_std_7"] = df[rev_col].rolling(7, min_periods=1).std().fillna(0)

    weekday_dummies = pd.get_dummies(df["weekday"], prefix="wd")
    df = pd.concat([df, weekday_dummies], axis=1)

    feature_cols = [
        "day_num", "month", "is_weekend", "day_of_month",
        "lag_1", "lag_2", "lag_3", "lag_7",
        "rolling_mean_7", "rolling_std_7",
    ] + [c for c in weekday_dummies.columns]

    # ---- 训练 ----
    train_df = df.iloc[7:].copy()
    X_train = train_df[feature_cols].fillna(0)
    y_train = y[7:]

    if len(X_train) < 7:
        # 数据太少，用简单均值
        recent = df.tail(7)
        avg_val = recent[rev_col].mean()
        result = pd.DataFrame({
            "date": [(df["date"].max() + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(forecast_days)],
            "predicted": [round(avg_val, 2)] * forecast_days,
            "lower_bound": [round(avg_val * 0.85, 2)] * forecast_days,
            "upper_bound": [round(avg_val * 1.15, 2)] * forecast_days,
        })
        return result, {"mape": None, "method": "简单移动平均(数据不足)", "forecast_days": forecast_days}

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)

    model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1)
    model.fit(X_scaled, y_train)

    # ---- 评估 ----
    y_pred_train = model.predict(X_scaled)
    mape = np.mean(np.abs((y_train - y_pred_train) / (y_train + 0.01))) * 100
    residuals = y_train - y_pred_train
    residual_std = residuals.std()

    # ---- 递归预测未来 ----
    last_known = df.iloc[-1]
    lag_values = {f"lag_{i}": df[rev_col].iloc[-i] for i in [1, 2, 3, 7]}
    rolling_window = list(df[rev_col].tail(7).values)
    last_date = df["date"].max()
    predictions = []

    for i in range(1, forecast_days + 1):
        pred_date = last_date + timedelta(days=i)
        feats = {
            "day_num": last_known["day_num"] + i,
            "month": pred_date.month,
            "is_weekend": 1 if pred_date.weekday() >= 5 else 0,
            "day_of_month": pred_date.day,
            "lag_1": lag_values["lag_1"],
            "lag_2": lag_values["lag_2"],
            "lag_3": lag_values["lag_3"],
            "lag_7": lag_values["lag_7"],
            "rolling_mean_7": np.mean(rolling_window),
            "rolling_std_7": np.std(rolling_window) if len(rolling_window) >= 2 else 0,
        }
        for c in weekday_dummies.columns:
            feats[c] = 0
        wd_col = f"wd_{pred_date.weekday()}"
        if wd_col in weekday_dummies.columns:
            feats[wd_col] = 1

        X_new = pd.DataFrame([feats])[feature_cols].fillna(0)
        pred = model.predict(scaler.transform(X_new))[0]

        predictions.append({
            "date": pred_date.strftime("%Y-%m-%d"),
            "predicted": round(max(0, pred), 2),
            "lower_bound": round(max(0, pred - 1.96 * residual_std), 2),
            "upper_bound": round(max(0, pred + 1.96 * residual_std), 2),
        })

        # 更新滞后值和滚动窗口
        for j in [3, 2, 1]:
            lag_values[f"lag_{j+1}"] = lag_values[f"lag_{j}"]
        lag_values["lag_1"] = pred
        if i <= 7:
            lag_values["lag_7"] = df[rev_col].iloc[-(7-i)] if (7-i) < len(df) else df[rev_col].iloc[0]
        else:
            lag_values["lag_7"] = predictions[i-8]["predicted"]
        rolling_window.append(pred)
        rolling_window = rolling_window[-7:]

    result = pd.DataFrame(predictions)
    return result, {
        "mape": round(mape, 2),
        "method": "随机森林回归(RandomForest)",
        "forecast_days": forecast_days,
    }


def main():
    inject_nav_css()
    st.title("🔮 智能预测 & 异常检测")

    df = st.session_state.get("df_orders")
    if df is None:
        st.warning("请先在「数据上传」页面加载数据")
        return

    # ===== 时间序列预测 =====
    st.subheader("📈 营收预测")

    col1, col2 = st.columns([3, 1])
    with col2:
        forecast_days = st.slider("预测天数", 7, 30, 14)

    with col1:
        st.markdown("""
        > 使用 **随机森林回归 + 时间特征工程** 进行预测。
        > 将时间序列转化为监督学习：构造趋势、星期、月份、滞后值等特征，用集成学习模型学习历史规律，然后对未来递归预测。
        """)

    # 构建日聚合数据
    daily_df = compute_trend_analysis(df)

    with st.spinner(f"正在训练预测模型（未来 {forecast_days} 天）..."):
        forecast_result, forecast_meta = _forecast_revenue(daily_df, forecast_days=forecast_days)

    st.session_state["forecast_result"] = forecast_result

    if forecast_meta:
        st.caption(f"模型：{forecast_meta['method']} | 预测天数：{forecast_meta['forecast_days']}")
        if forecast_meta.get("mape"):
            st.caption(f"平均绝对百分比误差（MAPE）：{forecast_meta['mape']:.2f}%（越小越准）")

    # 预测图
    fig_fc = forecast_chart(forecast_result, historical_df=daily_df.tail(30))
    st.plotly_chart(fig_fc, use_container_width=True)

    # 预测数据表
    with st.expander("📋 预测数据明细", expanded=False):
        st.dataframe(
            forecast_result.style.background_gradient(subset=["predicted"], cmap="Blues"),
            use_container_width=True,
            column_config={
                "date": "日期",
                "predicted": st.column_config.NumberColumn("预测营收", format="¥%.2f"),
                "lower_bound": st.column_config.NumberColumn("下界(95%)", format="¥%.2f"),
                "upper_bound": st.column_config.NumberColumn("上界(95%)", format="¥%.2f"),
            },
        )

    # 统计预测指标
    next_7 = forecast_result.head(7)
    total_pred_7 = next_7["predicted"].sum()
    avg_pred_7 = next_7["predicted"].mean()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("未来7天预测总营收", f"¥{total_pred_7:,.0f}")
    with col2:
        st.metric("预测日均营收", f"¥{avg_pred_7:,.0f}")
    with col3:
        first_val = next_7["predicted"].iloc[0]
        last_val = next_7["predicted"].iloc[-1]
        trend_pct = (last_val - first_val) / first_val * 100
        st.metric("7日趋势", f"{trend_pct:+.1f}%")

    st.divider()

    # ===== 异常检测 =====
    st.subheader("🔍 异常订单检测（Isolation Forest）")

    st.markdown("""
    > **算法原理**：Isolation Forest 通过随机切分特征空间来「隔离」数据点。
    > 异常点因为稀疏，通常只需要很少的切割次数就能被隔离——就像在一群白羊中找黑羊比在一群白羊中找另一只白羊更容易。
    """)

    with st.spinner("正在运行 Isolation Forest..."):
        anomaly_df = run_isolation_forest(df)

    st.session_state["anomaly_df"] = anomaly_df

    n_anomalies = anomaly_df["is_anomaly"].sum()
    n_total = len(anomaly_df)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总订单数", f"{n_total:,}")
    with col2:
        st.metric("异常订单", f"{n_anomalies}", delta=f"{n_anomalies/n_total*100:.1f}%")
    with col3:
        avg_score = anomaly_df[anomaly_df["is_anomaly"]]["anomaly_score"].mean()
        st.metric("平均异常分数", f"{avg_score:.3f}")

    # 异常订单详情
    st.subheader("异常订单明细")
    anomalous = anomaly_df[anomaly_df["is_anomaly"]].sort_values("anomaly_score")
    st.dataframe(
        anomalous.head(20),
        use_container_width=True,
        column_config={
            "order_id": "订单编号",
            "total_amount": st.column_config.NumberColumn("实付金额", format="¥%.2f"),
            "item_count": "商品种类数",
            "total_quantity": "商品总数",
            "anomaly_score": st.column_config.NumberColumn("异常分数", format="%.4f"),
        },
    )

    # ===== 面试要点 =====
    with st.expander("📝 预测 & 异常检测面试讲解要点", expanded=False):
        st.markdown("""
        ### 随机森林时间序列预测

        **1. 为什么用随机森林？**
        > "随机森林是机器学习课的核心算法。方法上，我把时间序列转化成了监督学习——构造趋势、星期one-hot、月份、滞后值等特征，然后训练随机森林回归模型。这比调Prophet的包更能体现我的特征工程和建模能力。"

        **2. 评估指标**
        > "我用 MAPE（平均绝对百分比误差）评估预测准确度。MAPE 的优势是直观——比如 MAPE=15% 意味着平均预测偏差为 ±15%。"

        **3. 业务价值**
        > "预测不只是给一个数字，更重要的是给了置信区间。商家可以据此做备货计划和人员排班——预测值做基准，上界做安全库存，下界做最坏打算。"

        ### Isolation Forest 异常检测

        **1. 核心思想**
        > "Isolation Forest 基于一个直觉：异常点是少数且不同的，所以更容易被随机分割隔离。它在特征空间随机选切割点，计算每个点被隔离所需的切割次数。异常点需要的切割次数少（异常分数低）。"

        **2. 特征选择**
        > "我选了订单金额、商品种类数、商品总数量、平均单价、折扣金额作为检测特征。这些维度能覆盖金额异常（刷单大单）和结构异常（单一商品巨额折扣）。"

        **3. 对比 IQR**
        > "IQR 方法（页面1数据管道里用到）只能检测单维度异常（如金额过高），而 Isolation Forest 能在多维特征空间中检测复杂异常模式——比如「金额不算特别高，但只买了一种商品且折扣极大」这种组合异常。"
        """)


if __name__ == "__main__":
    main()
