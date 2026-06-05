"""
数据管道模块 (ETL)
负责：数据加载、Schema 校验、缺失值处理、异常值检测、数据标准化

面试亮点：
- 多平台数据（美团/微信/饿了么）自动识别和标准化
- IQR 方法检测异常订单
- 数据质量报告
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import io


class DataPipeline:
    """
    数据管道：原始 CSV/Excel → 清洗后的分析就绪数据

    使用方式:
        pipeline = DataPipeline()
        df_orders, quality_report = pipeline.run(file_bytes, filename)
    """

    # 各平台可能的列名映射（用于自动识别）
    COLUMN_ALIASES = {
        "order_id": ["order_id", "订单编号", "orderId", "订单号", "ordernum"],
        "order_time": ["order_time", "下单时间", "orderTime", "时间", "pay_time", "支付时间", "完成时间"],
        "customer_id": ["customer_id", "用户编号", "customerId", "会员编号", "user_id", "openid"],
        "product_name": ["product_name", "商品名称", "food_name", "菜品名称", "productName"],
        "category": ["category", "品类", "分类", "product_category", "category_name"],
        "quantity": ["quantity", "数量", "qty", "num"],
        "unit_price": ["unit_price", "单价", "price", "unitPrice"],
        "total_amount": ["total_amount", "总金额", "total", "amount", "原价"],
        "discount": ["discount", "优惠金额", "discount_amount", "立减", "红包"],
        "actual_amount": ["actual_amount", "实付金额", "actualAmount", "实际支付", "pay_amount"],
        "platform": ["platform", "平台", "source", "来源", "platform_name"],
        "status": ["status", "状态", "订单状态", "order_status"],
    }

    def __init__(self):
        self.quality_report = {}
        self.anomaly_indices = []  # 异常订单的行索引

    def run(self, file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, Dict]:
        """
        执行完整的数据管道

        Parameters
        ----------
        file_bytes : bytes
            上传文件的字节内容
        filename : str
            文件名（用于判断 CSV 还是 Excel）

        Returns
        -------
        Tuple[pd.DataFrame, Dict]
            (清洗后的 DataFrame, 数据质量报告)
        """
        # 1. 加载
        df_raw = self._load_data(file_bytes, filename)

        # 2. 列名标准化
        df = self._normalize_columns(df_raw)

        # 3. 数据校验
        df, validation_issues = self._validate(df)

        # 4. 数据清洗
        df = self._clean(df)

        # 5. 异常检测
        df, anomalies = self._detect_anomalies(df)

        # 6. 生成质量报告
        self._build_quality_report(
            raw_rows=len(df_raw),
            clean_rows=len(df),
            validation_issues=validation_issues,
            anomalies=anomalies,
        )

        return df, self.quality_report

    def _load_data(self, file_bytes: bytes, filename: str) -> pd.DataFrame:
        """加载 CSV 或 Excel 文件"""
        ext = filename.lower().split(".")[-1]

        if ext == "csv":
            # 尝试多种编码
            for enc in ["utf-8", "utf-8-sig", "gbk", "gb2312"]:
                try:
                    return pd.read_csv(io.BytesIO(file_bytes), encoding=enc)
                except (UnicodeDecodeError, UnicodeError):
                    continue
            raise ValueError("无法读取 CSV 文件，请检查文件编码")

        elif ext in ["xlsx", "xls"]:
            return pd.read_excel(io.BytesIO(file_bytes))

        else:
            raise ValueError(f"不支持的文件格式: {ext}，请上传 CSV 或 Excel 文件")

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """将不同平台的列名统一为标准列名"""
        rename_map = {}

        for standard_name, aliases in self.COLUMN_ALIASES.items():
            for col in df.columns:
                col_lower = col.strip().lower()
                if col_lower in [a.lower() for a in aliases]:
                    rename_map[col] = standard_name
                    break

        df = df.rename(columns=rename_map)
        return df

    def _validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        数据校验：
        - 必填字段检查
        - 日期格式标准化
        - 数值非负检查
        """
        issues = []

        # --- 必填字段 ---
        required_fields = ["order_id", "product_name", "total_amount"]
        for field in required_fields:
            if field not in df.columns:
                issues.append(f"缺少必填字段: {field}")

        # --- 日期标准化 ---
        if "order_time" in df.columns:
            df["order_time"] = pd.to_datetime(df["order_time"], errors="coerce")
            df["date"] = df["order_time"].dt.strftime("%Y-%m-%d")
            df["hour"] = df["order_time"].dt.hour
            df["weekday"] = df["order_time"].dt.weekday
            df["is_weekend"] = df["weekday"].isin([5, 6]).astype(int)

            n_bad_dates = df["order_time"].isna().sum()
            if n_bad_dates > 0:
                issues.append(f"{n_bad_dates} 行日期解析失败，已标记为缺失")

        # --- 数值字段类型转换 + 非负检查 ---
        numeric_checks = {
            "quantity": "数量",
            "unit_price": "单价",
            "total_amount": "总金额",
            "actual_amount": "实付金额",
            "discount": "优惠金额",
            "refund_amount": "退款金额",
        }
        for col, name in numeric_checks.items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    issues.append(f"{name}({col}) 有 {negative_count} 行负值，已替换为 0")
                    df[col] = df[col].clip(lower=0)

        # --- 检查平台字段 ---
        if "platform" not in df.columns:
            df["platform"] = "未知平台"
            issues.append("未识别到平台字段，已标记为'未知平台'")

        return df, issues

    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗缺失值、去重"""

        # 去掉完全重复的行
        n_before = len(df)
        df = df.drop_duplicates()
        n_after = len(df)
        if n_before > n_after:
            self.quality_report["duplicates_removed"] = n_before - n_after

        # 填补缺失值
        if "category" in df.columns:
            df["category"] = df["category"].fillna("其他")

        if "quantity" in df.columns:
            df["quantity"] = df["quantity"].fillna(1)

        if "unit_price" in df.columns:
            df["unit_price"] = df["unit_price"].fillna(df["total_amount"] / df["quantity"])

        if "total_amount" in df.columns and "actual_amount" in df.columns:
            df["actual_amount"] = df["actual_amount"].fillna(df["total_amount"])

        if "discount" in df.columns:
            df["discount"] = df["discount"].fillna(0.0)

        if "refund_amount" in df.columns:
            df["refund_amount"] = df["refund_amount"].fillna(0.0)

        # 构造缺失的关键列
        if "actual_amount" not in df.columns and "total_amount" in df.columns and "discount" in df.columns:
            df["actual_amount"] = df["total_amount"] - df["discount"]

        if "status" not in df.columns:
            df["status"] = "completed"

        if "customer_id" not in df.columns:
            # 没有顾客ID时，用订单ID兜底（影响 RFM 分析）
            df["customer_id"] = df["order_id"]
            self.quality_report["missing_customer_id"] = True

        return df

    def _detect_anomalies(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        异常检测（IQR 方法）

        检测维度：
        - 订单金额异常高（可能是刷单/大单）
        - 订单金额异常低（可能是测试订单）
        - 数量异常大
        """
        anomalies = {}

        if "actual_amount" in df.columns:
            # 按订单聚合
            order_amounts = df.groupby("order_id")["actual_amount"].sum()

            Q1 = order_amounts.quantile(0.25)
            Q3 = order_amounts.quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            anomalous_orders = order_amounts[
                (order_amounts < lower_bound) | (order_amounts > upper_bound)
            ]

            anomalies["amount_outliers"] = {
                "method": "IQR",
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
                "n_outliers": len(anomalous_orders),
                "outlier_order_ids": anomalous_orders.index.tolist(),
            }

            # 标记到 DataFrame
            outlier_set = set(anomalous_orders.index.tolist())
            df["is_anomaly"] = df["order_id"].apply(lambda x: x in outlier_set)

        # 数量异常
        if "quantity" in df.columns:
            qty_upper = df["quantity"].quantile(0.99)
            n_qty_outliers = (df["quantity"] > qty_upper).sum()
            anomalies["quantity_outliers"] = {
                "threshold": int(qty_upper),
                "n_outliers": int(n_qty_outliers),
            }

        return df, anomalies

    def _build_quality_report(
        self,
        raw_rows: int,
        clean_rows: int,
        validation_issues: List[str],
        anomalies: Dict,
    ):
        """组装数据质量报告"""
        self.quality_report = {
            "raw_rows": raw_rows,
            "clean_rows": clean_rows,
            "total_orders": 0,  # 将在 analysis 中填充
            "date_range": "",
            "issues": validation_issues,
            "anomalies": anomalies,
            "missing_customer_id": self.quality_report.get("missing_customer_id", False),
            "duplicates_removed": self.quality_report.get("duplicates_removed", 0),
        }


# ===== 便捷函数 =====

def load_sample_data(orders_path: str = "sample_data/sample_orders.csv") -> pd.DataFrame:
    """加载项目内置的模拟数据"""
    return pd.read_csv(orders_path, parse_dates=["order_time"])


def summarize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成数据集的统计摘要（类似 df.describe() 但更详细）
    返回 DataFrame 可直接展示
    """
    summary = df.describe(include="all").T
    summary["dtype"] = df.dtypes.values
    summary["missing"] = df.isnull().sum().values
    summary["missing_pct"] = (df.isnull().sum() / len(df) * 100).round(2).values
    summary["nunique"] = df.nunique().values
    return summary
