from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.auth import get_current_user
from backend.main import DATASET_STORE, PENDING_UPLOAD_STORE, app


def test_health_endpoint():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.fixture
def authenticated_client():
    user = SimpleNamespace(id=987654)
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_inspect_and_confirm_dataset_requires_review(authenticated_client):
    csv = (
        "订单号,下单时间,商品名称,订单金额\n"
        "A-1,2026-08-28 12:00:00,汉堡,20\n"
        "A-2,2026-08-28 13:00:00,可乐,8\n"
    ).encode("utf-8")
    response = authenticated_client.post(
        "/api/datasets/inspect",
        files={"file": ("orders.csv", csv, "text/csv")},
    )

    assert response.status_code == 200
    inspected = response.json()
    assert inspected["profile"]["row_count"] == 2
    assert inspected["suggestion"]["status"] == "not_configured"
    assert inspected["quality"]["inspection_mode"] is True

    confirmed = authenticated_client.post(
        "/api/datasets/confirm",
        json={
            "inspection_id": inspected["inspection_id"],
            "mapping": [
                {"source": "订单号", "field": "order_id"},
                {"source": "下单时间", "field": "order_time"},
                {"source": "商品名称", "field": "product_name"},
                {"source": "订单金额", "field": "total_amount"},
            ],
        },
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["rows"] == 2
    dataset_id = confirmed.json()["dataset_id"]
    reviewed = authenticated_client.patch(f"/api/anomalies/{dataset_id}/A-1", json={"status": "normal"})
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "normal"
    DATASET_STORE.delete(dataset_id)


def test_inspect_can_review_file_before_required_amount_is_resolved(authenticated_client):
    # Inspection should still expose the schema when the file needs a manual
    # mapping and cannot yet be fully cleaned by the deterministic pipeline.
    csv = "source_id,menu_label\nA,Burger\nB,Fries\n".encode("utf-8")
    response = authenticated_client.post(
        "/api/datasets/inspect",
        files={"file": ("unknown.csv", csv, "text/csv")},
    )

    assert response.status_code == 200
    inspected = response.json()
    assert inspected["profile"]["row_count"] == 2
    assert inspected["quality"]["clean_rows"] == 0
    PENDING_UPLOAD_STORE.delete(inspected["inspection_id"])
