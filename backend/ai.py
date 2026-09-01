"""Optional AI assistance for header translation and column mapping.

The deterministic data pipeline remains the source of truth. This module only
asks a configured provider to translate source headers and suggest mappings for
ambiguous columns; the response is validated before it can be applied to the
pipeline.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx


SUPPORTED_FIELDS = {
    "order_id", "order_time", "customer_id", "product_name", "category",
    "quantity", "unit_price", "total_amount", "discount", "actual_amount",
    "refund_amount", "platform", "status", "restaurant_name", "weekday_label",
    "rating", "preparation_time", "delivery_duration",
}


class AIServiceError(RuntimeError):
    """A provider could not return a usable mapping suggestion."""


def _endpoint(config: dict[str, Any]) -> str:
    endpoint = str(config.get("endpoint") or "").strip().rstrip("/")
    if not endpoint.startswith(("https://", "http://")):
        raise AIServiceError("AI API 端点必须以 http:// 或 https:// 开头")
    return endpoint


def _prompt(
    columns: list[str],
    sample: list[dict[str, Any]],
    existing_mapping: list[dict[str, Any]],
    profile: dict[str, Any] | None = None,
) -> str:
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
        "restaurant_name: 餐厅、门店或店铺名称（不是商品名称）",
        "weekday_label: 星期几、工作日/周末等营业日标签（不是具体日期）",
        "rating: 顾客评分或星级",
        "preparation_time: 备餐/出餐/制作时长",
        "delivery_duration: 配送/送餐时长",
    ]
    return """你是餐饮数据字段识别助手。请先把每一个原始表头翻译成简洁、准确的中文业务名称，再综合原始表头、中文释义、全表统计画像和跨文件抽样，判断每个原始列最对应的标准字段，并判断这是什么类型的报表以及是否属于餐饮订单业务。
表头翻译必须覆盖原始列名中的每一列，包括 Unnamed、编码和平台专有字段；无法确定含义时保留原文，并在 reason 中说明。翻译只用于帮助用户理解，不得修改原始列名。
只返回 JSON，不要 markdown，不要新增标准字段。无法确认时请放入 ignored_columns，不要强行映射。
特别注意：有业务意义的列不要放入 ignored_columns。星期几、工作日/周末应映射到 weekday_label，配送时长应映射到 delivery_duration，评分应映射到 rating，餐厅名称应映射到 restaurant_name，菜系/菜品分类应映射到 category；它们不能冒充具体订单时间、订单状态或商品名称。只有明确的日期/时间值才能映射到 order_time。
格式：
{"business_domain":"restaurant|non_restaurant|unknown","dataset_type":"order_detail|restaurant_summary|product_summary|delivery_summary|unknown","header_translations":[{"source":"原始列名","translated":"中文表头释义","confidence":0.0,"reason":"翻译依据"}],"mapping":[{"source":"原始列名","field":"标准字段","confidence":0.0,"reason":"一句话理由"}],"ignored_columns":["不参与分析的原始列"],"warnings":["需要用户确认的事项"]}

标准字段：
""" + "\n".join(schema) + "\n\n原始列名：\n" + json.dumps(columns, ensure_ascii=False) + "\n\n全表统计画像：\n" + json.dumps(profile or {}, ensure_ascii=False, default=str) + "\n\n代表性样例（不是完整数据）：\n" + json.dumps(sample, ensure_ascii=False, default=str) + "\n\n已有规则识别：\n" + json.dumps(existing_mapping, ensure_ascii=False, default=str)


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


def _profile_column(profile: dict[str, Any] | None, source: str) -> dict[str, Any]:
    for item in (profile or {}).get("columns", []):
        if isinstance(item, dict) and str(item.get("name")) == source:
            return item
    return {}


def _source_tokens(source: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", source.strip().lower())


def _mapping_rejection(source: str, field: str, profile: dict[str, Any] | None) -> str | None:
    """Reject semantically unsafe AI suggestions before they reach ETL."""
    item = _profile_column(profile, source)
    numeric_ratio = float(item.get("numeric_ratio", 0) or 0)
    date_ratio = float(item.get("date_ratio", 0) or 0)
    token = _source_tokens(source)

    if token.startswith("unnamed"):
        return "该列是 CSV 技术索引，不是业务字段"

    if field == "order_time":
        if any(term in token for term in ("dayofweek", "weekday", "weekend", "配送时长", "preparationtime", "deliverytime", "deliveryduration")):
            return "该列表示星期或时长，不是具体订单时间"
        if date_ratio < 0.45:
            return "该列可解析为日期/时间的比例过低"
    if field in {"total_amount", "actual_amount", "refund_amount", "discount", "unit_price", "quantity"} and numeric_ratio < 0.55:
        return "该列可解析为数字的比例过低"
    if field in {"total_amount", "actual_amount", "refund_amount", "discount", "unit_price", "quantity"} and any(term in token for term in ("dispatch", "waybill", "courier", "rider", "orderid", "customerid", "userid")):
        return "配送调度或编号字段不能作为金额/数量"
    if field == "status" and ("rating" in token or "score" in token or "评分" in token or "preparationtime" in token or "deliverytime" in token):
        return "评分或时长列不能作为订单状态"
    if field == "product_name" and ("restaurant" in token or "餐厅" in token) and "product" not in token and "商品" not in token:
        return "餐厅名称列不能默认作为商品名称"
    return None


def _validate_result(value: dict[str, Any], columns: list[str], profile: dict[str, Any] | None = None) -> dict[str, Any]:
    allowed_columns = {str(column) for column in columns}
    header_translations: list[dict[str, Any]] = []
    seen_translation_sources: set[str] = set()
    raw_translations = value.get("header_translations", value.get("translations", []))
    if isinstance(raw_translations, dict):
        raw_translations = [{"source": source, "translated": translated} for source, translated in raw_translations.items()]
    if not isinstance(raw_translations, list):
        raw_translations = []
    for item in raw_translations:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source", "")).strip()
        translated = str(item.get("translated", item.get("translation", item.get("label", "")))).strip()
        if source not in allowed_columns or source in seen_translation_sources or not translated:
            continue
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.8))))
        except (TypeError, ValueError):
            confidence = 0.8
        header_translations.append({"source": source, "translated": translated[:80], "confidence": round(confidence, 2), "reason": str(item.get("reason", "AI 根据原始表头和样例翻译"))[:160]})
        seen_translation_sources.add(source)
    # AI 可能因输出长度限制漏掉个别列；保留这些原文，确保前端每列都有稳定的释义记录。
    for source in columns:
        source = str(source)
        if source not in seen_translation_sources:
            header_translations.append({"source": source, "translated": source, "confidence": 0.0, "reason": "AI 未返回翻译，暂保留原始表头"})
    mapping: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    seen_fields: set[str] = set()
    raw_warnings = value.get("warnings", [])
    if isinstance(raw_warnings, str):
        raw_warnings = [raw_warnings]
    warnings = [str(item)[:200] for item in raw_warnings if str(item).strip()][:8]
    raw_mapping = value.get("mapping", [])
    if not isinstance(raw_mapping, list):
        raw_mapping = []
    for item in raw_mapping:
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
        rejection = _mapping_rejection(source, field, profile)
        if rejection:
            warnings.append(f"{source} → {field}：{rejection}，已暂不采用")
            continue
        mapping.append({"source": source, "field": field, "confidence": round(confidence, 2), "reason": str(item.get("reason", "AI 根据表头和样例判断"))[:160]})
        seen_sources.add(source)
        seen_fields.add(field)
    ignored = []
    raw_ignored = value.get("ignored_columns", [])
    if isinstance(raw_ignored, str):
        raw_ignored = [raw_ignored]
    for item in raw_ignored:
        source = str(item).strip()
        if source in allowed_columns and source not in seen_sources and source not in ignored:
            ignored.append(source)
    dataset_type = str(value.get("dataset_type", "unknown")).strip().lower()
    if dataset_type not in {"order_detail", "restaurant_summary", "product_summary", "delivery_summary", "unknown"}:
        dataset_type = "unknown"
    business_domain = str(value.get("business_domain", "unknown")).strip().lower()
    if business_domain not in {"restaurant", "non_restaurant", "unknown"}:
        business_domain = "unknown"
    return {"business_domain": business_domain, "dataset_type": dataset_type, "header_translations": header_translations, "mapping": mapping, "ignored_columns": ignored, "warnings": warnings[:12]}


async def suggest_field_mapping(
    config: dict[str, Any],
    columns: list[str],
    sample: list[dict[str, Any]],
    existing_mapping: list[dict[str, Any]],
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    provider = str(config.get("provider", "")).strip().lower()
    if provider not in {"deepseek", "doubao", "openai", "gemini"}:
        raise AIServiceError("暂不支持该 AI 服务商")
    api_key = str(config.get("apiKey") or config.get("api_key") or "").strip()
    if not api_key:
        raise AIServiceError("未配置 AI API Key")
    prompt = _prompt(columns, sample, existing_mapping, profile=profile)

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

    result = _validate_result(_extract_json(text), columns, profile=profile)
    result["provider"] = provider
    return result


def _report_prompt(summary: dict[str, Any]) -> str:
    """Build a compact, privacy-conscious prompt from computed aggregates."""
    return """你是一名餐饮经营分析顾问。请根据下面已经由系统本地计算完成的结构化指标，生成一份给餐饮店老板看的经营解读。
不要编造数据，不要把相关性说成因果；每条结论都要能在提供的数字中找到依据。使用简洁、直接、非技术化的中文。只返回 JSON，不要 markdown，不要代码块。

JSON 格式：
{
  "title": "一句话标题（不超过 24 字）",
  "summary": "一句话经营结论（40-90 字，必须包含关键数字）",
  "signals": [{"label":"指标名","value":"展示值","detail":"解释或数据依据","tone":"positive|warning|neutral"}],
  "risks": [{"title":"风险标题","detail":"为什么需要注意（包含数字）","evidence":"数据依据","priority":"高|中|低"}],
  "opportunities": [{"title":"机会标题","detail":"可以尝试的方向（包含数字）","evidence":"数据依据"}],
  "actions": [{"priority":1,"title":"今天要做什么","detail":"具体动作和对象","reason":"为什么现在做"}],
  "method_note": "一句话说明数据范围、预测或模型的局限"
}

要求：signals 最多 4 条；risks、opportunities、actions 各最多 4 条；没有依据的类别返回空数组。行动必须具体到商品、平台、用户群、日期或时段之一；不要只写“加强管理”“持续关注”。

系统计算摘要：
""" + json.dumps(summary, ensure_ascii=False, default=str)


def _validate_report_result(value: dict[str, Any]) -> dict[str, Any]:
    """Keep AI output bounded and predictable before it reaches the UI."""
    if not isinstance(value, dict):
        raise AIServiceError("AI 报告返回结果格式不正确")

    def clean_text(item: Any, limit: int, fallback: str = "") -> str:
        text = str(item or "").strip()
        return text[:limit] if text else fallback

    def clean_list(key: str, fields: list[str], limit: int = 4) -> list[dict[str, Any]]:
        raw = value.get(key, [])
        if not isinstance(raw, list):
            return []
        result: list[dict[str, Any]] = []
        for item in raw[:limit]:
            if not isinstance(item, dict):
                continue
            row: dict[str, Any] = {}
            for field in fields:
                if field == "priority" and key == "actions":
                    try:
                        row[field] = max(1, min(4, int(item.get(field, len(result) + 1))))
                    except (TypeError, ValueError):
                        row[field] = len(result) + 1
                else:
                    row[field] = clean_text(item.get(field), 180 if field != "title" else 60)
            if any(row.get(field) for field in fields if field != "priority"):
                result.append(row)
        return result

    signals = clean_list("signals", ["label", "value", "detail", "tone"])
    allowed_tones = {"positive", "warning", "neutral"}
    for signal in signals:
        if signal["tone"] not in allowed_tones:
            signal["tone"] = "neutral"
    risks = clean_list("risks", ["title", "detail", "evidence", "priority"])
    for risk in risks:
        if risk["priority"] not in {"高", "中", "低"}:
            risk["priority"] = "中"
    return {
        "title": clean_text(value.get("title"), 40, "本周期经营解读"),
        "summary": clean_text(value.get("summary"), 240, "系统已完成本周期数据解读，请结合下方指标查看经营变化。"),
        "signals": signals,
        "risks": risks,
        "opportunities": clean_list("opportunities", ["title", "detail", "evidence"]),
        "actions": clean_list("actions", ["priority", "title", "detail", "reason"]),
        "method_note": clean_text(value.get("method_note"), 240, "结论基于当前数据集的统计摘要，建议结合实际经营情况复核。"),
    }


async def generate_ai_report(config: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    """Generate a structured report with the same provider settings as mapping AI."""
    provider = str(config.get("provider", "")).strip().lower()
    if provider not in {"deepseek", "doubao", "openai", "gemini"}:
        raise AIServiceError("暂不支持该 AI 服务商")
    api_key = str(config.get("apiKey") or config.get("api_key") or "").strip()
    if not api_key:
        raise AIServiceError("未配置 AI API Key")
    prompt = _report_prompt(summary)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=8.0)) as client:
            if provider == "gemini":
                model = str(config.get("modelId") or "gemini-2.0-flash")
                url = f"{_endpoint(config)}/models/{model}:generateContent"
                response = await client.post(url, params={"key": api_key}, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}})
                if response.status_code >= 400:
                    raise AIServiceError(f"Gemini 请求失败（HTTP {response.status_code}）")
                body = response.json()
                text = body.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            else:
                model = str(config.get("modelId") or ("deepseek-chat" if provider == "deepseek" else "gpt-4o-mini"))
                url = f"{_endpoint(config)}/chat/completions"
                response = await client.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": model, "temperature": 0.2, "messages": [{"role": "system", "content": "你只输出合法 JSON。"}, {"role": "user", "content": prompt}]})
                if response.status_code >= 400:
                    raise AIServiceError(f"{provider or 'AI'} 请求失败（HTTP {response.status_code}）")
                body = response.json()
                text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    except httpx.HTTPError as exc:
        raise AIServiceError("AI 服务暂时不可用，已回退到本地报告") from exc

    result = _validate_report_result(_extract_json(text))
    result["provider"] = provider
    result["model"] = str(config.get("modelId") or "")
    return result


PUBLISH_PLATFORM_NAMES = {
    "douyin": "抖音图文",
    "xiaohongshu": "小红书笔记",
    "weibo": "微博动态",
}


def _publish_copy_prompt(
    platform: str,
    brief: str,
    current_draft: dict[str, Any] | None = None,
    tone: str = "自然真诚",
) -> str:
    """Build a bounded prompt for public-facing restaurant copy."""
    platform_name = PUBLISH_PLATFORM_NAMES.get(platform, "社交平台")
    context = {
        "目标平台": platform_name,
        "写作需求": brief,
        "语气": tone,
        "已有标题": str((current_draft or {}).get("title") or "")[:200],
        "已有正文": str((current_draft or {}).get("content") or "")[:5000],
        "已有话题": list((current_draft or {}).get("tags") or [])[:30],
    }
    return """你是餐饮门店的内容编辑。请根据用户提供的信息，为指定平台生成一条可公开发布的中文文案。
只使用用户明确提供的事实，不得编造价格、折扣、地址、营业时间、食材来源、销量或顾客评价。不得加入手机号、内部预算、库存、账号凭据或审批信息。文案要像真实门店在说话，避免空泛口号、夸大承诺和机械堆砌 emoji。

只返回 JSON，不要 markdown，不要代码块。格式：
{"title":"标题","content":"正文","tags":["话题1","话题2"],"angle":"一句话说明本次写作角度"}

要求：标题不超过 80 字；正文不超过 3000 字；话题最多 12 个，每个话题不带 #；angle 不超过 120 字。微博也需要返回一个便于编辑的短标题，交接时系统会把它并入正文。

写作上下文：
""" + json.dumps(context, ensure_ascii=False, default=str)


def _validate_publish_copy_result(value: dict[str, Any]) -> dict[str, Any]:
    """Normalize creative AI output before it can replace the local draft."""
    if not isinstance(value, dict):
        raise AIServiceError("AI 发布文案返回结果格式不正确")

    title = str(value.get("title") or "").strip()[:80]
    content = str(value.get("content") or value.get("body") or "").strip()[:3000]
    if not content:
        raise AIServiceError("AI 没有返回可用的发布正文")

    raw_tags = value.get("tags", [])
    if isinstance(raw_tags, str):
        raw_tags = re.split(r"[,，\n]+", raw_tags)
    if not isinstance(raw_tags, list):
        raw_tags = []
    tags: list[str] = []
    for item in raw_tags:
        tag = re.sub(r"^#+", "", str(item)).strip()[:30]
        if tag and tag not in tags:
            tags.append(tag)
        if len(tags) == 12:
            break

    return {
        "title": title,
        "content": content,
        "tags": tags,
        "angle": str(value.get("angle") or "").strip()[:120],
    }


async def generate_publish_copy(
    config: dict[str, Any],
    platform: str,
    brief: str,
    current_draft: dict[str, Any] | None = None,
    tone: str = "自然真诚",
) -> dict[str, Any]:
    """Generate public restaurant copy using the provider selected in settings."""
    provider = str(config.get("provider", "")).strip().lower()
    if provider not in {"deepseek", "doubao", "openai", "gemini"}:
        raise AIServiceError("暂不支持该 AI 服务商")
    if platform not in PUBLISH_PLATFORM_NAMES:
        raise AIServiceError("暂不支持这个发布平台")
    api_key = str(config.get("apiKey") or config.get("api_key") or "").strip()
    if not api_key:
        raise AIServiceError("未配置 AI API Key")
    prompt = _publish_copy_prompt(platform, brief, current_draft=current_draft, tone=tone)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=8.0)) as client:
            if provider == "gemini":
                model = str(config.get("modelId") or "gemini-2.0-flash")
                url = f"{_endpoint(config)}/models/{model}:generateContent"
                response = await client.post(
                    url,
                    params={"key": api_key},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.55},
                    },
                )
                if response.status_code >= 400:
                    raise AIServiceError(f"Gemini 请求失败（HTTP {response.status_code}）")
                body = response.json()
                text = body.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            else:
                model = str(config.get("modelId") or ("deepseek-chat" if provider == "deepseek" else "gpt-4o-mini"))
                url = f"{_endpoint(config)}/chat/completions"
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "temperature": 0.55,
                        "messages": [
                            {"role": "system", "content": "你只输出合法 JSON。"},
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                if response.status_code >= 400:
                    raise AIServiceError(f"{provider or 'AI'} 请求失败（HTTP {response.status_code}）")
                body = response.json()
                text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    except httpx.HTTPError as exc:
        raise AIServiceError("AI 文案服务暂时不可用，请稍后重试") from exc

    result = _validate_publish_copy_result(_extract_json(text))
    result["provider"] = provider
    result["model"] = model
    return result
