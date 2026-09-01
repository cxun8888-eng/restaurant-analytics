from backend.ai import _publish_copy_prompt, _validate_publish_copy_result, _validate_result
from backend.main import _analysis_gate


def test_ai_mapping_rejects_weekday_as_order_time():
    result = _validate_result(
        {
            "dataset_type": "restaurant_summary",
            "mapping": [
                {"source": "day_of_the_week", "field": "order_time", "confidence": 0.95},
                {"source": "cost_of_the_order", "field": "total_amount", "confidence": 0.95},
            ],
            "ignored_columns": ["rating"],
        },
        ["day_of_the_week", "cost_of_the_order", "rating"],
        {
            "columns": [
                {"name": "day_of_the_week", "numeric_ratio": 0, "date_ratio": 0},
                {"name": "cost_of_the_order", "numeric_ratio": 1, "date_ratio": 0},
                {"name": "rating", "numeric_ratio": 1, "date_ratio": 0},
            ]
        },
    )

    assert all(item["field"] != "order_time" for item in result["mapping"])
    assert any("day_of_the_week" in warning for warning in result["warnings"])
    assert result["mapping"] == [{"source": "cost_of_the_order", "field": "total_amount", "confidence": 0.95, "reason": "AI 根据表头和样例判断"}]


def test_ai_header_translation_covers_every_source_column():
    result = _validate_result(
        {
            "header_translations": [
                {"source": "order_id", "translated": "订单编号", "confidence": 0.98},
            ]
        },
        ["order_id", "cost_of_the_order"],
    )

    assert result["header_translations"][0]["translated"] == "订单编号"
    assert result["header_translations"][1]["source"] == "cost_of_the_order"
    assert result["header_translations"][1]["translated"] == "cost_of_the_order"


def test_analysis_gate_blocks_delivery_waybill_without_amount():
    profile = {
        "columns": [
            {"name": "Unnamed: 0", "numeric_ratio": 1},
            {"name": "dt", "numeric_ratio": 1},
            {"name": "dispatch_time", "numeric_ratio": 1},
            {"name": "order_id", "numeric_ratio": 1},
        ]
    }
    result = _analysis_gate(
        profile,
        [
            {"source": "dt", "field": "order_time"},
            {"source": "dispatch_time", "field": "order_time"},
            {"source": "order_id", "field": "order_id"},
        ],
        {"business_domain": "unknown", "mapping": []},
    )

    assert result["allowed"] is False
    assert result["kind"] == "delivery_summary"
    assert "配送/运单" in result["reason"]


def test_analysis_gate_allows_restaurant_order_with_amount():
    profile = {
        "columns": [
            {"name": "order_id", "numeric_ratio": 1},
            {"name": "order_time", "numeric_ratio": 0},
            {"name": "product_name", "numeric_ratio": 0},
            {"name": "total_amount", "numeric_ratio": 1},
        ]
    }
    result = _analysis_gate(
        profile,
        [
            {"source": "order_id", "field": "order_id"},
            {"source": "order_time", "field": "order_time"},
            {"source": "product_name", "field": "product_name"},
            {"source": "total_amount", "field": "total_amount"},
        ],
        {"business_domain": "unknown", "mapping": []},
    )

    assert result["allowed"] is True
    assert result["kind"] == "restaurant_order"


def test_publish_copy_result_is_bounded_and_normalized():
    result = _validate_publish_copy_result(
        {
            "title": " 周末晚市上新 ",
            "content": "今晚想和你分享三道新菜。",
            "tags": ["#晚市", "晚市", " 城市探店 "],
            "angle": "用门店口吻介绍新品",
        }
    )

    assert result == {
        "title": "周末晚市上新",
        "content": "今晚想和你分享三道新菜。",
        "tags": ["晚市", "城市探店"],
        "angle": "用门店口吻介绍新品",
    }


def test_publish_copy_prompt_forbids_invented_business_details():
    prompt = _publish_copy_prompt("xiaohongshu", "写三道新品", tone="自然真诚")

    assert "小红书笔记" in prompt
    assert "不得编造价格、折扣、地址、营业时间" in prompt
    assert "只返回 JSON" in prompt
