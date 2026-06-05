"""
机器学习模型模块
负责：关联规则 / 聚类 / 时序预测 / 异常检测

面试亮点：
- Apriori 算法实现购物篮分析（Support/Confidence/Lift）
- K-Means 聚类验证 RFM 分层
- Prophet 时间序列预测（自动处理周期性和节假日）
- Isolation Forest 异常检测
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta


# ==================== 关联规则 ====================


def run_apriori(
    df_orders: pd.DataFrame,
    min_support: float = 0.01,
    min_lift: float = 1.0,
    top_n: int = 30,
) -> pd.DataFrame:
    """
    购物篮关联规则挖掘（Apriori 算法）

    Parameters
    ----------
    df_orders : 订单明细（须包含 order_id, product_name）
    min_support : 最小支持度（商品组合占总订单的比例）
    min_lift : 最小提升度
    top_n : 返回前 N 条规则

    Returns
    -------
    pd.DataFrame
        关联规则表：antecedent, consequent, support, confidence, lift, 建议
    """
    from mlxtend.frequent_patterns import apriori, association_rules

    # 1. 构建订单-商品 one-hot 矩阵
    basket = df_orders.pivot_table(
        index="order_id",
        columns="product_name",
        values="quantity",
        aggfunc="sum",
        fill_value=0,
    )
    basket = basket.map(lambda x: 1 if x > 0 else 0)

    # 2. 频繁项集
    frequent_itemsets = apriori(basket, min_support=min_support, use_colnames=True)

    if frequent_itemsets.empty:
        return pd.DataFrame(columns=["antecedent", "consequent", "support", "confidence", "lift", "recommendation"])

    # 3. 关联规则
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_lift)
    rules = rules.sort_values("lift", ascending=False).head(top_n)

    # 4. 整理输出
    result = pd.DataFrame({
        "antecedent": rules["antecedents"].apply(lambda x: " + ".join(list(x))),
        "consequent": rules["consequents"].apply(lambda x: " + ".join(list(x))),
        "support": rules["support"].round(4),
        "confidence": rules["confidence"].round(4),
        "lift": rules["lift"].round(2),
    })

    # 5. 自动生成建议
    def make_recommendation(row):
        if row["lift"] >= 3:
            level = "强烈建议"
        elif row["lift"] >= 2:
            level = "建议"
        elif row["lift"] >= 1.5:
            level = "可考虑"
        else:
            level = "弱关联"
        return f"{level}将「{row['antecedent']}」+「{row['consequent']}」组合为套餐，Lift={row['lift']}"

    result["recommendation"] = result.apply(make_recommendation, axis=1)

    return result


# ==================== K-Means 聚类 ====================


def run_kmeans_clustering(rfm_df: pd.DataFrame, n_clusters: int = 4) -> Tuple[pd.DataFrame, Dict]:
    """
    对 RFM 特征进行 K-Means 聚类

    Parameters
    ----------
    rfm_df : 包含 R_score, F_score, M_score 的 DataFrame
    n_clusters : 聚类数

    Returns
    -------
    Tuple[pd.DataFrame, Dict]
        (带聚类标签的 DataFrame, 聚类中心信息)
    """
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans

    features = rfm_df[["recency", "frequency", "monetary"]].copy()

    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    # K-Means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    rfm_df = rfm_df.copy()
    rfm_df["cluster"] = kmeans.fit_predict(X_scaled)

    # 聚类中心（反标准化）
    centers_scaled = kmeans.cluster_centers_
    centers = scaler.inverse_transform(centers_scaled)
    centers_df = pd.DataFrame(
        centers,
        columns=["recency", "frequency", "monetary"],
    )
    centers_df.index.name = "cluster"
    centers_df = centers_df.round(1)

    # 为每个聚类命名
    cluster_profiles = []
    for i in range(n_clusters):
        row = centers_df.iloc[i]
        r_desc = "近" if row["recency"] < rfm_df["recency"].median() else "远"
        f_desc = "高" if row["frequency"] > rfm_df["frequency"].median() else "低"
        m_desc = "高" if row["monetary"] > rfm_df["monetary"].median() else "低"
        cluster_profiles.append(f"聚类{i+1}: R{r_desc}/F{f_desc}/M{m_desc}")

    centers_df["profile"] = cluster_profiles
    centers_df["count"] = rfm_df["cluster"].value_counts().sort_index().values

    return rfm_df, {"centers": centers_df, "inertia": round(kmeans.inertia_, 2)}


# ==================== 时间序列预测 ====================


def run_prophet_forecast(
    daily_df: pd.DataFrame,
    forecast_days: int = 14,
) -> Tuple[pd.DataFrame, Optional[Dict]]:
    """
    使用随机森林 + 时间特征工程预测未来营收

    方法：将时间序列转化为监督学习问题
    1. 构造特征：趋势(第几天)、星期几(one-hot)、月份、滞后特征(lag)
    2. 用随机森林回归学习历史规律
    3. 对未来每一天递归预测

    Parameters
    ----------
    daily_df : 日聚合数据（须包含 date, total_revenue 或 revenue）
    forecast_days : 预测天数

    Returns
    -------
    Tuple[pd.DataFrame, Optional[Dict]]
    """
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler

    df = daily_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # 兼容列名
    rev_col = "total_revenue" if "total_revenue" in df.columns else "revenue"
    y = df[rev_col].values

    # ===== 特征工程 =====
    n = len(df)
    df["day_num"] = np.arange(n)                          # 线性趋势
    df["weekday"] = df["date"].dt.weekday                 # 星期几 (0=周一)
    df["month"] = df["date"].dt.month                     # 月份
    df["is_weekend"] = df["weekday"].isin([5, 6]).astype(int)  # 是否周末
    df["day_of_month"] = df["date"].dt.day                # 几号

    # 滞后特征（用前几天营收预测下一天）
    for lag in [1, 2, 3, 7]:
        df[f"lag_{lag}"] = df[rev_col].shift(lag)

    # 滚动统计特征
    df["rolling_mean_7"] = df[rev_col].rolling(7, min_periods=1).mean()
    df["rolling_std_7"] = df[rev_col].rolling(7, min_periods=1).std().fillna(0)

    # 星期几 one-hot
    weekday_dummies = pd.get_dummies(df["weekday"], prefix="wd")
    df = pd.concat([df, weekday_dummies], axis=1)

    # 特征列表
    feature_cols = [
        "day_num", "month", "is_weekend", "day_of_month",
        "lag_1", "lag_2", "lag_3", "lag_7",
        "rolling_mean_7", "rolling_std_7",
    ] + [c for c in weekday_dummies.columns]

    # 去掉前7天（因为 lag_7 为 NaN）
    train_df = df.iloc[7:].copy()

    X_train = train_df[feature_cols].fillna(0)
    y_train = y[7:]

    if len(X_train) < 7:
        # 数据太少，回退到简单移动平均
        return _simple_sma_forecast(df, rev_col, forecast_days)

    # ===== 训练随机森林 =====
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled, y_train)

    # ===== 训练集评估 =====
    y_pred_train = model.predict(X_scaled)
    mape = np.mean(np.abs((y_train - y_pred_train) / (y_train + 0.01))) * 100

    # 用残差标准差估算置信区间
    residuals = y_train - y_pred_train
    residual_std = residuals.std()

    # ===== 对未来递归预测 =====
    last_known = df.iloc[-1].copy()
    last_values = {f"lag_{i}": df[rev_col].iloc[-(i)] for i in [1, 2, 3, 7]}
    rolling_window = list(df[rev_col].tail(7).values)

    last_date = df["date"].max()
    predictions = []

    for i in range(1, forecast_days + 1):
        pred_date = last_date + timedelta(days=i)

        # 构造当天特征
        features = {
            "day_num": last_known["day_num"] + i,
            "month": pred_date.month,
            "is_weekend": 1 if pred_date.weekday() >= 5 else 0,
            "day_of_month": pred_date.day,
            "lag_1": last_values["lag_1"],
            "lag_2": last_values["lag_2"],
            "lag_3": last_values["lag_3"],
            "lag_7": last_values["lag_7"],
            "rolling_mean_7": np.mean(rolling_window[-7:]),
            "rolling_std_7": np.std(rolling_window[-7:]) if len(rolling_window) >= 2 else 0,
        }
        # 星期几 one-hot
        for c in weekday_dummies.columns:
            features[c] = 0
        wd_col = f"wd_{pred_date.weekday()}"
        if wd_col in weekday_dummies.columns:
            features[wd_col] = 1

        X_new = pd.DataFrame([features])[feature_cols].fillna(0)
        X_new_scaled = scaler.transform(X_new)
        pred = model.predict(X_new_scaled)[0]

        predictions.append({
            "date": pred_date.strftime("%Y-%m-%d"),
            "predicted": round(max(0, pred), 2),
            "lower_bound": round(max(0, pred - 1.96 * residual_std), 2),
            "upper_bound": round(max(0, pred + 1.96 * residual_std), 2),
        })

        # 更新滞后值用于下一次预测
        for j in [3, 2, 1]:
            last_values[f"lag_{j+1}"] = last_values[f"lag_{j}"]
        last_values["lag_1"] = pred
        second_last_values = {f"lag_{i}": df[rev_col].iloc[-(i-1)] if i > 1 else pred for i in [1, 2, 3, 7]}
        # 更新 lag_7
        if i <= 7:
            last_values["lag_7"] = df[rev_col].iloc[-(7-i)] if 7-i < len(df) else df[rev_col].iloc[0]
        else:
            last_values["lag_7"] = predictions[i-8]["predicted"]

        rolling_window.append(pred)
        rolling_window = rolling_window[-7:]

    result = pd.DataFrame(predictions)

    return result, {
        "mape": round(mape, 2),
        "method": "随机森林回归(RandomForest)",
        "forecast_days": forecast_days,
        "n_features": len(feature_cols),
        "residual_std": round(residual_std, 2),
    }


def _simple_sma_forecast(df, rev_col, forecast_days):
    """数据量不够时的简单移动平均回退"""
    recent = df.tail(7)
    avg = recent[rev_col].mean()
    last_date = df["date"].max()

    result = pd.DataFrame({
        "date": [(last_date + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(forecast_days)],
        "predicted": [round(avg, 2)] * forecast_days,
        "lower_bound": [round(avg * 0.85, 2)] * forecast_days,
        "upper_bound": [round(avg * 1.15, 2)] * forecast_days,
    })
    return result, {"mape": None, "method": "简单移动平均(数据不足)", "forecast_days": forecast_days}


# ==================== 异常检测 ====================


def run_isolation_forest(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    使用 Isolation Forest 检测异常订单

    Parameters
    ----------
    df_orders : 订单明细

    Returns
    -------
    pd.DataFrame
        每个订单一行，包含 anomaly_score 和 is_anomaly 标记
    """
    from sklearn.ensemble import IsolationForest

    # 按订单聚合特征
    order_features = df_orders.groupby("order_id").agg(
        total_amount=("actual_amount", "sum"),
        item_count=("product_name", "nunique"),
        total_quantity=("quantity", "sum"),
        avg_unit_price=("unit_price", "mean"),
        discount_total=("discount", "sum"),
    ).reset_index()

    # 提取下单时间
    time_info = df_orders.groupby("order_id").agg(
        order_hour=("hour", "first"),
        is_weekend=("is_weekend", "first"),
    ).reset_index()

    order_features = order_features.merge(time_info, on="order_id", how="left")

    # 特征工程
    X = order_features[["total_amount", "item_count", "total_quantity", "avg_unit_price", "discount_total"]].copy()
    X = X.fillna(0)

    # 训练
    iso = IsolationForest(contamination=0.05, random_state=42)
    order_features["anomaly_label"] = iso.fit_predict(X)
    order_features["anomaly_score"] = iso.score_samples(X)

    # -1 = 异常, 1 = 正常
    order_features["is_anomaly"] = order_features["anomaly_label"] == -1

    return order_features


# ==================== 辅助函数 ====================


def find_optimal_k(rfm_df: pd.DataFrame, max_k: int = 8) -> pd.DataFrame:
    """
    使用肘部法则计算不同 K 值下的 SSE
    """
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans

    features = rfm_df[["recency", "frequency", "monetary"]]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    results = []
    for k in range(1, max_k + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        results.append({"k": k, "inertia": round(km.inertia_, 2)})

    return pd.DataFrame(results)
