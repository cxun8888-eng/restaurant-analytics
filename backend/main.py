"""REST API for the restaurant analytics application.

The analytical functions remain in ``src``.  This module only handles HTTP,
dataset lifecycle and JSON serialization for the React web frontend.
"""

from __future__ import annotations

from datetime import datetime
import json
import logging
import os
import re
from typing import Any, Dict
from uuid import uuid4

import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth import get_current_user, hash_password, set_auth_cookie, user_payload, verify_password, AUTH_COOKIE_NAME
from backend.ai import AIServiceError, generate_ai_report, suggest_field_mapping
from backend.database import get_db, init_db
from backend.models import User
from backend.storage import Dataset, DatasetStore, PendingUpload, PendingUploadStore

from src.analysis import (
    compute_overview_metrics,
    compute_platform_comparison,
    compute_product_analysis,
    compute_trend_analysis,
)
from src.data_pipeline import DataPipeline
from src.features import build_hourly_heatmap, build_product_hourly_heatmap, build_product_time_analysis, build_rfm_features, build_segment_preferences
from src.models import (
    find_optimal_k,
    run_apriori,
    run_isolation_forest,
    run_kmeans_clustering,
    run_smart_forecast,
)
from src.report import generate_full_report

logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024


app = FastAPI(
    title="餐饮订单数据分析 API",
    version="1.0.0",
    description="为独立前端提供订单清洗、分析、建模和报告接口。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:4815,http://127.0.0.1:4815").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_database() -> None:
    init_db()
    PENDING_UPLOAD_STORE.purge_expired()


@app.exception_handler(Exception)
async def unhandled_exception(_: Request, exc: Exception) -> JSONResponse:
    """统一返回 JSON 错误，避免前端只看到模糊的网络错误。"""
    logger.exception("Unhandled API error")
    return JSONResponse(status_code=500, content={"detail": "服务处理失败，请查看后端日志"})


# 小规模部署使用本地持久化；多实例部署时可替换为对象存储。
DATASET_STORE = DatasetStore(os.getenv("DATASET_DIR", "data/datasets"))
PENDING_UPLOAD_STORE = PendingUploadStore(
    os.getenv("PENDING_UPLOAD_DIR", "data/pending"),
    ttl_seconds=int(os.getenv("PENDING_UPLOAD_TTL_SECONDS", "1800")),
)


class ForecastRequest(BaseModel):
    forecast_days: int = Field(default=14, ge=7, le=90)


class AnomalyReviewRequest(BaseModel):
    status: str = Field(pattern="^(reviewed|normal|needs_action)$")


class ReportRequest(BaseModel):
    # API key is sent only for this request and is never persisted by the API.
    ai_config: dict[str, Any] | None = None


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=80)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class ProfileRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class MappingSelection(BaseModel):
    source: str = Field(min_length=1, max_length=255)
    # Empty field means the user chose to ignore this source column.
    field: str = Field(default="", max_length=64)


class ConfirmDatasetRequest(BaseModel):
    inspection_id: str = Field(min_length=32, max_length=32)
    mapping: list[MappingSelection] = Field(default_factory=list, max_length=300)


def _dataset(dataset_id: str, current_user: User) -> Dataset:
    item = DATASET_STORE.get(dataset_id)
    if item is None or getattr(item, "owner_id", None) != current_user.id:
        raise HTTPException(status_code=404, detail="数据集不存在或已被清理")
    return item


def _clean_value(value: Any) -> Any:
    """将 pandas/numpy 类型转换成标准 JSON 类型。"""
    if value is None or value is pd.NaT:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, float) and np.isnan(value):
        return None
    if isinstance(value, dict):
        return {str(k): _clean_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_clean_value(v) for v in value]
    return value


def _json(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return [_json(row) for row in value.to_dict(orient="records")]
    if isinstance(value, pd.Series):
        return {_clean_value(k): _json(v) for k, v in value.to_dict().items()}
    return _clean_value(value)


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    return _json(df.reset_index().to_dict(orient="records"))


def _column_profile(frame: pd.DataFrame) -> dict[str, Any]:
    """Build a compact, JSON-safe profile from the complete raw dataframe."""
    columns: list[dict[str, Any]] = []
    for column in frame.columns:
        source = str(column)
        series = frame[column]
        non_null = series.dropna()
        if non_null.empty:
            examples: list[Any] = []
            numeric_ratio = 0.0
            date_ratio = 0.0
        else:
            examples = [_clean_value(value) for value in non_null.head(5).tolist()]
            numeric_ratio = float(DataPipeline._to_numeric(non_null).notna().mean())
            parsed_dates = pd.to_datetime(non_null, errors="coerce", format="mixed")
            date_ratio = float(parsed_dates.notna().mean())
        try:
            unique_count = int(non_null.nunique(dropna=True))
        except TypeError:
            unique_count = int(non_null.astype(str).nunique(dropna=True))
        columns.append(
            {
                "name": source,
                "dtype": str(series.dtype),
                "non_null_ratio": round(float(non_null.size / max(len(series), 1)), 4),
                "numeric_ratio": round(numeric_ratio, 4),
                "date_ratio": round(date_ratio, 4),
                "unique_count": unique_count,
                "examples": examples,
            }
        )
    return {"row_count": int(len(frame)), "column_count": int(len(frame.columns)), "columns": columns}


def _empty_ai_suggestion(status: str = "not_configured", provider: str | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "provider": provider,
        "business_domain": "unknown",
        "dataset_type": "unknown",
        "header_translations": [],
        "mapping": [],
        "ignored_columns": [],
        "warnings": [],
    }


def _source_token(value: object) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(value).strip().lower())


def _technical_index_source(source: object) -> bool:
    return _source_token(source).startswith("unnamed")


def _looks_like_amount_source(source: object, profile_item: dict[str, Any]) -> bool:
    """Accept only plausible amount columns for the analysis gate.

    Numeric delivery timestamps and identifiers are deliberately excluded even
    when an AI provider proposes them as ``total_amount``.
    """
    token = _source_token(source)
    if not token or _technical_index_source(source):
        return False
    blocked_tokens = ("dispatch", "waybill", "courier", "rider", "orderid", "customerid", "userid", "timestamp", "datetime", "date", "time", "dt")
    if any(term in token for term in blocked_tokens):
        return False
    amount_tokens = ("amount", "cost", "price", "total", "revenue", "sales", "value", "subtotal", "gmv", "harga", "金额", "金额", "营业", "收入", "实收", "实付", "费用", "总额", "总价")
    if any(term in token for term in amount_tokens):
        return True
    numeric_ratio = float(profile_item.get("numeric_ratio", 0) or 0)
    return numeric_ratio >= 0.8 and not any(term in token for term in ("id", "编号", "单号", "数量", "qty", "count"))


def _analysis_gate(profile: dict[str, Any], rule_mapping: list[dict[str, Any]], suggestion: dict[str, Any]) -> dict[str, Any]:
    """Decide whether an upload belongs to the current restaurant-order mode."""
    profile_by_source = {str(item.get("name")): item for item in profile.get("columns", []) if isinstance(item, dict)}
    mappings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in [*(rule_mapping or []), *((suggestion or {}).get("mapping", []) or [])]:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source", "")).strip()
        field = str(item.get("field", "")).strip()
        key = (source, field)
        if source and field and key not in seen:
            seen.add(key)
            mappings.append({"source": source, "field": field})

    if (suggestion or {}).get("business_domain") == "non_restaurant":
        return {"allowed": False, "reason": "当前文件不是餐饮订单数据，无法使用餐饮经营分析。请上传包含订单金额、商品/菜品和订单时间的餐饮订单报表。", "kind": "non_restaurant"}

    delivery_tokens = ("dispatch", "waybill", "courier", "rider", "派单", "运单", "骑手", "配送调度")
    has_delivery_signal = any(any(term in _source_token(source) for term in delivery_tokens) for source in profile_by_source)
    amount_sources = [item["source"] for item in mappings if item["field"] == "total_amount" and _looks_like_amount_source(item["source"], profile_by_source.get(item["source"], {}))]

    if has_delivery_signal and not amount_sources:
        return {"allowed": False, "reason": "检测到配送/运单明细，但没有订单金额字段。这不是可进行营收、商品和用户分析的餐饮订单报表。", "kind": "delivery_summary"}
    if not amount_sources:
        return {"allowed": False, "reason": "当前文件缺少可靠的订单金额字段，无法生成餐饮经营分析。请上传包含订单金额、营业额或实收金额的报表。", "kind": "missing_amount"}

    non_restaurant_tokens = ("warehouse", "inventory", "shipment", "invoice", "purchase", "flight", "hotel", "ticket", "sku")
    non_restaurant_hits = sum(any(term in _source_token(source) for term in non_restaurant_tokens) for source in profile_by_source)
    restaurant_tokens = ("restaurant", "food", "dish", "menu", "cuisine", "meal", "delivery", "餐厅", "餐馆", "菜品", "外卖", "配送")
    restaurant_hits = sum(any(term in _source_token(source) for term in restaurant_tokens) for source in profile_by_source)
    if non_restaurant_hits >= 2 and restaurant_hits == 0:
        return {"allowed": False, "reason": "当前文件看起来不是餐饮订单数据，无法使用餐饮经营分析。", "kind": "non_restaurant"}
    return {"allowed": True, "reason": "已通过餐饮订单数据校验", "kind": "restaurant_order"}


async def _inspect_upload(payload: bytes, filename: str, ai_config: str | None) -> tuple[DataPipeline, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    """Parse an upload and produce a reviewable AI/rules suggestion."""
    pipeline = DataPipeline()
    try:
        frame, quality = pipeline.run(payload, filename)
    except (ValueError, TypeError, KeyError) as exc:
        # Inspection must remain possible even when a core field is missing;
        # the user may be able to resolve it in the review table.
        if pipeline.raw_frame.empty:
            raise
        frame = pd.DataFrame()
        quality = {
            "raw_rows": int(len(pipeline.raw_frame)),
            "clean_rows": 0,
            "total_orders": 0,
            "date_range": "",
            "issues": [str(exc)],
            "anomalies": {},
            "missing_customer_id": False,
            "duplicates_removed": 0,
            "column_mapping": pipeline.column_mapping,
        }
    profile = _column_profile(pipeline.raw_frame)
    rule_mapping = quality.get("column_mapping", [])
    suggestion = _empty_ai_suggestion()

    if ai_config:
        try:
            config = json.loads(ai_config)
            if not isinstance(config, dict):
                raise AIServiceError("AI 配置格式不正确")
            suggestion = await suggest_field_mapping(
                config,
                pipeline.raw_columns,
                pipeline.raw_sample,
                rule_mapping,
                profile=profile,
            )
            suggestion["status"] = "ready" if suggestion.get("header_translations") or suggestion.get("mapping") or suggestion.get("warnings") else "no_match"
        except (json.JSONDecodeError, TypeError, AIServiceError, ValueError) as exc:
            logger.warning("AI field mapping unavailable during inspection: %s", exc)
            provider = None
            try:
                provider = json.loads(ai_config).get("provider")
            except (json.JSONDecodeError, AttributeError):
                pass
            suggestion = _empty_ai_suggestion("fallback", provider)
            suggestion["warnings"] = ["AI 辅助识别暂不可用，已使用规则识别结果"]

    quality["ai_assistance"] = {
        "status": suggestion.get("status", "not_configured"),
        "provider": suggestion.get("provider"),
        "header_translations": suggestion.get("header_translations", []),
        "mapping": suggestion.get("mapping", []),
        "warnings": suggestion.get("warnings", []),
    }
    quality["dataset_type"] = suggestion.get("dataset_type", "unknown")
    quality["analysis_gate"] = _analysis_gate(profile, rule_mapping, suggestion)
    quality["inspection_mode"] = True
    return pipeline, frame, quality, {"profile": profile, "suggestion": suggestion, "analysis_gate": quality["analysis_gate"]}


async def _read_upload(file: UploadFile) -> tuple[str, bytes]:
    filename = file.filename or "upload.csv"
    if not filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="仅支持 CSV、XLSX 或 XLS 文件")
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="上传文件为空")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"文件不能超过 {MAX_UPLOAD_BYTES // 1024 // 1024} MB")
    return filename, payload


def _save_dataset(frame: pd.DataFrame, quality: dict[str, Any], filename: str, owner_id: int) -> dict[str, Any]:
    dataset_id = uuid4().hex
    try:
        DATASET_STORE.save(dataset_id, Dataset(frame, quality, filename, datetime.utcnow(), owner_id=owner_id))
    except OSError as exc:
        logger.exception("Unable to persist dataset")
        raise HTTPException(status_code=500, detail="数据保存失败，请检查服务存储配置") from exc
    return {"dataset_id": dataset_id, "filename": filename, "rows": len(frame), "quality": _json(quality)}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(status_code=400, detail="请输入有效的邮箱地址")
    return email


@app.post("/api/auth/register")
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> dict[str, Any]:
    email = _normalize_email(payload.email)
    display_name = payload.display_name.strip()
    if not display_name:
        raise HTTPException(status_code=400, detail="请输入显示名称")
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="该邮箱已注册")

    user = User(email=email, display_name=display_name, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="该邮箱已注册") from exc
    set_auth_cookie(response, user.id)
    return {"user": user_payload(user)}


@app.post("/api/auth/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict[str, Any]:
    email = _normalize_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码不正确")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已停用")
    set_auth_cookie(response, user.id)
    return {"user": user_payload(user)}


@app.get("/api/auth/me")
def me(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {"user": user_payload(current_user)}


@app.post("/api/auth/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return {"message": "已退出登录"}


@app.patch("/api/auth/profile")
def update_profile(payload: ProfileRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    display_name = payload.display_name.strip()
    if not display_name:
        raise HTTPException(status_code=400, detail="显示名称不能为空")
    current_user.display_name = display_name
    db.commit()
    db.refresh(current_user)
    return {"user": user_payload(current_user)}


@app.post("/api/auth/password")
def update_password(payload: PasswordChangeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "密码已更新"}


@app.post("/api/datasets/inspect")
async def inspect_dataset(
    file: UploadFile = File(...),
    ai_config: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Parse an upload and return an AI-assisted mapping review, without saving a dataset."""
    filename, payload = await _read_upload(file)
    try:
        pipeline, _, quality, inspection = await _inspect_upload(payload, filename, ai_config)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    inspection_id = uuid4().hex
    suggestion = inspection["suggestion"]
    try:
        PENDING_UPLOAD_STORE.save(
            inspection_id,
            PendingUpload(
                payload=payload,
                filename=filename,
                created_at=datetime.utcnow(),
                owner_id=current_user.id,
                columns=list(pipeline.raw_columns),
                quality=quality,
                suggestion=suggestion,
            ),
        )
    except OSError as exc:
        logger.exception("Unable to persist pending upload")
        raise HTTPException(status_code=500, detail="临时文件保存失败，请检查服务存储配置") from exc

    return {
        "inspection_id": inspection_id,
        "filename": filename,
        "columns": list(pipeline.raw_columns),
        "profile": _json(inspection["profile"]),
        "sample_rows": _json(pipeline.raw_sample),
        "rule_mapping": _json(quality.get("column_mapping", [])),
        "suggestion": _json(suggestion),
        "quality": _json(quality),
        "expires_in_seconds": PENDING_UPLOAD_STORE.ttl_seconds,
    }


@app.post("/api/datasets/confirm")
def confirm_dataset(
    payload: ConfirmDatasetRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Apply the user's reviewed mappings and persist the processed dataset."""
    pending = PENDING_UPLOAD_STORE.get(payload.inspection_id)
    if pending is None or pending.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="上传检查已过期，请重新选择文件")

    columns = set(pending.columns)
    forced: dict[str, dict[str, Any]] = {}
    selected: list[dict[str, str]] = []
    ignored: list[str] = []
    seen_sources: set[str] = set()
    seen_fields: set[str] = set()
    for item in payload.mapping:
        source = item.source.strip()
        field = item.field.strip()
        if source not in columns:
            raise HTTPException(status_code=400, detail=f"未知原始字段: {source}")
        if source in seen_sources:
            raise HTTPException(status_code=400, detail=f"原始字段重复提交: {source}")
        seen_sources.add(source)
        if not field:
            ignored.append(source)
            continue
        if field not in DataPipeline.COLUMN_ALIASES:
            raise HTTPException(status_code=400, detail=f"不支持的标准字段: {field}")
        if field in seen_fields:
            raise HTTPException(status_code=400, detail=f"标准字段只能映射一次: {field}")
        seen_fields.add(field)
        forced[source] = {"field": field, "confidence": 1.0}
        selected.append({"source": source, "field": field})

    try:
        review_frame = DataPipeline()._load_data(pending.payload, pending.filename)
        review_profile = _column_profile(review_frame)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=f"无法重新读取待确认文件：{exc}") from exc
    review_suggestion = {"business_domain": (pending.suggestion or {}).get("business_domain", "unknown"), "mapping": []}
    review_gate = _analysis_gate(review_profile, selected, review_suggestion)
    if not review_gate["allowed"]:
        raise HTTPException(status_code=400, detail=review_gate["reason"])

    try:
        frame, quality = DataPipeline().run(pending.payload, pending.filename, forced_mapping=forced)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    required = {"order_id", "order_time", "product_name", "total_amount"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise HTTPException(status_code=400, detail=f"缺少必要字段: {', '.join(missing)}")

    suggestion = dict(pending.suggestion or {})
    quality["ai_assistance"] = {
        "status": "confirmed" if suggestion.get("provider") else "not_configured",
        "provider": suggestion.get("provider"),
        "header_translations": suggestion.get("header_translations", []),
        "mapping": suggestion.get("mapping", []),
        "warnings": suggestion.get("warnings", []),
    }
    quality["dataset_type"] = suggestion.get("dataset_type", "unknown")
    quality["mapping_review"] = {"selected": selected, "ignored": ignored}
    result = _save_dataset(frame, quality, pending.filename, current_user.id)
    PENDING_UPLOAD_STORE.delete(payload.inspection_id)
    return result


@app.post("/api/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    ai_config: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    filename = file.filename or "upload.csv"
    if not filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="仅支持 CSV、XLSX 或 XLS 文件")

    try:
        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="上传文件为空")
        if len(payload) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"文件不能超过 {MAX_UPLOAD_BYTES // 1024 // 1024} MB")
        pipeline = DataPipeline()
        frame, quality = pipeline.run(payload, filename)

        # 配置 AI 后始终先翻译完整表头；字段模糊时再采用 AI 的映射建议。
        suggestion = _empty_ai_suggestion()
        quality["ai_assistance"] = {"status": "not_configured", "provider": None, "header_translations": [], "mapping": [], "warnings": []}
        if ai_config:
            try:
                config = json.loads(ai_config)
                mapping = quality.get("column_mapping", [])
                needs_assistance = any(
                    item.get("method") != "别名匹配" and item.get("field") in {"order_id", "order_time", "product_name", "total_amount"}
                    for item in mapping
                )
                if isinstance(config, dict):
                    suggestion = await suggest_field_mapping(
                        config,
                        pipeline.raw_columns,
                        pipeline.raw_sample,
                        mapping,
                        profile=_column_profile(pipeline.raw_frame),
                    )
                    forced = {item["source"]: item for item in suggestion.get("mapping", [])} if needs_assistance else {}
                    if forced:
                        frame, quality = pipeline.run(payload, filename, forced_mapping=forced)
                    quality["ai_assistance"] = {
                        "status": "used" if forced else "translated",
                        "provider": suggestion.get("provider"),
                        "header_translations": suggestion.get("header_translations", []),
                        "mapping": suggestion.get("mapping", []),
                        "warnings": suggestion.get("warnings", []),
                    }
            except (json.JSONDecodeError, TypeError, AIServiceError, ValueError) as exc:
                # AI 是可选增强能力，供应商故障时仍然保留规则识别结果。
                logger.warning("AI field mapping unavailable: %s", exc)
                quality["ai_assistance"] = {"status": "fallback", "provider": None, "header_translations": [], "mapping": [], "warnings": ["AI 辅助识别暂不可用，已使用规则识别结果"]}
        quality["analysis_gate"] = _analysis_gate(_column_profile(pipeline.raw_frame), quality.get("column_mapping", []), suggestion)
        if not quality["analysis_gate"]["allowed"]:
            raise HTTPException(status_code=400, detail=quality["analysis_gate"]["reason"])
        required = {"order_id", "order_time", "product_name", "total_amount"}
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise HTTPException(status_code=400, detail=f"缺少必要字段: {', '.join(missing)}")
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    dataset_id = uuid4().hex
    try:
        DATASET_STORE.save(dataset_id, Dataset(frame, quality, filename, datetime.utcnow(), owner_id=current_user.id))
    except OSError as exc:
        logger.exception("Unable to persist dataset")
        raise HTTPException(status_code=500, detail="数据保存失败，请检查服务存储配置") from exc
    return {
        "dataset_id": dataset_id,
        "filename": filename,
        "rows": len(frame),
        "quality": _json(quality),
    }


@app.delete("/api/datasets/{dataset_id}")
def delete_dataset(dataset_id: str, current_user: User = Depends(get_current_user)) -> dict[str, str]:
    _dataset(dataset_id, current_user)
    if not DATASET_STORE.delete(dataset_id):
        raise HTTPException(status_code=404, detail="数据集不存在或已被清理")
    return {"message": "数据集已删除"}


@app.get("/api/datasets/{dataset_id}/quality")
def dataset_quality(dataset_id: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    item = _dataset(dataset_id, current_user)
    return {"dataset_id": dataset_id, "filename": item.filename, "quality": _json(item.quality)}


@app.get("/api/datasets/{dataset_id}/preview")
def dataset_preview(
    dataset_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """返回清洗后的字段信息和少量样例，供前端数据预览页使用。"""
    frame = _dataset(dataset_id, current_user).frame.head(limit)
    return {"columns": list(frame.columns), "rows": _records(frame)}


@app.get("/api/overview/{dataset_id}")
def overview(dataset_id: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    frame = _dataset(dataset_id, current_user).frame
    daily = compute_trend_analysis(frame)
    platform = compute_platform_comparison(frame)
    heatmap = build_hourly_heatmap(frame)
    return {
        "metrics": _json(compute_overview_metrics(frame)),
        "trend": _records(daily),
        "platform": _records(platform),
        "hourly_heatmap": _records(heatmap),
    }


@app.get("/api/products/{dataset_id}")
def products(
    dataset_id: str,
    min_support: float = Query(default=0.01, ge=0.0001, le=1),
    min_lift: float = Query(default=1.0, ge=0),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    frame = _dataset(dataset_id, current_user).frame
    result = compute_product_analysis(frame)
    rules = run_apriori(frame, min_support=min_support, min_lift=min_lift)
    return {
        "ranking": _records(result["product_ranking"]),
        "categories": _records(result["category_breakdown"]),
        "slow_movers": _records(result["slow_movers"]),
        "association_rules": _records(rules),
        "product_hourly_heatmap": _records(build_product_hourly_heatmap(frame)),
        "product_time_analysis": _records(build_product_time_analysis(frame)),
    }


@app.get("/api/users/{dataset_id}")
def users(
    dataset_id: str,
    clusters: int = Query(default=4, ge=2, le=8),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    frame = _dataset(dataset_id, current_user).frame
    rfm = build_rfm_features(frame)
    elbow = find_optimal_k(rfm, max_k=min(8, len(rfm))) if len(rfm) >= 2 else pd.DataFrame()
    cluster_count = min(clusters, len(rfm))
    if cluster_count >= 2:
        clustered, meta = run_kmeans_clustering(rfm, n_clusters=cluster_count)
    else:
        clustered, meta = rfm.copy(), {"centers": pd.DataFrame(), "inertia": None}
    return {
        "rfm": _records(clustered),
        "segments": _records(clustered["segment"].value_counts().rename("count").to_frame()),
        "elbow": _records(elbow),
        "clusters": _records(meta.get("centers", pd.DataFrame())),
        "inertia": _json(meta.get("inertia")),
        "preferences": _records(build_segment_preferences(frame, clustered)),
    }


@app.post("/api/forecast/{dataset_id}")
def forecast(
    dataset_id: str,
    request: ForecastRequest | None = None,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    item = _dataset(dataset_id, current_user)
    days = request.forecast_days if request else 14
    anomaly_result = run_isolation_forest(item.frame)
    excluded_ids = set(anomaly_result.loc[anomaly_result["is_anomaly"], "order_id"].astype(str))
    clean_frame = item.frame[~item.frame["order_id"].astype(str).isin(excluded_ids)]
    if clean_frame.empty:
        clean_frame = item.frame
        excluded_ids = set()
    daily = compute_trend_analysis(clean_frame)
    result, meta = run_smart_forecast(daily, forecast_days=days)
    meta["excluded_anomalies"] = len(excluded_ids)
    return {"forecast": _records(result), "meta": _json(meta)}


@app.get("/api/anomalies/{dataset_id}")
def anomalies(dataset_id: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    item = _dataset(dataset_id, current_user)
    result = run_isolation_forest(item.frame)
    flagged = result[result["is_anomaly"]].copy()
    reviews = getattr(item, "anomaly_reviews", {}) or {}
    flagged["review_status"] = flagged["order_id"].astype(str).map(reviews).fillna("pending")
    type_counts: dict[str, int] = {}
    for value in flagged.get("anomaly_types", pd.Series(dtype=str)).fillna(""):
        for anomaly_type in str(value).split("、"):
            if anomaly_type:
                type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1
    status_counts = {str(key): int(value) for key, value in flagged["review_status"].value_counts().items()}
    return {
        "total": len(result),
        "total_anomalies": len(flagged),
        "summary": {"by_type": type_counts, "by_status": status_counts},
        "anomalies": _records(flagged),
    }


@app.patch("/api/anomalies/{dataset_id}/{order_id}")
def review_anomaly(
    dataset_id: str,
    order_id: str,
    request: AnomalyReviewRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    item = _dataset(dataset_id, current_user)
    known_orders = set(item.frame["order_id"].astype(str))
    if order_id not in known_orders:
        raise HTTPException(status_code=404, detail="订单不存在")
    reviews = dict(getattr(item, "anomaly_reviews", {}) or {})
    reviews[order_id] = request.status
    item.anomaly_reviews = reviews
    DATASET_STORE.save(dataset_id, item)
    return {"order_id": order_id, "review_status": request.status}


def _report_ai_summary(
    overview_data: dict[str, Any],
    product_data: dict[str, pd.DataFrame],
    rfm: pd.DataFrame,
    rules: pd.DataFrame,
    forecast_data: pd.DataFrame,
    anomaly_data: pd.DataFrame,
    platform_data: pd.DataFrame,
) -> dict[str, Any]:
    """Create a small aggregate-only payload for the AI report prompt."""
    def records(frame: pd.DataFrame, columns: list[str], limit: int = 8) -> list[dict[str, Any]]:
        if frame is None or frame.empty:
            return []
        available = [column for column in columns if column in frame.columns]
        return _json(frame[available].head(limit)) if available else []

    segment_counts = {}
    if rfm is not None and not rfm.empty and "segment" in rfm.columns:
        segment_counts = {str(key): int(value) for key, value in rfm["segment"].value_counts().items()}
    anomalies = anomaly_data[anomaly_data["is_anomaly"]] if anomaly_data is not None and "is_anomaly" in anomaly_data.columns else pd.DataFrame()
    return {
        "overview": overview_data,
        "platforms": records(platform_data, ["platform", "total_orders", "total_revenue", "avg_order_value", "revenue_share", "refund_rate"], 6),
        "top_products": records(product_data.get("product_ranking"), ["product_name", "category", "total_sold", "total_revenue", "revenue_share", "refund_count"], 8),
        "slow_products": records(product_data.get("slow_movers"), ["product_name", "category", "total_sold", "total_revenue"], 5),
        "user_segments": segment_counts,
        "association_rules": records(rules, ["antecedent", "consequent", "support", "confidence", "lift", "recommendation"], 5),
        "forecast": records(forecast_data, ["date", "predicted", "lower_bound", "upper_bound"], 14),
        "anomalies": records(anomalies, ["order_id", "total_amount", "actual_amount", "anomaly_score"], 8),
    }


def _report_payload(frame: pd.DataFrame) -> tuple[str, dict[str, Any]]:
    overview_data = compute_overview_metrics(frame)
    product_data = compute_product_analysis(frame)
    platform_data = compute_platform_comparison(frame)
    rfm = build_rfm_features(frame)
    rules = run_apriori(frame)
    anomaly_data = run_isolation_forest(frame)
    forecast_data, _ = run_smart_forecast(compute_trend_analysis(frame), forecast_days=7)
    content = generate_full_report(
        overview=overview_data,
        product_analysis=product_data,
        rfm_df=rfm,
        assoc_rules=rules,
        forecast_result=forecast_data,
        anomaly_orders=anomaly_data,
        platform_df=platform_data,
    )
    summary = _report_ai_summary(overview_data, product_data, rfm, rules, forecast_data, anomaly_data, platform_data)
    return content, summary


@app.get("/api/report/{dataset_id}")
def report(dataset_id: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    content, _ = _report_payload(_dataset(dataset_id, current_user).frame)
    return {"dataset_id": dataset_id, "report": content, "report_mode": "rules", "provider": None, "ai_report": None}


@app.post("/api/report/{dataset_id}")
async def ai_report(dataset_id: str, request: ReportRequest | None = None, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    frame = _dataset(dataset_id, current_user).frame
    content, summary = _report_payload(frame)
    config = request.ai_config if request else None
    if not config:
        return {"dataset_id": dataset_id, "report": content, "report_mode": "rules", "provider": None, "ai_report": None}
    try:
        result = await generate_ai_report(config, summary)
        provider = result.pop("provider", config.get("provider"))
        model = result.pop("model", config.get("modelId"))
        return {"dataset_id": dataset_id, "report": content, "report_mode": "ai", "provider": provider, "model": model, "ai_report": result, "ai_warning": None}
    except (AIServiceError, TypeError, ValueError, IndexError, json.JSONDecodeError) as exc:
        logger.warning("AI report unavailable, using deterministic report: %s", exc)
        return {"dataset_id": dataset_id, "report": content, "report_mode": "rules", "provider": None, "ai_report": None, "ai_warning": "AI 解读暂不可用，已切换为本地数据报告。"}
