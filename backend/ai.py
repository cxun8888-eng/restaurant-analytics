"""Optional AI assistance for uncertain column mapping.

The deterministic data pipeline remains the source of truth. This module only
asks a configured provider to suggest mappings for ambiguous source columns;
the response is validated before it can be applied to the pipeline.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx


SUPPORTED_FIELDS = {
    "order_id", "order_time", "customer_id", "product_name", "category",
    "quantity", "unit_price", "total_amount", "discount", "actual_amount",
    "refund_amount", "platform", "status",
}


class AIServiceError(RuntimeError):
    """A provider could not return a usable mapping suggestion."""


def _endpoint(config: dict[str, Any]) -> str:
    endpoint = str(config.get("endpoint") or "").strip().rstrip("/")
    if not endpoint.startswith(("https://", "http://")):
        raise AIServiceError("AI API 端点必须以 http:// 或 https:// 开头")
    return endpoint


def _prompt(columns: list[str], sample: list[dict[str, Any]], existing_mapping: list[dict[str, Any]]) -> str:
    schema = [
        "order_id: 订单唯一编号",
        "order_time: 下单、支付、交易或营业日期时间",
        "customer_id: 顾客/会员唯一编号",
        "product_name: 商品或菜品名称",
        "category: 商品品类",
        "quantity: 购买数量",
        "unit_price: 商品单价",
        "total_amount: 订单总金额/营业额/交易金额",
        "discount: 优惠或折扣金额",
        "actual_amount: 顾客实际支付/到账金额",
        "refund_amount: 退款金额",
        "platform: 美团、饿了么、微信等来源平台",
        "status: 订单状态",
    ]
    return """你是餐饮数据字段识别助手。请根据表头和少量样例，判断每个原始列最对应的标准字段。
只返回 JSON，不要 markdown，不要新增标准字段。格式：
{"mapping":[{"source":"原始列名","field":"标准字段","confidence":0.0,"reason":"一句话理由"}],"warnings":["需要用户确认的事项"]}

标准字段：
""" + "\n".join(schema) + "\n\n原始列名：\n" + json.dumps(columns, ensure_ascii=False) + "\n\n样例数据：\n" + json.dumps(sample, ensure_ascii=False, default=str) + "\n\n已有规则识别：\n" + json.dumps(existing_mapping, ensure_ascii=False, default=str)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise AIServiceError("AI 返回的字段识别结果不是有效 JSON") from exc
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError as nested:
            raise AIServiceError("AI 返回的字段识别结果不是有效 JSON") from nested
    if not isinstance(value, dict):
        raise AIServiceError("AI 返回结果格式不正确")
    return value


def _validate_result(value: dict[str, Any], columns: list[str]) -> dict[str, Any]:
    allowed_columns = {str(column) for column in columns}
    mapping: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    seen_fields: set[str] = set()
    for item in value.get("mapping", []):
        if not isinstance(item, dict):
            continue
        source = str(item.get("source", "")).strip()
        field = str(item.get("field", "")).strip()
        if source not in allowed_columns or source in seen_sources or field not in SUPPORTED_FIELDS or field in seen_fields:
            continue
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.7))))
        except (TypeError, ValueError):
            confidence = 0.7
        mapping.append({"source": source, "field": field, "confidence": round(confidence, 2), "reason": str(item.get("reason", "AI 根据表头和样例判断"))[:160]})
        seen_sources.add(source)
        seen_fields.add(field)
    warnings = [str(item)[:200] for item in value.get("warnings", []) if str(item).strip()][:8]
    return {"mapping": mapping, "warnings": warnings}


async def suggest_field_mapping(config: dict[str, Any], columns: list[str], sample: list[dict[str, Any]], existing_mapping: list[dict[str, Any]]) -> dict[str, Any]:
    provider = str(config.get("provider", "")).strip().lower()
    if provider not in {"deepseek", "doubao", "openai", "gemini"}:
        raise AIServiceError("暂不支持该 AI 服务商")
    api_key = str(config.get("apiKey") or config.get("api_key") or "").strip()
    if not api_key:
        raise AIServiceError("未配置 AI API Key")
    prompt = _prompt(columns, sample, existing_mapping)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=8.0)) as client:
            if provider == "gemini":
                model = str(config.get("modelId") or "gemini-2.0-flash")
                url = f"{_endpoint(config)}/models/{model}:generateContent"
                response = await client.post(url, params={"key": api_key}, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}})
                if response.status_code >= 400:
                    raise AIServiceError(f"Gemini 请求失败（HTTP {response.status_code}）")
                body = response.json()
                text = body.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            else:
                model = str(config.get("modelId") or ("deepseek-chat" if provider == "deepseek" else "gpt-4o-mini"))
                url = f"{_endpoint(config)}/chat/completions"
                response = await client.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": model, "temperature": 0.1, "messages": [{"role": "system", "content": "你只输出合法 JSON。"}, {"role": "user", "content": prompt}]})
                if response.status_code >= 400:
                    raise AIServiceError(f"{provider or 'AI'} 请求失败（HTTP {response.status_code}）")
                body = response.json()
                text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    except httpx.HTTPError as exc:
        raise AIServiceError("AI 服务暂时不可用，已回退到规则识别") from exc

    result = _validate_result(_extract_json(text), columns)
    result["provider"] = provider
    return result
