"""REST API for the restaurant analytics application.

The analytical functions remain in ``src``.  This module only handles HTTP,
dataset lifecycle and JSON serialization for the React web frontend.
"""

from __future__ import annotations

from datetime import datetime
import json
import logging
import os
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
from backend.ai import AIServiceError, suggest_field_mapping
from backend.database import get_db, init_db
from backend.models import User
from backend.storage import Dataset, DatasetStore

from src.analysis import (
    compute_overview_metrics,
    compute_platform_comparison,
    compute_product_analysis,
    compute_trend_analysis,
)
from src.data_pipeline import DataPipeline
from src.features import build_hourly_heatmap, build_rfm_features
from src.models import (
    find_optimal_k,
    run_apriori,
    run_isolation_forest,
    run_kmeans_clustering,
    run_prophet_forecast,
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
    allow_origins=[origin.strip() for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_database() -> None:
    init_db()


@app.exception_handler(Exception)
async def unhandled_exception(_: Request, exc: Exception) -> JSONResponse:
    """统一返回 JSON 错误，避免前端只看到模糊的网络错误。"""
    logger.exception("Unhandled API error")
    return JSONResponse(status_code=500, content={"detail": "服务处理失败，请查看后端日志"})


# 小规模部署使用本地持久化；多实例部署时可替换为对象存储。
DATASET_STORE = DatasetStore(os.getenv("DATASET_DIR", "data/datasets"))


class ForecastRequest(BaseModel):
    forecast_days: int = Field(default=14, ge=7, le=90)


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

        # 规则识别优先；只有存在模糊/兜底字段时，才按用户配置调用 AI 辅助判断。
        quality["ai_assistance"] = {"status": "not_configured", "provider": None, "mapping": [], "warnings": []}
        if ai_config:
            try:
                config = json.loads(ai_config)
                mapping = quality.get("column_mapping", [])
                needs_assistance = any(
                    item.get("method") != "别名匹配" and item.get("field") in {"order_id", "order_time", "product_name", "total_amount"}
                    for item in mapping
                )
                if needs_assistance and isinstance(config, dict):
                    suggestion = await suggest_field_mapping(config, pipeline.raw_columns, pipeline.raw_sample, mapping)
                    forced = {item["source"]: item for item in suggestion.get("mapping", [])}
                    if forced:
                        frame, quality = pipeline.run(payload, filename, forced_mapping=forced)
                    quality["ai_assistance"] = {
                        "status": "used" if forced else "no_match",
                        "provider": suggestion.get("provider"),
                        "mapping": suggestion.get("mapping", []),
                        "warnings": suggestion.get("warnings", []),
                    }
                elif isinstance(config, dict):
                    quality["ai_assistance"] = {"status": "not_needed", "provider": config.get("provider"), "mapping": [], "warnings": []}
            except (json.JSONDecodeError, TypeError, AIServiceError, ValueError) as exc:
                # AI 是可选增强能力，供应商故障时仍然保留规则识别结果。
                logger.warning("AI field mapping unavailable: %s", exc)
                quality["ai_assistance"] = {"status": "fallback", "provider": None, "mapping": [], "warnings": ["AI 辅助识别暂不可用，已使用规则识别结果"]}
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
    }


@app.post("/api/forecast/{dataset_id}")
def forecast(
    dataset_id: str,
    request: ForecastRequest | None = None,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    item = _dataset(dataset_id, current_user)
    days = request.forecast_days if request else 14
    daily = compute_trend_analysis(item.frame)
    result, meta = run_prophet_forecast(daily, forecast_days=days)
    return {"forecast": _records(result), "meta": _json(meta)}


@app.get("/api/anomalies/{dataset_id}")
def anomalies(dataset_id: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    result = run_isolation_forest(_dataset(dataset_id, current_user).frame)
    return {"total": len(result), "anomalies": _records(result[result["is_anomaly"]]), "all": _records(result)}


@app.get("/api/report/{dataset_id}")
def report(dataset_id: str, current_user: User = Depends(get_current_user)) -> dict[str, str]:
    frame = _dataset(dataset_id, current_user).frame
    overview_data = compute_overview_metrics(frame)
    product_data = compute_product_analysis(frame)
    platform_data = compute_platform_comparison(frame)
    rfm = build_rfm_features(frame)
    rules = run_apriori(frame)
    anomaly_data = run_isolation_forest(frame)
    forecast_data, _ = run_prophet_forecast(compute_trend_analysis(frame), forecast_days=7)
    content = generate_full_report(
        overview=overview_data,
        product_analysis=product_data,
        rfm_df=rfm,
        assoc_rules=rules,
        forecast_result=forecast_data,
        anomaly_orders=anomaly_data,
        platform_df=platform_data,
    )
    return {"dataset_id": dataset_id, "report": content}
