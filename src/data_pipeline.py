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
import re
from difflib import SequenceMatcher


class DataPipeline:
    """
    数据管道：原始 CSV/Excel → 清洗后的分析就绪数据

    使用方式:
        pipeline = DataPipeline()
        df_orders, quality_report = pipeline.run(file_bytes, filename)
    """

    # 各平台可能的列名映射（用于自动识别）
    COLUMN_ALIASES = {
        "order_id": ["order_id", "订单编号", "订单号", "订单流水号", "流水号", "交易单号", "orderId", "ordernum", "编号"],
        "order_time": ["order_time", "date", "datetime", "created_at", "下单时间", "下单日期", "交易时间", "交易日期", "订单日期", "结算日期", "结算日", "营业日期", "orderTime", "时间", "日期", "支付日期", "pay_time", "支付时间", "完成时间", "成交时间"],
        "customer_id": ["customer_id", "用户编号", "客户编号", "会员编号", "顾客编号", "customerId", "user_id", "openid", "会员id"],
        "product_name": ["product_name", "商品名称", "商品", "菜品名称", "菜品", "品名", "项目名称", "food_name", "productName", "item_name"],
        "category": ["category", "品类", "分类", "商品分类", "菜品分类", "product_category", "category_name", "cuisine_type", "菜系", "菜系类型"],
        "quantity": ["quantity", "数量", "销量", "件数", "qty", "num", "count"],
        "unit_price": ["unit_price", "单价", "售价", "商品单价", "price", "unitPrice"],
        "total_amount": ["total_amount", "transaction_amount", "sales_amount", "cost_of_the_order", "order_cost", "cost", "总金额", "订单金额", "订单总额", "交易金额", "成交金额", "销售额", "营业额", "销售收入", "收入", "实收", "应付金额", "原价", "total", "amount", "revenue", "gmv"],
        "discount": ["discount", "优惠金额", "折扣金额", "discount_amount", "立减", "红包", "优惠"],
        "actual_amount": ["actual_amount", "实付金额", "实收金额", "实际支付", "支付金额", "到账金额", "actualAmount", "pay_amount", "paid_amount"],
        "refund_amount": ["refund_amount", "退款金额", "退款", "refund", "refundAmount"],
        "platform": ["platform", "平台", "来源平台", "渠道", "source", "来源", "platform_name"],
        "status": ["status", "状态", "订单状态", "交易状态", "order_status"],
        # 这些字段在不少平台报表中有业务价值，但不应冒充核心订单字段。
        "restaurant_name": ["restaurant_name", "餐厅名称", "餐馆名称", "门店名称", "店铺名称", "restaurant"],
        "weekday_label": ["day_of_the_week", "weekday", "week_day", "星期", "星期几", "营业日类型", "工作日类型"],
        "rating": ["rating", "评分", "星级", "用户评分", "score"],
        "preparation_time": ["food_preparation_time", "preparation_time", "备餐时长", "出餐时长", "制作时长"],
        "delivery_duration": ["delivery_time", "delivery_duration", "配送时长", "配送时间", "送餐时长"],
    }

    FIELD_LABELS = {
        "order_id": "订单号", "order_time": "订单时间", "product_name": "商品名称",
        "total_amount": "订单金额", "customer_id": "顾客编号", "category": "商品分类",
        "quantity": "数量", "unit_price": "单价", "discount": "优惠金额",
        "actual_amount": "实付金额", "refund_amount": "退款金额", "platform": "平台", "status": "订单状态",
        "restaurant_name": "餐厅名称", "weekday_label": "星期/营业日", "rating": "评分",
        "preparation_time": "备餐时长", "delivery_duration": "配送时长",
    }

    def __init__(self):
        self.quality_report = {}
        self.anomaly_indices = []  # 异常订单的行索引
        self.column_mapping = []
        self.raw_columns = []
        self.raw_sample = []
        self.raw_frame = pd.DataFrame()

    def run(self, file_bytes: bytes, filename: str, forced_mapping: Optional[Dict[str, object]] = None) -> Tuple[pd.DataFrame, Dict]:
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
        self.quality_report = {}
        self.column_mapping = []

        # 1. 加载
        df_raw = self._load_data(file_bytes, filename)
        self.raw_frame = df_raw.copy()
        self.raw_columns = [str(column) for column in df_raw.columns]
        self.raw_sample = self._representative_sample(df_raw)

        # 2. 列名标准化
        df = self._normalize_columns(df_raw, forced_mapping=forced_mapping)

        # 3. 对无法直接识别的核心字段做安全兜底，避免因列名不同而直接失败。
        df, inference_issues = self._ensure_core_fields(df)

        # 4. 数据校验
        df, validation_issues = self._validate(df)
        validation_issues = inference_issues + validation_issues

        # 5. 数据清洗
        df = self._clean(df)

        # 6. 异常检测
        df, anomalies = self._detect_anomalies(df)

        # 7. 生成质量报告
        self._build_quality_report(
            raw_rows=len(df_raw),
            clean_rows=len(df),
            validation_issues=validation_issues,
            anomalies=anomalies,
        )

        # 补充上传接口和前端都需要的基础摘要字段。
        self.quality_report["total_orders"] = int(df["order_id"].nunique()) if "order_id" in df else 0
        if "date" in df.columns and df["date"].notna().any():
            dates = df["date"].dropna().astype(str)
            self.quality_report["date_range"] = f"{dates.min()} ~ {dates.max()}"

        return df, self.quality_report

    @staticmethod
    def _representative_sample(df: pd.DataFrame, limit: int = 20) -> list[dict]:
        """Return deterministic samples from across a file for AI inspection.

        The complete frame is still processed locally.  Sampling evenly across
        the file avoids making the first few rows the sole source of truth when
        exports contain headers, blank sections, or multiple data blocks.
        """
        if df.empty:
            return []
        count = min(len(df), max(1, limit))
        positions = np.linspace(0, len(df) - 1, count, dtype=int)
        sample = df.iloc[sorted(set(int(position) for position in positions))]
        return sample.where(pd.notna(sample), None).to_dict(orient="records")

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

    def _normalize_columns(self, df: pd.DataFrame, forced_mapping: Optional[Dict[str, object]] = None) -> pd.DataFrame:
        """将不同平台的列名统一为标准列名，并推断非标准列名的业务含义。"""
        columns = list(df.columns)
        normalized = {col: self._normalize_column_name(col) for col in columns}
        aliases = {field: {self._normalize_column_name(alias) for alias in names} for field, names in self.COLUMN_ALIASES.items()}
        rename_map = {}
        used = set()

        # AI 或用户确认的映射优先级最高，后续规则识别不会覆盖它。
        for source, suggestion in (forced_mapping or {}).items():
            target = suggestion.get("field") if isinstance(suggestion, dict) else suggestion
            if source not in columns or target not in self.COLUMN_ALIASES or source in used or target in rename_map.values():
                continue
            confidence = suggestion.get("confidence", 0.8) if isinstance(suggestion, dict) else 0.8
            rename_map[source] = target
            used.add(source)
            self.column_mapping.append({"source": str(source), "field": target, "label": self.FIELD_LABELS[target], "confidence": round(float(confidence), 2), "method": "AI 辅助识别"})

        # 第一层：别名精确匹配，可信度最高。
        for field, field_aliases in aliases.items():
            if field in rename_map.values():
                continue
            for col in columns:
                if col in used or normalized[col] not in field_aliases:
                    continue
                rename_map[col] = field
                used.add(col)
                self.column_mapping.append({"source": str(col), "field": field, "label": self.FIELD_LABELS[field], "confidence": 1.0, "method": "别名匹配"})
                break

        # 第二层：模糊列名 + 数据类型联合判断，覆盖平台导出的自定义表头。
        for field in self.COLUMN_ALIASES:
            if field in rename_map.values():
                continue
            candidate = self._best_column_candidate(df, field, [col for col in columns if col not in used], normalized)
            if candidate is None:
                continue
            col, confidence = candidate
            if confidence < 0.52:
                continue
            rename_map[col] = field
            used.add(col)
            self.column_mapping.append({"source": str(col), "field": field, "label": self.FIELD_LABELS[field], "confidence": round(float(confidence), 2), "method": "智能识别"})

        return df.rename(columns=rename_map)

    @staticmethod
    def _normalize_column_name(value: object) -> str:
        """去除空格、括号和分隔符，便于中英文表头比较。"""
        text = str(value).strip().lower()
        return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", text)

    @staticmethod
    def _to_numeric(series: pd.Series) -> pd.Series:
        """解析平台常见的金额/数量文本（货币符号、千分位和空格）。"""
        cleaned = series.astype("string").str.replace(r"[,，\s￥¥$€£]", "", regex=True)
        return pd.to_numeric(cleaned, errors="coerce")

    def _best_column_candidate(self, df: pd.DataFrame, field: str, available: List[object], normalized: Dict[object, str]):
        if not available:
            return None
        aliases = [self._normalize_column_name(alias) for alias in self.COLUMN_ALIASES[field]]
        name_hints = {
            "order_id": ["订单", "流水", "单号", "编号", "order", "trade", "serial", "id"],
            "order_time": ["时间", "日期", "下单", "交易", "结算", "营业", "支付", "成交", "完成", "date", "time"],
            "customer_id": ["顾客", "客户", "会员", "用户", "customer", "user", "openid"],
            "product_name": ["商品", "菜品", "品名", "项目", "product", "food", "item", "sku"],
            "category": ["品类", "分类", "类别", "category"],
            "quantity": ["数量", "销量", "件数", "qty", "quantity", "count"],
            "unit_price": ["单价", "售价", "price"],
            "total_amount": ["金额", "金额元", "订单额", "交易额", "销售额", "营业额", "销售收入", "收入", "实收", "收款", "合计", "总额", "总价", "应收", "应付", "结算", "原价", "amount", "total", "revenue", "gmv"],
            "discount": ["优惠", "折扣", "立减", "红包", "discount"],
            "actual_amount": ["实付", "实收", "支付", "到账", "actual", "paid", "pay"],
            "refund_amount": ["退款", "refund"],
            "platform": ["平台", "渠道", "来源", "platform", "source"],
            "status": ["状态", "订单状态", "交易状态", "status"],
            "restaurant_name": ["餐厅", "门店", "店铺", "restaurant"],
            "weekday_label": ["星期", "工作日", "周末", "weekday", "week"],
            "rating": ["评分", "星级", "rating", "score"],
            "preparation_time": ["备餐", "出餐", "制作", "preparation"],
            "delivery_duration": ["配送", "送餐", "delivery"],
        }[field]

        best = None
        for col in available:
            name = normalized[col]
            if not name:
                continue
            alias_score = max((1.0 if name == alias else 0.86 if alias in name or name in alias else SequenceMatcher(None, name, alias).ratio() for alias in aliases), default=0)
            hint_score = max((1.0 if hint in name else 0 for hint in name_hints), default=0)
            sample = df[col].dropna().head(200)
            if sample.empty:
                continue
            numeric_ratio = self._to_numeric(sample).notna().mean()
            date_ratio = pd.to_datetime(sample, errors="coerce", format="mixed").notna().mean()
            text_ratio = 1 - numeric_ratio
            unique_ratio = sample.nunique(dropna=True) / max(len(sample), 1)
            if field == "order_time":
                type_score = date_ratio
            elif field in {"total_amount", "actual_amount", "refund_amount", "discount", "unit_price", "quantity", "rating", "preparation_time", "delivery_duration"}:
                type_score = numeric_ratio
            elif field in {"order_id", "customer_id"}:
                type_score = min(1.0, text_ratio * .65 + unique_ratio * .35)
            else:
                type_score = text_ratio
            score = alias_score * .55 + hint_score * .2 + type_score * .25
            if best is None or score > best[1]:
                best = (col, score)
        return best

    def _ensure_core_fields(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """为没有标准列名的文件提供可追踪的核心字段兜底。"""
        issues = []
        if "order_id" not in df.columns:
            df["order_id"] = [f"ROW-{index + 1:06d}" for index in range(len(df))]
            issues.append("未识别到订单号，已为每行生成唯一记录编号")
            self.column_mapping.append({"source": "系统生成", "field": "order_id", "label": self.FIELD_LABELS["order_id"], "confidence": 0.45, "method": "系统兜底"})
        if "order_time" not in df.columns:
            df["order_time"] = pd.Timestamp.now().normalize()
            issues.append("未识别到时间字段，已使用上传日期；趋势分析将按上传日期归档")
            self.column_mapping.append({"source": "系统生成", "field": "order_time", "label": self.FIELD_LABELS["order_time"], "confidence": 0.35, "method": "系统兜底"})
        if "product_name" not in df.columns:
            df["product_name"] = "未命名商品"
            issues.append("未识别到商品名称，已统一标记为“未命名商品”")
            self.column_mapping.append({"source": "系统生成", "field": "product_name", "label": self.FIELD_LABELS["product_name"], "confidence": 0.35, "method": "系统兜底"})
        if "total_amount" not in df.columns:
            # 实付/实收金额可以直接作为订单金额使用。
            if "actual_amount" in df.columns:
                df["total_amount"] = df["actual_amount"]
                issues.append("未识别到订单金额，已使用实付金额进行分析")
                self.column_mapping.append({"source": "actual_amount", "field": "total_amount", "label": self.FIELD_LABELS["total_amount"], "confidence": 0.7, "method": "语义回退"})
            else:
                # 最后一层按数据类型推断金额列，排除明显的数量/单价字段。
                # 若只有单价和数量，也可以自动构造订单金额。
                if "unit_price" in df.columns and "quantity" in df.columns:
                    unit_price = self._to_numeric(df["unit_price"])
                    quantity = self._to_numeric(df["quantity"])
                    df["total_amount"] = unit_price * quantity
                    issues.append("未识别到订单金额，已根据单价 × 数量计算订单金额")
                    self.column_mapping.append({"source": "unit_price × quantity", "field": "total_amount", "label": self.FIELD_LABELS["total_amount"], "confidence": 0.8, "method": "公式推断"})
                    return df, issues

                amount_candidates = []
                excluded_terms = ("数量", "销量", "件数", "qty", "quantity", "单价", "折扣", "discount")
                for column in df.columns:
                    name = self._normalize_column_name(column)
                    # 订单号、顾客号等字段通常也是数字型，但绝不能被当作金额。
                    if column in {"order_id", "customer_id", "order_time", "product_name", "category", "platform", "status"}:
                        continue
                    # CSV 导出的行号（Unnamed: 0）只是技术索引，不是业务金额。
                    if name.startswith("unnamed"):
                        continue
                    # 派单时间、日期编码和运单字段虽然是数字，也不能兜底为金额。
                    if name in {"dt", "date", "datetime", "timestamp"} or any(term in name for term in ("dispatch", "waybill", "courier", "rider", "派单", "运单", "骑手")):
                        continue
                    if any(term in name for term in ("订单号", "订单编号", "流水号", "客户号", "顾客号", "用户号", "customerid", "userid", "orderid")):
                        continue
                    if any(term in name for term in excluded_terms):
                        continue
                    sample = df[column].dropna().head(200)
                    if sample.empty:
                        continue
                    numeric_ratio = self._to_numeric(sample).notna().mean()
                    if numeric_ratio >= 0.8:
                        amount_candidates.append((column, numeric_ratio))
                if amount_candidates:
                    source_column, confidence = max(amount_candidates, key=lambda item: item[1])
                    df["total_amount"] = self._to_numeric(df[source_column])
                    issues.append(f"未识别到标准金额列，已根据数值特征使用“{source_column}”作为订单金额")
                    self.column_mapping.append({"source": str(source_column), "field": "total_amount", "label": self.FIELD_LABELS["total_amount"], "confidence": round(float(confidence * .55), 2), "method": "数值推断"})
                else:
                    raise ValueError("无法识别订单金额字段，请确认表格包含金额、营业额或实收金额列")
        return df, issues

    def _validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        数据校验：
        - 必填字段检查
        - 日期格式标准化
        - 数值非负检查
        """
        issues = []

        # --- 必填字段 ---
        # 时间字段是趋势、热力图、RFM 和预测分析的共同基础。
        required_fields = ["order_id", "order_time", "product_name", "total_amount"]
        for field in required_fields:
            if field not in df.columns:
                issues.append(f"缺少必填字段: {field}")

        # --- 日期标准化 ---
        if "order_time" in df.columns:
            # 不同平台会混用 `2026-08-01`、`8/23/2022`、Excel 序列号等格式。
            # format="mixed" 可以逐行推断格式，避免 pandas 按第一行格式解析导致
            # 后续日期变成 NaT。数值型日期再按 Excel 的 1899-12-30 起点补解析。
            raw_dates = df["order_time"]
            parsed_dates = pd.to_datetime(raw_dates, errors="coerce", format="mixed")
            numeric_dates = pd.to_numeric(raw_dates, errors="coerce")
            excel_mask = parsed_dates.isna() & numeric_dates.between(1, 100000)
            if excel_mask.any():
                parsed_dates.loc[excel_mask] = pd.to_datetime(
                    numeric_dates.loc[excel_mask],
                    unit="D",
                    origin="1899-12-30",
                    errors="coerce",
                )

            n_bad_dates = int(parsed_dates.isna().sum())
            if n_bad_dates > 0:
                # 日期缺失不应阻断整份表格分析。使用已识别日期的中位日期作为
                # 可追踪的兜底值；若整列都无法解析，则使用上传当天。
                valid_dates = parsed_dates.dropna()
                fallback_date = (
                    valid_dates.sort_values().iloc[len(valid_dates) // 2].normalize()
                    if not valid_dates.empty
                    else pd.Timestamp.now().normalize()
                )
                parsed_dates = parsed_dates.fillna(fallback_date)
                issues.append(
                    f"{n_bad_dates} 行日期无法识别，已使用 {fallback_date.strftime('%Y-%m-%d')} 归档"
                )

            df["order_time"] = parsed_dates
            # 始终输出字符串日期，避免 groupby/sort 时出现 str 与 float 混排。
            df["date"] = parsed_dates.dt.strftime("%Y-%m-%d")
            df["hour"] = df["order_time"].dt.hour
            df["weekday"] = df["order_time"].dt.weekday
            df["is_weekend"] = df["weekday"].isin([5, 6]).astype(int)

        # --- 数值字段类型转换 + 非负检查 ---
        numeric_checks = {
            "quantity": "数量",
            "unit_price": "单价",
            "total_amount": "总金额",
            "actual_amount": "实付金额",
            "discount": "优惠金额",
            "refund_amount": "退款金额",
            "rating": "评分",
            "preparation_time": "备餐时长",
            "delivery_duration": "配送时长",
        }
        for col, name in numeric_checks.items():
            if col in df.columns:
                df[col] = self._to_numeric(df[col])
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
        else:
            df["category"] = "其他"

        if "quantity" in df.columns:
            df["quantity"] = df["quantity"].fillna(1)
        else:
            df["quantity"] = 1

        if "unit_price" in df.columns:
            df["unit_price"] = df["unit_price"].fillna(df["total_amount"] / df["quantity"])
        else:
            df["unit_price"] = df["total_amount"] / df["quantity"]

        if "total_amount" in df.columns and "actual_amount" in df.columns:
            df["actual_amount"] = df["actual_amount"].fillna(df["total_amount"])

        if "discount" in df.columns:
            df["discount"] = df["discount"].fillna(0.0)
        else:
            df["discount"] = 0.0

        if "refund_amount" in df.columns:
            df["refund_amount"] = df["refund_amount"].fillna(0.0)
        else:
            df["refund_amount"] = 0.0

        # 构造缺失的关键列
        if "actual_amount" not in df.columns and "total_amount" in df.columns:
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
            "column_mapping": self.column_mapping,
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
