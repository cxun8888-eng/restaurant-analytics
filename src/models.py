"""
机器学习模型模块
负责：关联规则 / 聚类 / 时序预测 / 异常检测

面试亮点：
- Apriori 算法实现购物篮分析（Support/Confidence/Lift）
- K-Means 聚类验证 RFM 分层
- 多模型时间序列回测（自动选择误差更低的预测方法）
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

    if rfm_df.empty:
        return rfm_df.copy(), {"centers": pd.DataFrame(), "inertia": None}
    n_clusters = max(1, min(int(n_clusters), len(rfm_df)))
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


_FORECAST_FEATURES = [
    "day_num", "month", "is_weekend", "day_of_month",
    "lag_1", "lag_2", "lag_3", "lag_7",
    "rolling_mean_7", "rolling_std_7",
] + [f"wd_{weekday}" for weekday in range(7)]

_FORECAST_METHODS = {
    "random_forest": "随机森林回归",
    "gradient_boosting": "梯度提升回归",
    "weekly_seasonal": "七日周期基线",
    "moving_average": "近 7 日移动平均",
}


def _forecast_features(pred_date: pd.Timestamp, day_num: int, history: List[float]) -> Dict[str, float]:
    """只使用预测日之前的数据构造特征，避免把当天答案泄漏给模型。"""
    recent = np.asarray(history[-7:], dtype=float)
    features = {
        "day_num": day_num,
        "month": pred_date.month,
        "is_weekend": 1 if pred_date.weekday() >= 5 else 0,
        "day_of_month": pred_date.day,
        "lag_1": history[-1],
        "lag_2": history[-2],
        "lag_3": history[-3],
        "lag_7": history[-7],
        "rolling_mean_7": float(recent.mean()),
        "rolling_std_7": float(recent.std()),
    }
    features.update({f"wd_{weekday}": int(pred_date.weekday() == weekday) for weekday in range(7)})
    return features


def _forecast_training_frame(dates: List[pd.Timestamp], values: List[float], end: Optional[int] = None) -> Tuple[pd.DataFrame, np.ndarray]:
    stop = len(values) if end is None else end
    rows = [_forecast_features(dates[index], index, values[:index]) for index in range(7, stop)]
    return pd.DataFrame(rows, columns=_FORECAST_FEATURES), np.asarray(values[7:stop], dtype=float)


def _make_forecast_model(method_key: str):
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor

    if method_key == "random_forest":
        return RandomForestRegressor(
            n_estimators=160,
            max_depth=6,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
    if method_key == "gradient_boosting":
        return GradientBoostingRegressor(
            n_estimators=140,
            learning_rate=0.04,
            max_depth=2,
            loss="huber",
            random_state=42,
        )
    return None


def _recursive_forecast(method_key: str, model, dates: List[pd.Timestamp], history: List[float], start_day_num: int) -> List[float]:
    predictions: List[float] = []
    rolling_history = [float(value) for value in history]
    for offset, pred_date in enumerate(dates):
        if method_key == "weekly_seasonal":
            pred = rolling_history[-7]
        elif method_key == "moving_average":
            pred = float(np.mean(rolling_history[-7:]))
        else:
            features = _forecast_features(pred_date, start_day_num + offset, rolling_history)
            pred = float(model.predict(pd.DataFrame([features], columns=_FORECAST_FEATURES))[0])
        pred = max(0.0, pred)
        predictions.append(pred)
        rolling_history.append(pred)
    return predictions


def _smape(actual: np.ndarray, predicted: np.ndarray) -> float:
    denominator = np.abs(actual) + np.abs(predicted)
    ratio = np.divide(2 * np.abs(actual - predicted), denominator, out=np.zeros_like(actual, dtype=float), where=denominator > 1e-9)
    return float(np.mean(ratio) * 100)


def run_smart_forecast(
    daily_df: pd.DataFrame,
    forecast_days: int = 14,
) -> Tuple[pd.DataFrame, Optional[Dict]]:
    """按时间顺序回测多个候选算法，自动采用误差更低的方法预测未来营收。"""
    df = daily_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    rev_col = "total_revenue" if "total_revenue" in df.columns else "revenue"
    df[rev_col] = pd.to_numeric(df[rev_col], errors="coerce").fillna(0).clip(lower=0)

    # 至少要有 7 天历史才能比较两种稳健基线；更短的数据只能给出提示性均值。
    if len(df) < 8:
        return _simple_sma_forecast(df, rev_col, forecast_days)

    dates = list(df["date"])
    values = [float(value) for value in df[rev_col]]
    # 小样本保留最近可用的一段做回测；数据充足时固定留出至少 7 天。
    validation_days = min(7, len(df) - 7) if len(df) < 21 else min(14, max(7, len(df) // 5))
    train_end = len(df) - validation_days
    X_train, y_train = _forecast_training_frame(dates, values, train_end)
    validation_dates = dates[train_end:]
    actual = np.asarray(values[train_end:], dtype=float)
    candidate_scores = []
    validation_predictions: Dict[str, List[float]] = {}
    candidate_method_keys = ["weekly_seasonal", "moving_average"]
    # 时间特征模型至少需要 7 条可训练样本；不足时仍然比较两个周期基线。
    if train_end - 7 >= 7:
        candidate_method_keys = list(_FORECAST_METHODS)

    for method_key in candidate_method_keys:
        model = _make_forecast_model(method_key)
        if model is not None:
            model.fit(X_train, y_train)
        predicted = _recursive_forecast(method_key, model, validation_dates, values[:train_end], train_end)
        predicted_array = np.asarray(predicted, dtype=float)
        candidate_scores.append({
            "key": method_key,
            "method": _FORECAST_METHODS[method_key],
            "smape": round(_smape(actual, predicted_array), 2),
            "mae": round(float(np.mean(np.abs(actual - predicted_array))), 2),
        })
        validation_predictions[method_key] = predicted

    candidate_scores.sort(key=lambda item: (item["smape"], item["mae"]))
    selected = candidate_scores[0]
    selected_key = selected["key"]
    for score in candidate_scores:
        score["selected"] = score["key"] == selected_key

    final_model = _make_forecast_model(selected_key)
    if final_model is not None:
        X_full, y_full = _forecast_training_frame(dates, values)
        final_model.fit(X_full, y_full)

    last_date = df["date"].max()
    future_dates = [last_date + timedelta(days=offset) for offset in range(1, forecast_days + 1)]
    future_predictions = _recursive_forecast(selected_key, final_model, future_dates, values, len(values))

    validation_residuals = actual - np.asarray(validation_predictions[selected_key], dtype=float)
    residual_std = float(validation_residuals.std(ddof=1)) if len(validation_residuals) > 1 else 0.0
    # 即使历史走势完全平稳，也保留一个小范围，避免把点预测误解成确定结果。
    residual_std = max(residual_std, float(np.mean(values[-7:])) * 0.05)
    predictions = []
    for index, (pred_date, pred) in enumerate(zip(future_dates, future_predictions)):
        uncertainty = 1.96 * residual_std * np.sqrt(1 + index * 0.04)
        predictions.append({
            "date": pred_date.strftime("%Y-%m-%d"),
            "predicted": round(pred, 2),
            "lower_bound": round(max(0, pred - uncertainty), 2),
            "upper_bound": round(pred + uncertainty, 2),
        })

    return pd.DataFrame(predictions), {
        "selection_mode": "智能选择" if len(candidate_method_keys) > 2 else "智能选择（数据较少）",
        "method": selected["method"],
        "method_key": selected_key,
        "validation_smape": selected["smape"],
        "validation_mae": selected["mae"],
        "validation_days": validation_days,
        "candidate_scores": candidate_scores,
        "forecast_days": forecast_days,
        "n_features": len(_FORECAST_FEATURES) if final_model is not None else 1,
        "residual_std": round(residual_std, 2),
        "selection_note": f"按最近 {validation_days} 天回测，对比 {len(candidate_scores)} 种方法后自动采用误差更低的方法。",
    }


def run_prophet_forecast(
    daily_df: pd.DataFrame,
    forecast_days: int = 14,
) -> Tuple[pd.DataFrame, Optional[Dict]]:
    """兼容旧调用；实际执行智能多模型选择。"""
    return run_smart_forecast(daily_df, forecast_days)


def _simple_sma_forecast(df, rev_col, forecast_days):
    """数据量不够时使用近 7 日移动平均，并在元数据中明确说明。"""
    recent = df.tail(7)
    avg = float(recent[rev_col].mean()) if not recent.empty else 0.0
    last_date = df["date"].max() if not df.empty else pd.Timestamp.today().normalize()
    result = pd.DataFrame({
        "date": [(last_date + timedelta(days=i + 1)).strftime("%Y-%m-%d") for i in range(forecast_days)],
        "predicted": [round(avg, 2)] * forecast_days,
        "lower_bound": [round(max(0, avg * 0.85), 2)] * forecast_days,
        "upper_bound": [round(avg * 1.15, 2)] * forecast_days,
    })
    return result, {
        "selection_mode": "智能选择（数据不足）",
        "method": _FORECAST_METHODS["moving_average"],
        "method_key": "moving_average",
        "validation_smape": None,
        "validation_mae": None,
        "validation_days": 0,
        "candidate_scores": [{"key": "moving_average", "method": _FORECAST_METHODS["moving_average"], "smape": None, "mae": None, "selected": True}],
        "forecast_days": forecast_days,
        "selection_note": "历史数据不足 8 天，暂用近 7 日平均值作为稳健参考。",
    }


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

    # 按订单聚合特征，同时保留诊断页需要的人类可读上下文。
    order_features = df_orders.groupby("order_id").agg(
        total_amount=("actual_amount", "sum"),
        item_count=("product_name", "nunique"),
        total_quantity=("quantity", "sum"),
        avg_unit_price=("unit_price", "mean"),
        discount_total=("discount", "sum"),
        order_date=("date", "first"),
        platform=("platform", "first"),
        products=("product_name", lambda values: "、".join(dict.fromkeys(values.astype(str)))[:120]),
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

    # 机器学习负责发现“组合起来不寻常”的订单；极小数据集只采用稳健阈值。
    if len(order_features) >= 5:
        iso = IsolationForest(contamination=min(0.05, max(1 / len(order_features), 0.01)), random_state=42)
        order_features["anomaly_label"] = iso.fit_predict(X)
        order_features["anomaly_score"] = iso.score_samples(X)
    else:
        order_features["anomaly_label"] = 1
        order_features["anomaly_score"] = 0.0

    def robust_bounds(series: pd.Series, lower: bool = True) -> tuple[float, float]:
        clean = pd.to_numeric(series, errors="coerce").dropna()
        if clean.empty:
            return 0.0, 0.0
        q1, q3 = clean.quantile([0.25, 0.75])
        spread = float(q3 - q1)
        floor = max(0.0, float(q1 - 1.5 * spread)) if lower else float("-inf")
        ceiling = float(q3 + 1.5 * spread)
        return floor, ceiling

    amount_low, amount_high = robust_bounds(order_features["total_amount"])
    _, quantity_high = robust_bounds(order_features["total_quantity"], lower=False)
    _, discount_high = robust_bounds(order_features["discount_total"], lower=False)

    anomaly_types: list[str] = []
    anomaly_reasons: list[str] = []
    rule_flags: list[bool] = []
    severities: list[str] = []
    for row in order_features.itertuples(index=False):
        types: list[str] = []
        reasons: list[str] = []
        amount = float(row.total_amount or 0)
        quantity = float(row.total_quantity or 0)
        discount = float(row.discount_total or 0)
        if amount > amount_high:
            types.append("金额异常")
            reasons.append(f"实付金额 ¥{amount:,.2f}，高于常规上限 ¥{amount_high:,.2f}")
        elif amount < amount_low:
            types.append("金额异常")
            reasons.append(f"实付金额 ¥{amount:,.2f}，低于常规下限 ¥{amount_low:,.2f}")
        if quantity > quantity_high:
            types.append("数量异常")
            reasons.append(f"商品数量 {quantity:g} 份，高于常规上限 {quantity_high:g} 份")
        if discount > max(0.0, discount_high):
            types.append("折扣异常")
            reasons.append(f"优惠金额 ¥{discount:,.2f}，高于常规上限 ¥{discount_high:,.2f}")

        model_flag = int(row.anomaly_label) == -1
        if model_flag and not types:
            types.append("组合异常")
            reasons.append("金额、数量、单价和折扣的组合明显偏离大多数订单")
        rule_flag = bool(types)
        anomaly_types.append("、".join(types))
        anomaly_reasons.append("；".join(reasons))
        rule_flags.append(rule_flag)
        severities.append("高" if len(types) >= 2 else "中")

    order_features["anomaly_types"] = anomaly_types
    order_features["anomaly_reason"] = anomaly_reasons
    order_features["severity"] = severities
    order_features["is_anomaly"] = (order_features["anomaly_label"] == -1) | pd.Series(rule_flags, index=order_features.index)

    return order_features


# ==================== 辅助函数 ====================


def find_optimal_k(rfm_df: pd.DataFrame, max_k: int = 8) -> pd.DataFrame:
    """
    使用肘部法则计算不同 K 值下的 SSE
    """
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans

    if len(rfm_df) < 2:
        return pd.DataFrame(columns=["k", "inertia"])
    max_k = max(1, min(int(max_k), len(rfm_df)))
    features = rfm_df[["recency", "frequency", "monetary"]]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    results = []
    for k in range(1, max_k + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        results.append({"k": k, "inertia": round(km.inertia_, 2)})

    return pd.DataFrame(results)
